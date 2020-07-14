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



def get_KOMIPO_power_plants_and_units():
	apiViewListUrl = 'https://www.komipo.co.kr/fr/kor/openApi/view.do'
	apiViewListQueryParams = {
		'apiSeq' : '4',
		'schTabCd' : 'tab1'
	}
	r = requests.post(apiViewListUrl, data=apiViewListQueryParams)
	# parse that webpage to get the power plant codes (a little strange that there's no API for that ? )
	KomipoPowerPlantsAndUnits = []
	soup = BeautifulSoup(r.content, 'html.parser')
	powerPlantSelect = soup.find('select', id='strOrgNo')
	for option in powerPlantSelect.find_all('option'):
		if option.get('value') != '' and option.text != '':
			KomipoPowerPlantsAndUnits.append({'powerPlantCode' : option.get('value'), 'powerPlantName' : option.text})

	#now request the unit codes from an internal API webpage
	for powerPlant in KomipoPowerPlantsAndUnits:
		unitsListUrl = 'https://www.komipo.co.kr/fr/kor/openApi/hokiList.json'
		unitsListQueryParams = {
			'StrOrgNo' : powerPlant['powerPlantCode'],
			'apiKind' : 'resultPlant'
		}
		r = requests.get(unitsListUrl, params=unitsListQueryParams)
		# result is json
		powerPlantUnitData = json.loads(r.content.decode('utf-8'))
		powerPlant['powerPlantUnits'] = powerPlantUnitData['strHokiList']

	return KomipoPowerPlantsAndUnits


def get_capacity_and_power_usage(powerPlant, year, month):
	powerplantProductionAPIurl = 'https://www.komipo.co.kr/openapi/service/rest/resultPlant/getData'
	queryParams = { 
		'ServiceKey' : idKey, 
		'strOrgNo' : '', 
		'strHokiS' : '', 
		'strHokiE' : '', 
		'strDateS' : '', 
		'strDateE' : '' 
	}
	date = '{:04}{:02}'.format(year, month)
	queryParams['strDateS'] = date
	queryParams['strDateE'] = date
	# store 용량 (capacity)
	queryParams['strOrgNo'] = powerPlant['powerPlantCode']
	# request all units (the API returns a sub-total of selected units at the end)
	queryParams['strHokiS'] = powerPlant['powerPlantUnits'][0]['HOGI_CD']
	queryParams['strHokiE'] = powerPlant['powerPlantUnits'][-1]['HOGI_CD']
	r = requests.get(powerplantProductionAPIurl, params=queryParams)
	root = ET.fromstring(r.content)

	# response -> header -> result code -> 00 ? then process else continue
	result = root.find('header').find('resultCode').text
	if result != '00':
		print ("Error code", result)
		print (root.find('header').find('resultMsg').text)
		return

	# response -> body -> items -> last item	
	items = root.find('body').find('items').findall('item')
	powerPlant['capacity'][date] = {}
	powerPlant['monthlyTotal'][date] = {}
	if len(items) > 0 and items[-1].find('hokinm').text == '소계':
		powerPlant['capacity'][date] = items[-1].find('capacity').text
		powerPlant['monthlyTotal'][date] = items[-1].find('qvodgen').text
		# powerPlant['monthlyAverage'] = float(items[-1].find('qvodgen').text) / numberHours
	else:
		powerPlant['capacity'][date] = 0
		powerPlant['monthlyTotal'][date] = 0
		# powerPlant['monthlyAverage'] = 0


year = 2020
month = 4


# mapping the results from API to electricyMap electricity-type categories
# fuel1 	유연탄 				"Bituminous coal"
# fuel2 	무연탄 				"Anthracite"
# fuel12 	유연,무연탄 소계 	"Total"
# fuel3 	유류 				"Oil"
# fuel4 	LNG 				"LNG"
# fuel5 	고형연료 			"Refuse-derived fuel" (https://en.wikipedia.org/wiki/Refuse-derived_fuel)
# fuel6 	우드펠릿 			"Wood Pellets"

fuelTypes = [
	{'emCode' : 'bituminous', 'komipoName' : '유연탄', 'komipoCode' : 'fuel1'},
	{'emCode' : 'anthracite', 'komipoName' : '무연탄', 'komipoCode' : 'fuel2'},
	{'emCode' : 'coal', 'komipoName' : '계', 'komipoCode' : 'fuel12'}, # so far, this is just the sum of fuel1 and fuel2
	{'emCode' : 'oil', 'komipoName' : '유류', 'komipoCode' : 'fuel3'},
	{'emCode' : 'gas', 'komipoName' : 'LNG', 'komipoCode' : 'fuel4'},
	{'emCode' : 'refuse', 'komipoName' : '고형연료', 'komipoCode' : 'fuel5'},
	{'emCode' : 'biomass', 'komipoName' : '우드펠릿', 'komipoCode' : 'fuel6'}
]


def get_fuel_usage(powerPlant, year, month):
	fuelConsumptionAPIurl = 'https://www.komipo.co.kr/openapi/service/rest/fuelCon/getData'
	queryParams = { 
		'ServiceKey' : idKey, 
		'strOrgNo' : '', 
		'strHokiS' : '', 
		'strHokiE' : '', 
		'strDateS' : '', 
		'strDateE' : '' 
	}
	date = '{:04}{:02}'.format(year, month)
	queryParams['strDateS'] = date
	queryParams['strDateE'] = date
	queryParams['strOrgNo'] = powerPlant['powerPlantCode']
	# request all units (the API returns a sub-total of selected units at the end)
	queryParams['strHokiS'] = powerPlant['powerPlantUnits'][0]['HOGI_CD']
	queryParams['strHokiE'] = powerPlant['powerPlantUnits'][-1]['HOGI_CD']
	r = requests.get(fuelConsumptionAPIurl, params=queryParams)
	root = ET.fromstring(r.content)

	# response -> header -> result code -> 00 ? then process else continue
	result = root.find('header').find('resultCode').text
	if result != '00':
		print ("Error code", result)
		print (root.find('header').find('resultMsg').text)
		return

	# response -> body -> items -> last item
	items = root.find('body').find('items').findall('item')
	for fuel in fuelTypes:
		powerPlant[fuel['emCode']][date] = {}
	if len(items) > 0 and items[-1].find('hokinm').text == '소계':
		for fuel in fuelTypes:
			powerPlant[fuel['emCode']][date] = items[-1].find(fuel['komipoCode']).text
	else:
		for fuel in fuelTypes:
			powerPlant[fuel['emCode']][date] = 0

# TODO see what electricityMap needs and process all the data

print ('Loading KOMIPO power plants and units')
KomipoPowerPlantsAndUnits = get_KOMIPO_power_plants_and_units()

for year in range(2019, 2021):
	for month in range(1, 13):
		print ('Loading data for month', month)
		for plant in KomipoPowerPlantsAndUnits:
			if 'capacity' not in plant:
				plant['capacity'] = {}
				plant['monthlyTotal'] = {}
				for fuel in fuelTypes:
					plant[fuel['emCode']] = {}
			get_capacity_and_power_usage(plant, year, month)
			get_fuel_usage(plant, year, month)
		

# total capacity
# coal vs. gas usage over 2 years
with open('KR_KOMIPO_results.json', 'w') as f:
	print ('Dumping to KR_KOMIPO_results.json')
	json.dump(KomipoPowerPlantsAndUnits, f)

