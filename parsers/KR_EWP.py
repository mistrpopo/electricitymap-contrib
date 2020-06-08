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

from KR_DataAPIKey import idKey

import xml.etree.ElementTree as ET
import json

# Korea East-West Power (한국동서발전 - EWP)
# https://ewp.co.kr/kor/main/main.asp
# look for 공공데이터 목록


# example page looks good but results are always :
# <response>
# <header>
# <resultCode>99</resultCode>
# <resultMsg>가용한 세션이 존재하지 않습니다. (100/100)</resultMsg>
# </header>
# <body/>
# </response>
# No sessions available
# sounds like b***s***, I pinged every hour and it never went through

# got a result today (05/06)
# http://ewp.co.kr:8888/openapi/service/rest/resultPlant/getData?serviceKey=***&strDateS=201401&strDateE=201402&strOrgNo=2000&strHokiS=2001&strHokiE=2002&
# results in xml file


# keep backup if API doesn't respond
EWPPowerPlantsAndUnits = [
	{'PPT_CD': '2000', 'PPT_NM': '당진'}, 
	{'PPT_CD': '5000', 'PPT_NM': '동해'}, 
	{'PPT_CD': '3000', 'PPT_NM': '울산'}, 
	{'PPT_CD': '6000', 'PPT_NM': '일산'}, 
	{'PPT_CD': '4000', 'PPT_NM': '호남'}
]

powerPlantListUrl = 'http://ewp.co.kr/kor/openapi/info_open/getData/getOrgNoList.asp'
powerPlantListQueryParams = { 'strOrder' : 'resultPlant' }

r = requests.post(powerPlantListUrl,data=powerPlantListQueryParams)
EWPPowerPlantsAndUnits = json.loads(r.content.decode('utf-8'))

powerPlantUnitListUrl = 'http://ewp.co.kr/kor/openapi/info_open/getData/getHogiList.asp'
powerPlantUnitListQueryParams = { 'strOrgNo':'', 'strOrder':'resultPlant' }
for powerPlant in EWPPowerPlantsAndUnits:
	powerPlantUnitListQueryParams['strOrgNo'] = powerPlant['PPT_CD']
	r = requests.post(powerPlantUnitListUrl,data=powerPlantUnitListQueryParams)
	powerPlant['units'] = json.loads(r.content.decode('utf-8'))



# API name : 한국동서발전 발전량 현황
powerplantProductionAPIurl = 'http://ewp.co.kr:8888/openapi/service/rest/resultPlant/getData'

# TODO no results after 201504 !!!
queryParams = {
	'serviceKey' : idKey, 
	'strDateS' : '201504',
	'strDateE' : '201504',
	'strOrgNo' : '2000',
	'strHokiS' : '2001', 
	'strHokiE' : '2002'
}
year = 2015
month = 4
queryParams['strDateS'] = '{:04}{:02}'.format(year, month)
queryParams['strDateE'] = '{:04}{:02}'.format(year, month)
# TODO number of hours in a month
numberHours = 720

for powerPlant in EWPPowerPlantsAndUnits:
	queryParams['strOrgNo'] = powerPlant['PPT_CD']
	queryParams['strHokiS'] = powerPlant['units'][0]['HOGI_CD']
	queryParams['strHokiE'] = powerPlant['units'][-1]['HOGI_CD']
	r = requests.get(powerplantProductionAPIurl, params=queryParams)
	root = ET.fromstring(r.content)
	items = root.find('body').find('items').findall('item')
	if len(items) > 0 and items[-1].find('hokinm').text == '소계':
		powerPlant['capacity'] = 1000 * float(items[-1].find('capacity').text) # NB capacity is in GW (even though noted as MW in the doc)
		powerPlant['monthlyTotal'] = items[-1].find('qvodgen').text # monthly total in MWh
		powerPlant['monthlyAverage'] = float(items[-1].find('qvodgen').text) / numberHours
	else:
		powerPlant['capacity'] = 0
		powerPlant['monthlyTotal'] = 0
		powerPlant['monthlyAverage'] = 0
	print (powerPlant['PPT_NM'], '\t', powerPlant['capacity'], '\t', powerPlant['monthlyAverage'])

# TODO
# # email about missing data
# # # 공공데이터제공 책임관 : https://ewp.co.kr/kor/subpage/contents.asp?cn=O7LLOXLH&ln=GW1DHD0E&sb=4NPUV623&tb=EF7TWP9
# # finish job : get the electricity type per plant / unit (beware there are solar / coal / hydro units in each plant)
