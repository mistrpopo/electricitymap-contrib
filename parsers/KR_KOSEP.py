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


# Korea South-East Power (한국남동발전 - KOSEP)
# http://www.koenergy.kr/kosep/hw/gv/nf/nfhw36/main.do?menuCd=GV0501
# 48 APIs ...
# I just deleted them, I think they're not relevant

# https://www.koenergy.kr/kosep/gv/nf/dt/nfdt01/main.do?menuCd=GV05020201
# 발전 실적_현황
# actual REST API is to check in the source lol
# https://www.koenergy.kr/kosep/gv/nf/dt/nfdt01/getData.do
# $("#schForm").ajaxSubmit({			
#	 url:'./getData.do',			
#	 type:'POST',		
#	 data:{"op":"resultPlant"},
#	 dataType:'text',
#	 success:function(msg){
#		 var xmlDoc=$.parseXML(msg);
#		 $xml=$(xmlDoc);
#	 }
# });

# results are like this
# 발전소명 		년월 		호기 	용량(MW) 	발전량(MWh) 		열효율(%) 	이용율(%) 	발전원
# 영흥태양광	202004		소계		1.99		301.25			0			21.03		태양력
# 영흥태양광 #3	202003		소계		6.15		913.69			0			19.97		태양력
# 영흥			202004		소계		5,080		2,245,678.8		39.68		61.4		석탄
resultPlantMainUrl = 'https://www.koenergy.kr/kosep/gv/nf/dt/nfdt01/main.do?menuCd=GV05020201'
getDataUrl = 'http://www.koenergy.kr/kosep/gv/nf/dt/nfdt01/getData.do'
head = {
	'User-Agent': 'sdfsdfsdf' # LOL seems they block python requests by detecting user-agent
}
queryParams = {
	'strTitle':"발전실적",
	'fileName':"한국남동발전 발전실적.csv",
	'strOrgNo':"",
	'strHokiS':"",
	'strHokiE':"",
	'strDateS':"202003",
	'strDateE':"202005",
	'__encrypted':"dedOsx0Jn22DngIuvYPWT0BPsnGgn8e4MwzjMjqNKGy/NLAmPfr9IrXrV+YtZ+Mj0Nqvue8pVo+/Vix85u2BMfHvWLZdPnBfUBzJFyvIUW7u6Qn1Ew1/IQH7WOMsRX1bkAhM8MPzllUJ13TSwKwXUMxOFWWpDdjm9qFtvmwtr/nIihPRCcPhdNFFCMJZh2U69cJKjaPTdPacflgdjRxkk0wN3Dq+DQ6BqyWsfxelZ6H0f2zVpok3/7prqcCmgsRHCcBMYg0ihjDVy4XjOjhx7MA7k5mEFV+IZf1aCm5rurVWbubFHK4ojXSZfEC6OH2sKgvJpPTfkux9SuPYgGovyr7rwj9LyIlgbBxG4gUv+/Mlv33xrdCPqFPvgLrMlHopBYadtxXE9LmRHGOD84JxwBECBOuAsCuX",
	'op':"resultPlant"
}
year = 2020
month = 4
queryParams['strDateS'] = '{:04}{:02}'.format(year, month)
queryParams['strDateE'] = '{:04}{:02}'.format(year, month)
# TODO number of hours in a month
numberHours = 720

KOSEPPowerPlantsAndUnits = []


s = requests.Session()
s.get(resultPlantMainUrl, headers=head) # get the main page first (not sure why this is needed)
r = s.post(getDataUrl, data=queryParams, headers=head)
print (r.content)
root = ET.fromstring(r.content)
results = root.find('resultList').findall('data')
for data in results:
	powerPlant = {
		'powerPlantName' : data.find('orgNm').text,
		'capacity' : data.find('capacity').text,
		'monthlyTotal' : data.find('qvodGen').text,
		'monthlyAverage' : float(data.find('qvodGen').text) / numberHours,
	}
	KOSEPPowerPlantsAndUnits.append(powerPlant)
	print (powerPlant['powerPlantName'], '\t', powerPlant['capacity'], '\t', powerPlant['monthlyAverage'])  

