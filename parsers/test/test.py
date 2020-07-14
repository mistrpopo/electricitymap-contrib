
from bs4 import BeautifulSoup
import requests

apiViewListUrl = 'https://www.komipo.co.kr/fr/kor/openApi/view.do'
apiViewListQueryParams = {
    'apiSeq' : '4',
    'schTabCd' : 'tab1'
}
r = requests.post(apiViewListUrl, data=apiViewListQueryParams)

soup = BeautifulSoup(r.content, 'html.parser')
# <select name="strOrgNo" id="strOrgNo" class="" title="발전소명 선택" onchange="javascript:strOrgNoSelected()">
# <option value="88A1" >매봉산풍력</option>
# get the 
powerPlantSelect = soup.find('select', id='strOrgNo')
for option in powerPlantSelect.find_all('option'):
    print (option.text, '\t', option.get('value'))
