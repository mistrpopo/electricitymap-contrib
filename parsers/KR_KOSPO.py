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
from urllib.parse  import urlencode, quote_plus

from KR_DataAPIKey import idKey

# Korea Southern Power ( 한국남부발전(주) - KOSPO )
# https://www.kospo.co.kr/?mn=sub&mcode=01110205
# 6 categories

# 실시간 전력수급현황 조회 서비스 (Real-time power supply and demand status inquiry service)
# 3 APIs (1 interesting)
# # 실시간 발전량 및 전력수급현황 서비스 (Real-time power generation and power supply and demand status service)

# 남부발전 발전소통합 발전정보 (Southern power plant integrated power generation information)
# 2 APIs
# # 발전실적 조회 (Inquiry of power generation performance)
# # 시간대별 발전량 및 송전량 정보조회 (Inquiry of power generation and transmission amount by time)

# 남부발전 전력계통정보 조회서비스 (Southern power generation power system information inquiry service)
# 8 APIs
# # 기상현황 급전속보 조회 서비스 (Meteorological status rapid breaking news inquiry service)
# # 발전소별 공급능력 조회 서비스 (Power plant supply capability inquiry service)
# # 발전실적 급전속보 조회 서비스 (Power generation performance rapid breaking news inquiry service)
# # 발전원별 점유율 조회 서비스 (Power generation share inquiry service)
# # 발전회사별 점유율 조회 서비스 (Power generation company share inquiry service)
# # 연료별 공급능력 조회 서비스 (Fuel supply capability inquiry service)
# # 연료현황 급전속보 조회 서비스 (Fuel status rapid breaking news inquiry service)
# # 전력수급 급전속보 조회 서비스 (Power supply and demand Rapid breaking news inquiry service)

# 동반성장 (Shared growth)
# 5 APIs
# # 중소기업지원사업 공고조회 서비스 (SME support project notice inquiry service)
# # 연구개발 과제정보조회 서비스 (R&D project information inquiry service)
# # 입찰공고정보조회 서비스 (Bid announcement information inquiry service)
# # 기자재유자격품목조회 서비스 (Equipment qualification items inquiry service)
# # 산업재산권관리 서비스 (Industrial property management service)

# 연료 (Fuel)
# 3 APIs
# # 연료도입실적 조회 서비스 (Fuel introduction performance inquiry service)
# # 연료소비실적 조회 서비스 (Fuel consumption performance inquiry service)
# # 주간연료정보지 다운로드 서비스 (Weekly fuel information download service)


# 환경정보  (Environmental information)
# 8 APIs
# # 탈황석고처리관리 서비스 (Desulfurization gypsum treatment management service)
# # 석탄회 발생관리 조회 서비스 (Coal ash generation management inquiry service)
# # 종합폐수처리량관리 서비스 (Comprehensive waste water treatment management service)
# # 대기오염물질배출농도 조회 서비스 (Air pollutant emission concentration inquiry service)
# # 발전소주변기상정보 서비스 (Power plant ambient weather information service)
# # 발전소주변농도(일별) (Power plant ambient concentration (daily))
# # 발전소주변대기정보 (Power plant ambient air information)
# # 발전소주변수질정보 (Power plant ambient quality information)


# https://www.data.go.kr/data/15057240/openapi.do
# 실시간 발전량 및 전력수급현황 서비스 (Real-time power generation and power supply and demand status service)
# Item name				항목명(국문) 	항목명(영문) 		항목크기 	항목구분 	샘플데이터 		항목설명
# Year-Month			년월 			ymd 							필수 		2017-01-17 		년월
# Supply capacity		공급능력 		szcurrpwr 						필수 		9428 			공급능력
# Current load			현재부하 		powersupply 					필수 		6902 			현재부하
# Supply reserve(W)		공급예비력 		sparepowers 					필수 		2526 			공급예비력
# Supply reserve(%)		공급예비율 		sparepowerpers 					필수 		36.6 			공급예비율
# Operating reserve(W)	운영예비력 		sparepowero 					필수 		2248 			운영예비력
# Operating reserve(%)	운영예비율 		sparepowerpero 					필수 		32.57 			운영예비율  




url = 'http://dataopen.kospo.co.kr/openApi/Gene/GenePwrInfoList'
queryParams = { 
    'ServiceKey' : idKey, 
    'numOfRows' : '10', 
    'pageNo' : '1', 
    'strSdate' : '20140310', 
    'strEdate' : '20140512' 
}

r = requests.get(url, params=queryParams)
print(r, r.content)

# lol no results even with access
