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

KomipoPowerPlantsAndUnitsV1 = [
	{"powerPlantCode" : "8414", "powerPlantName" : "서울화력", "powerPlantUnits" : [{"HOGI_CD" : "004", "HOGI_NM" : "4호기"}, {"HOGI_CD" : "005", "HOGI_NM" : "5호기"}]}, 
	{"powerPlantCode" : "8421", "powerPlantName" : "인천기력", "powerPlantUnits" : [{"HOGI_CD" : "001", "HOGI_NM" : "1호기"}, {"HOGI_CD" : "002", "HOGI_NM" : "2호기"}]}, 
	{"powerPlantCode" : "8561", "powerPlantName" : "제주기력", "powerPlantUnits" : [{"HOGI_CD" : "002", "HOGI_NM" : "2호기"}, {"HOGI_CD" : "003", "HOGI_NM" : "3호기"}]}, 
	{"powerPlantCode" : "8571", "powerPlantName" : "서천화력", "powerPlantUnits" : [{"HOGI_CD" : "001", "HOGI_NM" : "1호기"}, {"HOGI_CD" : "002", "HOGI_NM" : "2호기"}]}, 
	{"powerPlantCode" : "8573", "powerPlantName" : "서천태양광", "powerPlantUnits" : [{"HOGI_CD" : "001", "HOGI_NM" : "1호기"}, {"HOGI_CD" : "002", "HOGI_NM" : "2호기"}]}, 
	{"powerPlantCode" : "8575", "powerPlantName" : "여수엑스포태양광", "powerPlantUnits" : [{"HOGI_CD" : "001", "HOGI_NM" : "1호기"}]}, 
	{"powerPlantCode" : "85A1", "powerPlantName" : "보령기력", "powerPlantUnits" : [{"HOGI_CD" : "001", "HOGI_NM" : "1호기"}, {"HOGI_CD" : "002", "HOGI_NM" : "2호기"}, {"HOGI_CD" : "003", "HOGI_NM" : "3호기"}, {"HOGI_CD" : "004", "HOGI_NM" : "4호기"}, {"HOGI_CD" : "005", "HOGI_NM" : "5호기"}, {"HOGI_CD" : "006", "HOGI_NM" : "6호기"}, {"HOGI_CD" : "007", "HOGI_NM" : "7호기"}, {"HOGI_CD" : "008", "HOGI_NM" : "8호기"}  ]}, 
	{"powerPlantCode" : "85D1", "powerPlantName" : "보령소수력", "powerPlantUnits" : [{"HOGI_CD" : "001", "HOGI_NM" : "1호기"}, {"HOGI_CD" : "002", "HOGI_NM" : "2호기"}]}, 
	{"powerPlantCode" : "850", "powerPlantName" : "보령태양광", "powerPlantUnits" : [{"HOGI_CD" : "001", "HOGI_NM" : "1호기"}, {"HOGI_CD" : "002", "HOGI_NM" : "2호기"}]}, 
	{"powerPlantCode" : "85F1", "powerPlantName" : "보령연료전지", "powerPlantUnits" : [{"HOGI_CD" : "001", "HOGI_NM" : "1호기"}]}, 
	{"powerPlantCode" : "8691", "powerPlantName" : "보령복합", "powerPlantUnits" : [{"HOGI_CD" : "CG1", "HOGI_NM" :  "CG1"}, {"HOGI_CD" : "CG2", "HOGI_NM" :  "CG2"}, {"HOGI_CD" : "CS1", "HOGI_NM" :  "CS1"}, {"HOGI_CD" : "CG3", "HOGI_NM" :  "CG3"}, {"HOGI_CD" : "CG4", "HOGI_NM" :  "CG4"}, {"HOGI_CD" : "CS2", "HOGI_NM" :  "CS2"}, {"HOGI_CD" : "CG5", "HOGI_NM" :  "CG5"}, {"HOGI_CD" : "CG6", "HOGI_NM" :  "CG6"}, {"HOGI_CD" : "CS3", "HOGI_NM" :  "CS3"}]}, 
	{"powerPlantCode" : "8801", "powerPlantName" : "인천복합", "powerPlantUnits" : [{"HOGI_CD" : "CG1", "HOGI_NM" :  "CG1"}, {"HOGI_CD" : "CG2", "HOGI_NM" :  "CG2"}, {"HOGI_CD" : "CG3", "HOGI_NM" :  "CG3"}, {"HOGI_CD" : "CG4", "HOGI_NM" :  "CG4"}, {"HOGI_CD" : "CS1", "HOGI_NM" :  "CS1"}, {"HOGI_CD" : "CS2", "HOGI_NM" :  "CS2"}, {"HOGI_CD" : "CG5", "HOGI_NM" :  "CG5"}, {"HOGI_CD" : "CG6", "HOGI_NM" :  "CG6"}, {"HOGI_CD" : "CS3", "HOGI_NM" :  "CS3"}]}, 
	{"powerPlantCode" : "8807", "powerPlantName" : "세종열병합", "powerPlantUnits" : [{"HOGI_CD" : "CG1", "HOGI_NM" :  "CG1"}, {"HOGI_CD" : "CG2", "HOGI_NM" :  "CG2"}, {"HOGI_CD" : "CS1", "HOGI_NM" :  "CS1"}]}, 
	{"powerPlantCode" : "881A", "powerPlantName" : "제주태양광", "powerPlantUnits" : [{"HOGI_CD" : "001", "HOGI_NM" : "1호기"}, {"HOGI_CD" : "002", "HOGI_NM" : "2호기"}]}, 
	{"powerPlantCode" : "881B", "powerPlantName" : "제주대태양광", "powerPlantUnits" : [{"HOGI_CD" : "001", "HOGI_NM" : "1호기"}]}, 
	{"powerPlantCode" : "883A", "powerPlantName" : "제주내연", "powerPlantUnits" : [{"HOGI_CD" : "001", "HOGI_NM" : "1호기"}, {"HOGI_CD" : "002", "HOGI_NM" : "2호기"}]}, 
	{"powerPlantCode" : "886A", "powerPlantName" : "제주GT", "powerPlantUnits" : [{"HOGI_CD" : "CG3", "HOGI_NM" : "CG3"}]}, 
	{"powerPlantCode" : "880", "powerPlantName" : "인천태양광", "powerPlantUnits" : [{"HOGI_CD" : "001", "HOGI_NM" : "1호기"}]}, 
	{"powerPlantCode" : "8995", "powerPlantName" : "서울태양광", "powerPlantUnits" : [{"HOGI_CD" : "001", "HOGI_NM" : "1호기"}]}, 
	{"powerPlantCode" : "9983", "powerPlantName" : "양양풍력", "powerPlantUnits" : [{"HOGI_CD" : "001", "HOGI_NM" : "#1~2호기"}]}
]

