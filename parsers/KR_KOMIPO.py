#!/usr/bin/env python3
# coding=utf-8
import logging
import datetime
# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests

import re
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

import xml.etree.ElementTree as ET
import json

from KR_DataAPIKey import idKey

# Korea Midland Power ( 한국중부발전(주) -KOMIPO )
# https://www.komipo.co.kr/fr/kor/openApi/main.do
# 2 APIs needed

# OPEN API 발전실적조회 서비스
# = plant power performance inquiry service
# https://www.komipo.co.kr/openapi/service/rest/resultPlant/getData

# 발전소명 	년월 	호기 	용량(Mw) 	발전량(Mwh) 	열효율(%) 	이용율(%)     발전원
# 제주기력 	201905 	소계 	150 	    63,628      	34.71   	57.02   	중유
# 보령기력 	201905 	소계 	4,000 	    958,535 	    19.01 	    32.21 	    석탄
# ...

# 중유 / 태양력 / 석탄 / 소수력 / 복합 / 풍력 / 내연 
# for 복합 (multiple) and 내연 (internal combustion) refer to below API

# OPEN API 연료소비실적 조회 서비스
# = Fuel consumption performance inquiry service
# https://www.komipo.co.kr/openapi/service/rest/fuelCon/getData

#발전소명 	년월 	호기명 	            석탄 	                    기타
#                               유연탄 	무연탄 	계 	    유류 	LNG 	고형연료 	우드펠릿
#제주기력 	201905 	소계 	       0    	0 	0   	24,856 	0 	    0       	0
# ...

# "Bituminous coal" / "Anthracite" / "Total" / "Oil" / "LNG" / "Solid Fuel" / "Wood Pellets"

# KOMIPO list of power plants, names, ids and units
KomipoPowerPlantsAndUnitsV3 = []

apiViewListUrl = 'https://www.komipo.co.kr/fr/kor/openApi/view.do'
apiViewListQueryParams = {
    'apiSeq' : '4',
    'schTabCd' : 'tab1'
}
r = requests.post(apiViewListUrl, data=apiViewListQueryParams)

# parse that webpage to get the power plant codes (a little strange that there's no API for that ? )
KomipoPowerPlantsAndUnitsV3 = []
soup = BeautifulSoup(r.content, 'html.parser')
powerPlantSelect = soup.find('select', id='strOrgNo')
for option in powerPlantSelect.find_all('option'):
	if option.get('value') != '' and option.text != '':
		KomipoPowerPlantsAndUnitsV3.append({'powerPlantCode' : option.get('value'), 'powerPlantName' : option.text})

#now request the unit codes from an internal API webpage
for powerPlant in KomipoPowerPlantsAndUnitsV3:
	unitsListUrl = 'https://www.komipo.co.kr/fr/kor/openApi/hokiList.json'
	unitsListQueryParams = {
		'StrOrgNo' : powerPlant['powerPlantCode'],
		'apiKind' : 'resultPlant'
	}
	r = requests.get(unitsListUrl, params=unitsListQueryParams)
	# result is json
	powerPlantUnitData = json.loads(r.content.decode('utf-8'))
	unitList = powerPlantUnitData['strHokiList']
	powerPlant['powerPlantUnits'] = powerPlantUnitData['strHokiList']

KomipoPowerPlantsAndUnits = KomipoPowerPlantsAndUnitsV3

powerplantProductionAPIurl = 'https://www.komipo.co.kr/openapi/service/rest/resultPlant/getData'
queryParams = { 
    'ServiceKey' : idKey, 
    'strOrgNo' : '8414', 
    'strHokiS' : '004', 
    'strHokiE' : '004', 
    'strDateS' : '202004', 
    'strDateE' : '202004' 
}
year = 2020
month = 4
queryParams['strDateS'] = '{:04}{:02}'.format(year, month)
queryParams['strDateE'] = '{:04}{:02}'.format(year, month)
# TODO number of hours in a month
numberHours = 720

for powerPlant in KomipoPowerPlantsAndUnits:
	# store 용량 (capacity)
	queryParams['strOrgNo'] = powerPlant['powerPlantCode']
	# request all units (the API returns a sub-total of selected units at the end)
	queryParams['strHokiS'] = powerPlant['powerPlantUnits'][0]['HOGI_CD']
	queryParams['strHokiE'] = powerPlant['powerPlantUnits'][-1]['HOGI_CD']
	r = requests.get(powerplantProductionAPIurl, params=queryParams)
	root = ET.fromstring(r.content)
	# TODO : response -> header -> result code -> 00 ? then process else continue
	# response -> body -> items -> last item
	items = root.find('body').find('items').findall('item')
	if len(items) > 0 and items[-1].find('hokinm').text == '소계':
		powerPlant['capacity'] = items[-1].find('capacity').text
		powerPlant['monthlyTotal'] = items[-1].find('qvodgen').text
		powerPlant['monthlyAverage'] = float(items[-1].find('qvodgen').text) / numberHours
	else:
		powerPlant['capacity'] = 0
		powerPlant['monthlyTotal'] = 0
		powerPlant['monthlyAverage'] = 0


fuelConsumptionAPIurl = 'https://www.komipo.co.kr/openapi/service/rest/fuelCon/getData'

# mapping the results from API to electricyMap electricity-type categories
# fuel1 	유연탄 				"Bituminous coal"
# fuel2 	무연탄 				"Anthracite"
# fuel12 	유연,무연탄 소계 	"Total"
# fuel3 	유류 				"Oil"
# fuel4 	LNG 				"LNG"
# fuel5 	고형연료 			"Refuse-derived fuel" (https://en.wikipedia.org/wiki/Refuse-derived_fuel)
# fuel6 	우드펠릿 			"Wood Pellets"

fuelTypes = [
	{'emName' : 'coal', 'komipoName' : 'fuel1'},
	{'emName' : 'coal', 'komipoName' : 'fuel2'},
	{'emName' : 'oil', 'komipoName' : 'fuel3'},
	{'emName' : 'gas', 'komipoName' : 'fuel4'},
	{'emName' : 'biomass', 'komipoName' : 'fuel5'},
	{'emName' : 'biomass', 'komipoName' : 'fuel6'}
]


for powerPlant in KomipoPowerPlantsAndUnits:
	# store 용량 (capacity)
	queryParams['strOrgNo'] = powerPlant['powerPlantCode']
	# request all units (the API returns a sub-total of selected units at the end)
	queryParams['strHokiS'] = powerPlant['powerPlantUnits'][0]['HOGI_CD']
	queryParams['strHokiE'] = powerPlant['powerPlantUnits'][-1]['HOGI_CD']
	r = requests.get(fuelConsumptionAPIurl, params=queryParams)
	root = ET.fromstring(r.content)
	# TODO : response -> header -> result code -> 00 ? then process else continue
	# response -> body -> items -> last item
	items = root.find('body').find('items').findall('item')
	if len(items) > 0 and items[-1].find('hokinm').text == '소계':
		for fuel in fuelTypes:
			powerPlant[fuel['emName']] = items[-1].find(fuel['komipoName']).text
	else:
		for fuel in fuelTypes:
			powerPlant[fuel['emName']] = 0
	print (powerPlant['powerPlantName'], '\t', powerPlant['capacity'], '\t', powerPlant['monthlyAverage']) 

# TODO see what electricityMap needs and process all the data