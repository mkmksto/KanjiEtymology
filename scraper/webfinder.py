from bs4 import BeautifulSoup

import urllib.request
import urllib.parse
import json
import time
import re

terms = ['業', '本', '夢']
term = '業'
# term = '本'.encode('utf-8')
# term = 'ささ'.encode('utf-8')

# site2 = 'https://jisho.org/search/{}'.format(urllib.parse.quote(term))
# site3 = 'http://www.weblio.jp/content/'.format(urllib.parse.quote(term))

sample_vocab = '自業自得だと思わないか！夢dsadasd'

# https://stackoverflow.com/questions/34587346/python-check-if-a-string-contains-chinese-character
# removes latin and hiragana text
def extract_kanji(text):
    return re.findall(r'[\u4e00-\u9fff]+', text)

kanji_only_text = extract_kanji(sample_vocab)
kanji_only_text = ''.join(kanji_only_text)
kanji_only_text = set(kanji_only_text)
print(kanji_only_text)

num_retries = 10  # retries per term
for kanji in kanji_only_text:

    site = 'https://www.dong-chinese.com/dictionary/{}'.format(urllib.parse.quote(kanji.encode('utf-8')))

    # try waiting for a while if website returns an error
    try:
        response = urllib.request.urlopen(site)
    except Exception as e:
        for i in range(num_retries):
            try:
                response = urllib.request.urlopen(site)
            except Exception as e:
                time.sleep(0.1)


    soup = BeautifulSoup(response, features='html.parser')
    soup_text = str(soup)

    # get only the relevant JS part of dong-chinese which is formatted as a JSON
    soup_text = soup_text.split('<script>window["')[-1].split('__sink__charData_')[-1].split(']=')[-1]
    # returns a pure JSON object
    soup_text = soup_text.split(';</script>')[0]

    # print(soup_text)
    dong_text_not_found = '"error":"Word not found"'

    # not and error, i.e. something was actually found inside dong
    if not(dong_text_not_found in soup_text):
        # turn into JSON and parse
        soup_json = json.loads(soup_text)
        etymology = soup_json['hint']
        decomposition = soup_json['components']

        print(etymology)