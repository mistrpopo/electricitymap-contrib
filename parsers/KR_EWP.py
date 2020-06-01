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