# TODO this list has 20 power plants
# But Komipo has newer ones and I have older ones
# the API is shit ... need to scrape the web page ??
# list of power-plants with codes and names : view-source:https://www.komipo.co.kr/fr/kor/openApi/view.do
# <select name="strOrgNo" id="strOrgNo" class="" title="발전소명 선택" onchange="javascript:strOrgNoSelected()">
# <option value="88A1" >매봉산풍력</option>
# ...
# list of power-plant units given the strOrgNo : https://www.komipo.co.kr/fr/kor/openApi/hokiList.json?StrOrgNo=88A1&apiKind=resultPlant




apiViewListUrl = 'https://www.komipo.co.kr/fr/kor/openApi/view.do'
apiViewListQueryParams = {
    'apiSeq' : '4',
    'schTabCd' : 'tab1'
}
r = requests.post(apiViewListUrl, data=apiViewListQueryParams)

# hard-coded list of plants (TODO parse the request above)

KomipoPowerPlantsAndUnitsV2 = [
	{"powerPlantCode" : "88A1", "powerPlantName" : "매봉산풍력"},
	{"powerPlantCode" : "85A1", "powerPlantName" : "보령기력"},
	{"powerPlantCode" : "8691", "powerPlantName" : "보령복합"},
	{"powerPlantCode" : "85D1", "powerPlantName" : "보령소수력"},
	{"powerPlantCode" : "85F1", "powerPlantName" : "보령연료전지"},
	{"powerPlantCode" : "85E1", "powerPlantName" : "보령태양광"},
	{"powerPlantCode" : "881D", "powerPlantName" : "상명풍력"},
	{"powerPlantCode" : "8995", "powerPlantName" : "서울태양광"},
	{"powerPlantCode" : "8414", "powerPlantName" : "서울화력"},
	{"powerPlantCode" : "8573", "powerPlantName" : "서천태양광"},
	{"powerPlantCode" : "8571", "powerPlantName" : "서천화력"},
	{"powerPlantCode" : "8807", "powerPlantName" : "세종천연가스"},
	{"powerPlantCode" : "A101", "powerPlantName" : "신보령기력"},
	{"powerPlantCode" : "A811", "powerPlantName" : "신보령소수력"},
	{"powerPlantCode" : "A801", "powerPlantName" : "신보령태양광"},
	{"powerPlantCode" : "9983", "powerPlantName" : "양양풍력"},
	{"powerPlantCode" : "8575", "powerPlantName" : "여수엑스포태양광"},
	{"powerPlantCode" : "4802", "powerPlantName" : "원주그린열병합"},
	{"powerPlantCode" : "8421", "powerPlantName" : "인천기력"},
	{"powerPlantCode" : "8801", "powerPlantName" : "인천복합"},
	{"powerPlantCode" : "88E1", "powerPlantName" : "인천태양광"},
	{"powerPlantCode" : "886A", "powerPlantName" : "제주GT"},
	{"powerPlantCode" : "8561", "powerPlantName" : "제주기력"},
	{"powerPlantCode" : "883A", "powerPlantName" : "제주내연"},
	{"powerPlantCode" : "881B", "powerPlantName" : "제주대태양광"},
	{"powerPlantCode" : "881A", "powerPlantName" : "제주태양광"}
]

