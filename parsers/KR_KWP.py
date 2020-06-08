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

from urllib.request import Request, urlopen

from KR_DataAPIKey import idKey

import xml.etree.ElementTree as ET

# Korea Western Power (한국서부발전)
# https://www.iwest.co.kr/iwest/456/subview.do
# 20 APIs
# # 신재생에너지 건설 및 개발현황 (Renewable Energy Construction & Development Status)
# # 발전소 건설 인허가 현황 (Power Plant Construction License Status)
# # 폐기물 처리내역 및 현황 조회서비스 (Waste Treatment History & Status Inquiry Service)
# # 석탄 재활용 내역 조회서비스 (Coal Recycling History Inquiry Service)
# # 서부발전 입찰공고현황 (Western Power Bid Announcement Status)
# # 대기오염물질 정보 (Air Pollutants Information)
# # 신재생에너지(REC) 현물시장 거래시장 (Renewable Energy (REC) Spot Market Transaction Market)
# # 서부발전 발전연료 소비실적 (West Power Generation Power consumption consumption)
# # 발전용수 생산 및 사용량 (Power generation and consumption)
# # 서부발전 전력거래현황 (Power generation status of western power generation)
# # 연료정보지 (Fuel information magazine)
# # 소비탄 성상 (Consumption characteristics)
# # 서부발전 발전실적 정보 (West power generation performance information)
# # 서부발전 발전소배출 수질 (West power generation plant discharge water quality)
# # 발전설비 이용률 (Power plant utilization rate)
# # 서부발전 발전설비 열효율 정보 (West power generation facility thermal efficiency information)
# # 발전소 주변 대기오염물질 농도 (Power plant surroundings Air Pollutants Concentration)
# # 서부발전 산업재산권 정보 (West Power Industrial Property Information)
# # 대기오염물질 배출량 (Air Pollutant Emissions)
# # 연료도입 현황 (Fuel Introduction Status)

# 발전설비현황 : 11,342MW(2020년 2월 13일 현재), 국내 총 설비 용량의 9% 점유
# 4 plants + renewables
# capacities (MW) (as of 2019.12)
# 태안	6,100.0 
# 서인천	1,800.0 
# 평택기력	1,400.0 
# 평택2복합	868.5 
# 군산	718.4 
# 신재생	455.0 (2018.12 was 434.9 / 2017.12 was 424)
# 계	11,341.9 



