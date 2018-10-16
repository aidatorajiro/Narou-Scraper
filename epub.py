# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import urllib.request
import os
import sys
import uuid
import tempfile
import zipfile
import shutil
import shelve
import html
import datetime

try:
  shel = shelve.open(sys.argv[1] + '.shelve', flag='r')
except:
  print('shelve file not found!')

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
#│   ├── toc.xhtml
#│   ├── content.opf
#│   ├── 000.xhtml
#│   ├── 001.xhtml
#│   ├──     .
#│   ├──     .
#│   ├──     .

identifier = u'narou-epub.' + sys.argv[1] + '.' + str(uuid.uuid4()).upper()
depth = 1
totalPageCount = len(shel['titles'])

date = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

bookLanguage_2moji, bookTitle, bookAuthor, bookLanguage_5moji, bookRights, bookPublisher = ['ja', shel['book_title'], shel['book_auther'], u'ja_JP', u'知らないよ！', u'Narou-Scraper']

#toc.xhtml作成

toc_xhtml = u'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="%s">
    <head>
        <title>%s</title>
        <meta charset="utf-8" />
    </head>
    <body>
        <nav xmlns:epub="http://www.idpf.org/2007/ops" epub:type="toc" id="toc">
            <h1>Table of Contents</h1>
            <ol>''' % (bookLanguage_2moji, bookTitle)

for i in range(0, totalPageCount):
  toc_xhtml += u'''
                <li>
                    <a href="%d.xhtml">%s</a>
                </li>''' %  (i + 1, html.escape(shel['titles'][i]))

toc_xhtml += u'''
            </ol>
        </nav>
    </body>
</html>'''

#content.opf作成

content_opf = u'''<?xml version="1.0" encoding="utf-8" standalone="no"?>
<package xmlns="http://www.idpf.org/2007/opf" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" version="3.0" xml:lang="%s" unique-identifier="pub-identifier">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>%s</dc:title>
        <dc:creator id="creator">%s</dc:creator>
        <dc:language>%s</dc:language>
        <dc:rights>%s</dc:rights>
        <dc:publisher>%s</dc:publisher>
        <dc:identifier id="pub-identifier">urn:uuid:%s</dc:identifier>
        <dc:date>%s</dc:date>
        <meta property="dcterms:modified">%s</meta>
    </metadata>
    <manifest>
        <item id="htmltoc" properties="nav" media-type="application/xhtml+xml" href="toc.xhtml" />''' % (bookLanguage_2moji, bookTitle, bookAuthor, bookLanguage_2moji, bookRights, bookPublisher, identifier, date, date)

for i in range(0, totalPageCount):
  content_opf += u'''
        <item id="page-%s" href="%s.xhtml" media-type="application/xhtml+xml" />''' % (i + 1, i + 1)

content_opf += u'''
    </manifest>
    <spine>'''

for i in range(0, totalPageCount):
  content_opf += u'''
        <itemref idref="page-%s" linear="yes" />''' % (i + 1)

content_opf += u'''
    </spine>
</package>'''

#xhtmlファイル(本体)作成

xhtmls = {}

for i in range(0, totalPageCount):
  strdata = u'';
  
  if shel['novel_p_arr'][i]:
    strdata += shel['novel_p_arr'][i]
    strdata += u'\n<br /><hr />\n'
  
  if shel['novel_honbun_arr'][i]:
    strdata += shel['novel_honbun_arr'][i]
    strdata += u'\n<br /><hr />\n'
  
  if shel['novel_a_arr'][i]:
    strdata += shel['novel_a_arr'][i]
    strdata += u'\n<br /><hr />\n'
  
  xhtmls[i + 1] = u'''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2011/epub" lang="%s" xml:lang="%s">
<head>
  <title>%s</title>
</head>
<body>
  <h1>%s</h1>
  %s
</body>
</html>''' % (bookLanguage_2moji, bookLanguage_2moji, html.escape(shel['titles'][i]), html.escape(shel['titles'][i]), strdata)

#container.xml作成

container_xml = u'''<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''


#===============
#ここからzipコンテナ作り
#===============

rootdir = tempfile.mkdtemp()

#File mimetype
f = open(os.path.join(rootdir, 'mimetype'), 'w')
f.write('application/epub+zip')
f.close()

#Directory META-INF/ (container.xml)
os.mkdir(os.path.join(rootdir, 'META-INF'))

f = open(os.path.join(rootdir, 'META-INF/container.xml'), 'w')
f.write(container_xml)
f.close()

#Directory OEBPS/ (toc.xhtml, content.opf, and xhtml documents)
os.mkdir(os.path.join(rootdir, 'OEBPS'))

f = open(os.path.join(rootdir, 'OEBPS/toc.xhtml'), 'w')
f.write(toc_xhtml)
f.close()

f = open(os.path.join(rootdir, 'OEBPS/content.opf'), 'w')
f.write(content_opf)
f.close()

for k, v in xhtmls.items():
  f = open(os.path.join(rootdir, 'OEBPS/%s.xhtml' % k), 'w')
  f.write(v)
  f.close()

print(rootdir)

#zipに圧縮
zipf = zipfile.ZipFile(sys.argv[1] + '.epub', 'w')

os.chdir(rootdir)

for root, dirs, files in os.walk(rootdir):
    for file in files:
        zipf.write(os.path.relpath(os.path.join(root, file), rootdir))

zipf.close()

#こみを消す
shutil.rmtree(rootdir)