for powerPlant in KomipoPowerPlantsAndUnitsV2:
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

KomipoPowerPlantsAndUnits = KomipoPowerPlantsAndUnitsV2

url = 'https://www.komipo.co.kr/openapi/service/rest/resultPlant/getData'
queryParams = { 
    'ServiceKey' : idKey, 
    'strOrgNo' : '8414', 
    'strHokiS' : '004', 
    'strHokiE' : '004', 
    'strDateS' : '202004', 
    'strDateE' : '202004' 
}

for powerPlant in KomipoPowerPlantsAndUnits:
	# store 용량 (capacity)
	queryParams['strOrgNo'] = powerPlant['powerPlantCode']
	# request all units (the API returns a sub-total of selected units at the end)
	queryParams['strHokiS'] = powerPlant['powerPlantUnits'][0]['HOGI_CD']
	queryParams['strHokiE'] = powerPlant['powerPlantUnits'][-1]['HOGI_CD']
	r = requests.get(url, params=queryParams)
	root = ET.fromstring(r.content)
	# TODO : response -> header -> result code -> 00 ? then process else continue
	# response -> body -> items -> last item
	# TODO number of hours in a month
	numberHours = 720
	items = root.find('body').find('items').findall('item')
	if len(items) > 0 and items[-1].find('hokinm').text == '소계':
		powerPlant['capacity'] = items[-1].find('capacity').text
		powerPlant['monthlyTotal'] = items[-1].find('qvodgen').text
		powerPlant['monthlyAverage'] = float(items[-1].find('qvodgen').text) / numberHours
	else:
		powerPlant['capacity'] = 0
		powerPlant['monthlyTotal'] = 0
		powerPlant['monthlyAverage'] = 0


url = 'https://www.komipo.co.kr/openapi/service/rest/fuelCon/getData'
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
	r = requests.get(url, params=queryParams)
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

# r = requests.get(url, params=queryParams)
# print (r.content)
