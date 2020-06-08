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


# Korea South-East Power (한국남동발전 - KOSEP)
# http://www.koenergy.kr/kosep/hw/gv/nf/nfhw36/main.do?menuCd=GV0501
# 48 APIs ...
# I just deleted them, I think they're not relevant

# https://www.koenergy.kr/kosep/gv/nf/dt/nfdt01/main.do?menuCd=GV05020201
# 발전 실적_현황
# actual REST API is to check in the source lol
# https://www.koenergy.kr/kosep/gv/nf/dt/nfdt01/getData.do
# $("#schForm").ajaxSubmit({			
#     url:'./getData.do',			
#     type:'POST',		
#     data:{"op":"resultPlant"},
#     dataType:'text',
#     success:function(msg){
#         var xmlDoc=$.parseXML(msg);
#         $xml=$(xmlDoc);
#     }
# });

# results are like this
# 발전소명 		년월 		호기 	용량(MW) 	발전량(MWh) 		열효율(%) 	이용율(%) 	발전원
# 영흥태양광	202004		소계		1.99		301.25			0			21.03		태양력
# 영흥태양광 #3	202003		소계		6.15		913.69			0			19.97		태양력
# 영흥			202004		소계		5,080		2,245,678.8		39.68		61.4		석탄

url = 'http://www.koenergy.kr/kosep/gv/nf/dt/nfdt01/getData.do' # disabling HTTPS for now
head = {
    'User-Agent': 'curl/7.32.0' # LOL seems they block python requests by detecting user-agent
}
queryParams = {
    'strTitle':"발전실적",
    'fileName':"한국남동발전 발전실적.csv",
    'strOrgNo':"",
    'strHokiS':"",
    'strHokiE':"",
    'strDateS':"202003",
    'strDateE':"202005",
    '__encrypted':"dedOsx0Jn22DngIuvYPWT0BPsnGgn8e4MwzjMjqNKGy/NLAmPfr9IrXrV+YtZ+Mj0Nqvue8pVo+/Vix85u2BMfHvWLZdPnBfUBzJFyvIUW7u6Qn1Ew1/IQH7WOMsRX1bkAhM8MPzllUJ13TSwKwXUMxOFWWpDdjm9qFtvmwtr/nIihPRCcPhdNFFCMJZh2U69cJKjaPTdPacflgdjRxkk0wN3Dq+DQ6BqyWsfxelZ6H0f2zVpok3/7prqcCmgsRHCcBMYg0ihjDVy4XjOjhx7MA7k5mEFV+IZf1aCm5rurVWbubFHK4ojXSZfEC6OH2sKgvJpPTfkux9SuPYgGovyr7rwj9LyIlgbBxG4gUv+/PSb86VeuqpQh9TiYfmnMAgnIX0QFR2l6dsGa1ENRq7bn8fh/4TLO/0",
    'op':"resultPlant"
}
r = requests.post(url, data=queryParams, headers=head)
print (r, r.content)
print (r.request.headers)
print (r.request.body)

#no longer 400 but 404

# request fails if I try from Firefox without loading the page?
# 오류가 발생하였습니다. 관리자에게 문의해주세요
# F5 => retry => OK
# need a cookie :
# Cookie: SESSION_ID=RjlbeO7HypxjAqMbkukiSI3cxncvkcAPOXBKxaud-DLZ6hY7nxzk!-1546790683
# this header in the 302 response from server :
# Set-Cookie: SESSION_ID=0opbkHY_9PTxC3GSdNx…-1546790683; path=/; HttpOnly
# need to 
# - get the 302
# - get the cookie session ID
# - request again

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


dataDict = {
    'strTitle':"연료소비실적",
    'fileName':"한국남동발전 발전소주변농도.csv",
    'op':"fuelCon"
}