KWPPowerPlantsAndUnits = [
	{'powerPlantCode' : 'TA', 'unitCode' : '1', 'powerPlantName' : '태안'},
	{'powerPlantCode' : 'TA', 'unitCode' : '2', 'powerPlantName' : '태안'},
	{'powerPlantCode' : 'TA', 'unitCode' : '3', 'powerPlantName' : '태안'},
	{'powerPlantCode' : 'TA', 'unitCode' : '4', 'powerPlantName' : '태안'},
	{'powerPlantCode' : 'TA', 'unitCode' : '5', 'powerPlantName' : '태안'},
	{'powerPlantCode' : 'TA', 'unitCode' : '6', 'powerPlantName' : '태안'},
	{'powerPlantCode' : 'TA', 'unitCode' : '7', 'powerPlantName' : '태안'},
	{'powerPlantCode' : 'TA', 'unitCode' : '8', 'powerPlantName' : '태안'},
	{'powerPlantCode' : 'PY', 'unitCode' : '1', 'powerPlantName' : '평택'},
	{'powerPlantCode' : 'PY', 'unitCode' : '2', 'powerPlantName' : '평택'},
	{'powerPlantCode' : 'PYB', 'unitCode' : 'CG1', 'powerPlantName' : '평택복합'},
	{'powerPlantCode' : 'PYB', 'unitCode' : 'CG2', 'powerPlantName' : '평택복합'},
	{'powerPlantCode' : 'PYB', 'unitCode' : 'CG3', 'powerPlantName' : '평택복합'},
	{'powerPlantCode' : 'PYB', 'unitCode' : 'CG4', 'powerPlantName' : '평택복합'},
	{'powerPlantCode' : 'PYB', 'unitCode' : 'CS', 'powerPlantName' : '평택복합'},
	{'powerPlantCode' : 'PYB2', 'unitCode' : 'CG1', 'powerPlantName' : '평택복합2'},
	{'powerPlantCode' : 'PYB2', 'unitCode' : 'CG2', 'powerPlantName' : '평택복합2'},
	{'powerPlantCode' : 'PYB2', 'unitCode' : 'ST', 'powerPlantName' : '평택복합2'},
	{'powerPlantCode' : 'WI', 'unitCode' : 'CG1', 'powerPlantName' : '서인천'},
	{'powerPlantCode' : 'WI', 'unitCode' : 'CG2', 'powerPlantName' : '서인천'},
	{'powerPlantCode' : 'WI', 'unitCode' : 'CG3', 'powerPlantName' : '서인천'},
	{'powerPlantCode' : 'WI', 'unitCode' : 'CG4', 'powerPlantName' : '서인천'},
	{'powerPlantCode' : 'WI', 'unitCode' : 'CG5', 'powerPlantName' : '서인천'},
	{'powerPlantCode' : 'WI', 'unitCode' : 'CG6', 'powerPlantName' : '서인천'},
	{'powerPlantCode' : 'WI', 'unitCode' : 'CG7', 'powerPlantName' : '서인천'},
	{'powerPlantCode' : 'WI', 'unitCode' : 'CG8', 'powerPlantName' : '서인천'},
	{'powerPlantCode' : 'WI', 'unitCode' : 'CS1', 'powerPlantName' : '서인천'},
	{'powerPlantCode' : 'WI', 'unitCode' : 'CS2', 'powerPlantName' : '서인천'},
	{'powerPlantCode' : 'WI', 'unitCode' : 'CS3', 'powerPlantName' : '서인천'},
	{'powerPlantCode' : 'WI', 'unitCode' : 'CS4', 'powerPlantName' : '서인천'},
	{'powerPlantCode' : 'WI', 'unitCode' : 'CS5', 'powerPlantName' : '서인천'},
	{'powerPlantCode' : 'WI', 'unitCode' : 'CS6', 'powerPlantName' : '서인천'},
	{'powerPlantCode' : 'WI', 'unitCode' : 'CS7', 'powerPlantName' : '서인천'},
	{'powerPlantCode' : 'WI', 'unitCode' : 'CS8', 'powerPlantName' : '서인천'},
	{'powerPlantCode' : 'GU', 'unitCode' : 'GT1', 'powerPlantName' : '군산복합'},
	{'powerPlantCode' : 'GU', 'unitCode' : 'GT2', 'powerPlantName' : '군산복합'},
	{'powerPlantCode' : 'GU', 'unitCode' : 'ST', 'powerPlantName' : '군산복합'},
]

queryParams = { 
	'ServiceKey' : idKey, 
	'strOrgCd' : 'TA', 
	'strHoki' : '1', 
	'strDateS' : '201608'
}
# TODO 0 results for anything after 201609 !!
year = 2016
month = 8
queryParams['strDateS'] = '{:04}{:02}'.format(year, month)
# TODO number of hours in a month
numberHours = 720

url = 'http://www.iwest.co.kr:8082/openapi-data/service/Develop/Development'
for powerPlant in KWPPowerPlantsAndUnits:
	queryParams['strOrgCd'] = powerPlant['powerPlantCode']
	queryParams['strHoki'] = powerPlant['unitCode']
	r = requests.get(url, params=queryParams)
	root = ET.fromstring(r.content)
	items = root.find('body').find('items').findall('item')
	if len(items) > 0:
		powerPlant['capacity'] = items[-1].find('capacity').text
		powerPlant['monthlyTotal'] = items[-1].find('qvodgen').text
		powerPlant['monthlyAverage'] = float(items[-1].find('qvodgen').text) / numberHours
	else:
		powerPlant['capacity'] = 0
		powerPlant['monthlyTotal'] = 0
		powerPlant['monthlyAverage'] = 0
	print (powerPlant['powerPlantName'], powerPlant['unitCode'], '\t', powerPlant['capacity'], '\t', powerPlant['monthlyAverage'])


# TODO e-mail about this ...
# lol they don't have emails, of course
# 구분 	부서/직위 	성명 	연락처
# 공공데이터 제공 책임관 	보안처 / 처장 	이흥택 	041-400-1900
# 공공데이터 제공 담당 	ICT지원부 / 차장 	지병걸 	041-400-1931
# 공공데이터 제공 담당 	ICT지원부 / 대리 	설유진 	041-400-1936