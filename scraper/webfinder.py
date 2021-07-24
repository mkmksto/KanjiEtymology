import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import json

term = '本'.encode('utf-8')
# term = '夢'.encode('utf-8')

site = 'https://www.dong-chinese.com/dictionary/{}'.format(urllib.parse.quote(term))
site2 = 'https://jisho.org/search/{}'.format(urllib.parse.quote(term))
site3 = 'http://www.weblio.jp/content/'.format(urllib.parse.quote(term))

response = urllib.request.urlopen(site)
soup = BeautifulSoup(response, features='html.parser')
soup_text = str(soup)

# get only the relevant JS part of dong-chinese which is formatted as a JSON
soup_text = soup_text.split('<script>window["')[-1].split('__sink__charData_')[-1].split(']=')[-1]
# returns a pure JSON object
soup_text = soup_text.split(';</script>')[0]

# turn into JSON and parse
soup_json = json.loads(soup_text)
etymology = soup_json['hint']
decomposition = soup_json['components']

print(decomposition)

