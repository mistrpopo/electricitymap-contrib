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
# TODO this list has 20 power plants
# But Komipo has newer ones and I have older ones
# the API is shit ... need to scrape the web page ??
# list of power-plants with codes and names : view-source:https://www.komipo.co.kr/fr/kor/openApi/view.do
# <select name="strOrgNo" id="strOrgNo" class="" title="발전소명 선택" onchange="javascript:strOrgNoSelected()">
# <option value="88A1" >매봉산풍력</option>
# ...
# list of power-plant units given the strOrgNo : https://www.komipo.co.kr/fr/kor/openApi/hokiList.json?StrOrgNo=88A1&apiKind=resultPlant


KomipoPowerPlantsAndUnits = [
	{"powerPlantCode" : "8414", "powerPlantName" : "서울화력", "powerPlantUnits" : [{"unitCode" : "004", "unitName" : "4호기"}, {"unitCode" : "005", "unitName" : "5호기"}]}, 
	{"powerPlantCode" : "8421", "powerPlantName" : "인천기력", "powerPlantUnits" : [{"unitCode" : "001", "unitName" : "1호기"}, {"unitCode" : "002", "unitName" : "2호기"}]}, 
	{"powerPlantCode" : "8561", "powerPlantName" : "제주기력", "powerPlantUnits" : [{"unitCode" : "002", "unitName" : "2호기"}, {"unitCode" : "003", "unitName" : "3호기"}]}, 
	{"powerPlantCode" : "8571", "powerPlantName" : "서천화력", "powerPlantUnits" : [{"unitCode" : "001", "unitName" : "1호기"}, {"unitCode" : "002", "unitName" : "2호기"}]}, 
	{"powerPlantCode" : "8573", "powerPlantName" : "서천태양광", "powerPlantUnits" : [{"unitCode" : "001", "unitName" : "1호기"}, {"unitCode" : "002", "unitName" : "2호기"}]}, 
	{"powerPlantCode" : "8575", "powerPlantName" : "여수엑스포태양광", "powerPlantUnits" : [{"unitCode" : "001", "unitName" : "1호기"}]}, 
	{"powerPlantCode" : "85A1", "powerPlantName" : "보령기력", "powerPlantUnits" : [{"unitCode" : "001", "unitName" : "1호기"}, {"unitCode" : "002", "unitName" : "2호기"}, {"unitCode" : "003", "unitName" : "3호기"}, {"unitCode" : "004", "unitName" : "4호기"}, {"unitCode" : "005", "unitName" : "5호기"}, {"unitCode" : "006", "unitName" : "6호기"}, {"unitCode" : "007", "unitName" : "7호기"}, {"unitCode" : "008", "unitName" : "8호기"}  ]}, 
	{"powerPlantCode" : "85D1", "powerPlantName" : "보령소수력", "powerPlantUnits" : [{"unitCode" : "001", "unitName" : "1호기"}, {"unitCode" : "002", "unitName" : "2호기"}]}, 
	{"powerPlantCode" : "850", "powerPlantName" : "보령태양광", "powerPlantUnits" : [{"unitCode" : "001", "unitName" : "1호기"}, {"unitCode" : "002", "unitName" : "2호기"}]}, 
	{"powerPlantCode" : "85F1", "powerPlantName" : "보령연료전지", "powerPlantUnits" : [{"unitCode" : "001", "unitName" : "1호기"}]}, 
	{"powerPlantCode" : "8691", "powerPlantName" : "보령복합", "powerPlantUnits" : [{"unitCode" : "CG1", "unitName" :  "CG1"}, {"unitCode" : "CG2", "unitName" :  "CG2"}, {"unitCode" : "CS1", "unitName" :  "CS1"}, {"unitCode" : "CG3", "unitName" :  "CG3"}, {"unitCode" : "CG4", "unitName" :  "CG4"}, {"unitCode" : "CS2", "unitName" :  "CS2"}, {"unitCode" : "CG5", "unitName" :  "CG5"}, {"unitCode" : "CG6", "unitName" :  "CG6"}, {"unitCode" : "CS3", "unitName" :  "CS3"}]}, 
	{"powerPlantCode" : "8801", "powerPlantName" : "인천복합", "powerPlantUnits" : [{"unitCode" : "CG1", "unitName" :  "CG1"}, {"unitCode" : "CG2", "unitName" :  "CG2"}, {"unitCode" : "CG3", "unitName" :  "CG3"}, {"unitCode" : "CG4", "unitName" :  "CG4"}, {"unitCode" : "CS1", "unitName" :  "CS1"}, {"unitCode" : "CS2", "unitName" :  "CS2"}, {"unitCode" : "CG5", "unitName" :  "CG5"}, {"unitCode" : "CG6", "unitName" :  "CG6"}, {"unitCode" : "CS3", "unitName" :  "CS3"}]}, 
	{"powerPlantCode" : "8807", "powerPlantName" : "세종열병합", "powerPlantUnits" : [{"unitCode" : "CG1", "unitName" :  "CG1"}, {"unitCode" : "CG2", "unitName" :  "CG2"}, {"unitCode" : "CS1", "unitName" :  "CS1"}]}, 
	{"powerPlantCode" : "881A", "powerPlantName" : "제주태양광", "powerPlantUnits" : [{"unitCode" : "001", "unitName" : "1호기"}, {"unitCode" : "002", "unitName" : "2호기"}]}, 
	{"powerPlantCode" : "881B", "powerPlantName" : "제주대태양광", "powerPlantUnits" : [{"unitCode" : "001", "unitName" : "1호기"}]}, 
	{"powerPlantCode" : "883A", "powerPlantName" : "제주내연", "powerPlantUnits" : [{"unitCode" : "001", "unitName" : "1호기"}, {"unitCode" : "002", "unitName" : "2호기"}]}, 
	{"powerPlantCode" : "886A", "powerPlantName" : "제주GT", "powerPlantUnits" : [{"unitCode" : "CG3", "unitName" : "CG3"}]}, 
	{"powerPlantCode" : "880", "powerPlantName" : "인천태양광", "powerPlantUnits" : [{"unitCode" : "001", "unitName" : "1호기"}]}, 
	{"powerPlantCode" : "8995", "powerPlantName" : "서울태양광", "powerPlantUnits" : [{"unitCode" : "001", "unitName" : "1호기"}]}, 
	{"powerPlantCode" : "9983", "powerPlantName" : "양양풍력", "powerPlantUnits" : [{"unitCode" : "001", "unitName" : "#1~2호기"}]}
]

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
	queryParams['strHokiS'] = powerPlant['powerPlantUnits'][0]['unitCode']
	queryParams['strHokiE'] = powerPlant['powerPlantUnits'][-1]['unitCode']
	r = requests.get(url, params=queryParams)
	root = ET.fromstring(r.content)
	# TODO : response -> header -> result code -> 00 ? then process else continue
	# response -> body -> items -> last item
	items = root.find('body').find('items').findall('item')
	if len(items) > 0 and items[-1].find('hokinm').text == '소계':
		powerPlant['capacity'] = items[-1].find('capacity').text
	else:
		powerPlant['capacity'] = 0
	# print (powerPlant['powerPlantName'], '\t', powerPlant['capacity']) 


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
];


for powerPlant in KomipoPowerPlantsAndUnits:
	# store 용량 (capacity)
	queryParams['strOrgNo'] = powerPlant['powerPlantCode']
	# request all units (the API returns a sub-total of selected units at the end)
	queryParams['strHokiS'] = powerPlant['powerPlantUnits'][0]['unitCode']
	queryParams['strHokiE'] = powerPlant['powerPlantUnits'][-1]['unitCode']
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
	print (powerPlant['powerPlantName'], '\t', powerPlant['capacity'], '\t', powerPlant['biomass']) 

# r = requests.get(url, params=queryParams)
# print (r.content)
