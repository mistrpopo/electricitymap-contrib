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