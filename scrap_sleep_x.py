# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import urllib.request
from urllib.error import HTTPError
import requests
import os
import sys
import time
import tempfile
import zipfile
import shutil
import shelve
from datetime import datetime

# まず、クッキーを取得。
headers = {'User-Agent': 'TheGreatestBrowser 1.0'}
cookies = requests.get('http://noc.syosetu.com/').cookies
cookies["over18"] = "yes"

# 取得したクッキーを利用してアクセスする。
def get_http_data(url):
    r = requests.get(url, headers=headers, cookies=cookies)
    return r.content

#===============
#ここからページ取得
#===============

try:
  soup = BeautifulSoup(get_http_data('http://novel18.syosetu.com/' + sys.argv[1] + '/').decode('utf-8'), "html.parser")
except:
  sys.exit('Novel not found')

shel = shelve.open(sys.argv[1] + '.' + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-") + "%03d" % (datetime.now().microsecond // 1000) + '.shelve', writeback=True)

shel['book_title']       = soup.find("title").text

if soup.find("div", {"class": "novel_writername"}).find("a"):
    shel['book_auther']  = soup.find("div", {"class": "novel_writername"}).find("a").text
else:
    shel['book_auther']  = soup.find("div", {"class": "novel_writername"}).text.strip("\r\n")[3:]

shel['titles']           = []
shel['novel_p_arr']      = []
shel['novel_honbun_arr'] = []
shel['novel_a_arr']      = []

i = 1

#ページをwhileループで取得
while True:
  time.sleep(10)
  try:
    # ページ取得＆解析、今回はutf-8大先生！。
    soup = BeautifulSoup(get_http_data('http://novel18.syosetu.com/' + sys.argv[1] + '/' + str(i) + '/').decode('utf-8'), "html.parser")
    
    # データ取得。
    title        = soup.findAll('p', {'class' : 'novel_subtitle'})[0].text
    novel_p      = soup.find('div', {'id' : 'novel_p'     })
    novel_honbun = soup.find('div', {'id' : 'novel_honbun'})
    novel_a      = soup.find('div', {'id' : 'novel_a'     })
    
  except HTTPError as e:
    if e.code == 404:
      print('Scraping has finished.')
      break
    else:
      print('An unhandled error has found on Page' + str(i))
      continue # 再度チャレンジ
    
  except:
    if soup.find('div', {'class' : 'nothing'}) and soup.find('div', {'class' : 'nothing'}).text == "小説が見つかりません。":
      print('Scraping has finished.')
      break
    print('An unhandled error has found on Page' + str(i))
    continue # 再度チャレンジ
  
  # データ登録
  if soup.findAll('p', {'class' : 'novel_subtitle'})[0]:
    shel['titles'].append(title)
  
  if novel_p:
    shel['novel_p_arr']      .append("".join([str(x) for x in novel_p      .contents]))
  else:
    shel['novel_p_arr']      .append(None)
  
  if novel_honbun:
    shel['novel_honbun_arr'] .append("".join([str(x) for x in novel_honbun .contents]))
  else:
    shel['novel_honbun_arr'] .append(None)
  
  if novel_a:
    shel['novel_a_arr']      .append("".join([str(x) for x in novel_a      .contents]))
  else:
    shel['novel_a_arr']      .append(None)
  
  i += 1

shel.close()

"""
#===============
#ここからepub組み立て
#===============
#EPUB
#├── minetype
#│
#├── META-INF
#│   └── container.xml
#│
#├── OEBPS
#│   ├── toc.ncx
#│   ├── content.opf
#│   ├── (stylesheet.css)
#│   ├── 000.xhtml
#│   ├── 001.xhtml
#│   ├──     .
#│   ├──     .
#│   ├──     .

identifier = 'hakagiroyale.epub.B77778DA-A8C4-4069-8489-888CD0FB6A22'

#toc.ncx作成

toc_ncx = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="%s"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <doctitle>
        <text>Hakagi Royale</text>
    </doctitle>
    <navMap>''' % (identifier)

for i in range(0, len(numbers)):
  toc_ncx += u'''
        <navPoint id="%s" playOrder="%s">
            <navLabel><text>%s　%s</text></navLabel>
            <content src="%s.xhtml"/>
        </navPoint>''' % (numbers[i], i + 1, numbers[i], shel['titles'][i], numbers[i])

toc_ncx += '''
    </navMap>
</ncx>'''


#content.opf作成

content_opf = '''<?xml version="1.0" encoding="UTF-8"?>
<package version="2.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:title>Hakagi Royale</dc:title>
        <dc:creator opf:role="aut">Unknown</dc:creator>
        <dc:language>ja-JP</dc:language>
        <dc:rights>Unknown</dc:rights>
        <dc:publisher>Unknown</dc:publisher>
        <dc:identifier id="BookId">%s</dc:identifier>
    </metadata>
    <manifest>
        <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml" />
        <item id="style" href="stylesheet.css" media-type="text/css" />''' % (identifier)

for i in range(0, len(numbers)):
  content_opf += '''
        <item id="%s" href="%s.xhtml" media-type="application/xhtml+xml" />''' % (numbers[i], numbers[i])

content_opf += '''
    </manifest>
    <spine toc="ncx">'''

for i in range(0, len(numbers)):
  content_opf += '''
        <itemref idref="%s" />''' % (numbers[i])

content_opf += '''
    </spine>
</package>'''

#xhtmlファイル(本体)作成

xhtmls = []

for i in range(0, len(numbers)):
  strdata = str(datas[i]).decode('utf-8').replace('</br>', '').replace('<br>', '<br />')
  xhtmls.append(u'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2011/epub" lang="ja" xml:lang="ja">
<head>
  <title></title>
</head>
<body>
  <h1>%s　%s</h1>
  <br /><br />
  %s
</body>
</html>''' % (numbers[i], shel['titles'][i], strdata))

#container.xml作成

container_xml = '''<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''

#===============
#ここからzipコンテナ作り
#===============

rootdir = tempfile.mkdtemp()

f = open(os.path.join(rootdir, 'minetype'), 'w')
f.write('application/epub+zip')
f.close()

#META-INF
os.mkdir(os.path.join(rootdir, 'META-INF'))

f = open(os.path.join(rootdir, 'META-INF/container.xml'), 'w')
f.write(container_xml)
f.close()

#OEBPS
os.mkdir(os.path.join(rootdir, 'OEBPS'))

f = open(os.path.join(rootdir, 'OEBPS/toc.ncx'), 'w')
f.write(toc_ncx.encode('utf-8'))
f.close()

f = open(os.path.join(rootdir, 'OEBPS/content.opf'), 'w')
f.write(content_opf.encode('utf-8'))
f.close()

for i in range(0, len(numbers)):
  f = open(os.path.join(rootdir, 'OEBPS/' + numbers[i] + '.xhtml'), 'w')
  f.write(xhtmls[i].encode('utf-8'))
  f.close()

print rootdir

#zipに圧縮
zipf = zipfile.ZipFile('Python.zip', 'w')

os.chdir(rootdir)

for root, dirs, files in os.walk(rootdir):
    for file in files:
        zipf.write(os.path.relpath(os.path.join(root, file), rootdir))

zipf.close()

#こみを消す
shutil.rmtree(rootdir)
"""