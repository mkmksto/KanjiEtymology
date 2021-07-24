import urllib.request
import urllib.parse

term = '本'.encode('utf-8')

site = 'https://www.dong-chinese.com/dictionary/{}'.format(urllib.parse.quote(term))
site2 = 'https://jisho.org/search/{}'.format(urllib.parse.quote(term))
site3 = 'http://www.weblio.jp/content/'.format(urllib.parse.quote(term))
data = urllib.request.urlopen(site)

for l in data.readlines():
    print(l.decode('utf-8'))