# https://www.koenergy.kr/kosep/gv/nf/dt/nfdt04/main.do?menuCd=GV05020204
# 연료 소비 실적_현황
# $("#schForm").ajaxSubmit({			
# 	url:'./getData.do',			
# 	type:'POST',		
# 	data:{"op":"fuelCon"},
# 	dataType:'text',
# 	success:function(msg){
# 		var xmlDoc=$.parseXML(msg);
# 		$xml=$(xmlDoc);

queryParams = {
	'strTitle':"연료소비실적",
	'fileName':"한국남동발전 발전소주변농도.csv",
	'strOrgNo':"",
	'strHokiS':"",
	'strHokiE':"",
	'strDateS':"202003",
	'strDateE':"202005",
	'__encrypted':"dedOsx0Jn22DngIuvYPWT0BPsnGgn8e4MwzjMjqNKGy/NLAmPfr9IrXrV+YtZ+Mj0Nqvue8pVo+/Vix85u2BMfHvWLZdPnBfUBzJFyvIUW7u6Qn1Ew1/IQH7WOMsRX1bkAhM8MPzllUJ13TSwKwXUMxOFWWpDdjm9qFtvmwtr/nIihPRCcPhdNFFCMJZh2U69cJKjaPTdPacflgdjRxkk0wN3Dq+DQ6BqyWsfxelZ6H0f2zVpok3/7prqcCmgsRHCcBMYg0ihjDVy4XjOjhx7MA7k5mEFV+IZf1aCm5rurVWbubFHK4ojXSZfEC6OH2sKgvJpPTfkux9SuPYgGovyr7rwj9LyIlgbBxG4gUv+/Mlv33xrdCPqFPvgLrMlHopBYadtxXE9LmRHGOD84JxwBECBOuAsCuX",
	'op':"fuelCon"
}
year = 2020
month = 4
queryParams['strDateS'] = '{:04}{:02}'.format(year, month)
queryParams['strDateE'] = '{:04}{:02}'.format(year, month)
# TODO number of hours in a month
numberHours = 720

fuelConMainUrl = 'https://www.koenergy.kr/kosep/gv/nf/dt/nfdt04/main.do?menuCd=GV05020204'




fuelTypes = [
	{'emCode' : 'bituminous', 'kosepName' : '유연탄', 'kosepCode' : 'fuel1'},
	{'emCode' : 'anthracite', 'kosepName' : '무연탄', 'kosepCode' : 'fuel2'},
	{'emCode' : 'coal', 'kosepName' : '계', 'kosepCode' : 'fuel12'}, # so far, this is just the sum of fuel1 and fuel2
	{'emCode' : 'oil', 'kosepName' : '유류', 'kosepCode' : 'fuel3'},
	{'emCode' : 'gas', 'kosepName' : 'LNG', 'kosepCode' : 'fuel4'},
	{'emCode' : 'refuse', 'kosepName' : '고형연료', 'kosepCode' : 'fuel5'},
	{'emCode' : 'biomass', 'kosepName' : '우드펠릿', 'kosepCode' : 'fuel6'}
]

s = requests.Session()
s.get(fuelConMainUrl, headers=head) # get the main page first (not sure why this is needed)
r = s.post(getDataUrl, data=queryParams, headers=head)
root = ET.fromstring(r.content)
results = root.find('resultList').findall('data')
for data in results:
	powerPlant = [plant for plant in KOSEPPowerPlantsAndUnits if plant['powerPlantName'] == data.find('orgNm').text]
	print (powerPlant)

# TODO : 
# 분당화력 in the fuel consumption array, but not in the power generation array
# 분당 in the power generation array, but not in the fuel consumption array
# 두산엔진MG태양광 in fuel consumption, not in power generation
# 두산태양광 in power generation, not in fuel consumption