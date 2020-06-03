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


# Korea East-West Power (한국동서발전 - EWP)
# https://ewp.co.kr/kor/main/main.asp
# look for 공공데이터 목록

# applied for 한국동서발전 발전량 현황
url = '	http://ewp.co.kr:8888/openapi/service/rest/resultPlant/getData'

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