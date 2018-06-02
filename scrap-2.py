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
#│   ├── toc.ncx
#│   ├── content.opf
#│   ├── (stylesheet.css)
#│   ├── 000.xhtml
#│   ├── 001.xhtml
#│   ├──     .
#│   ├──     .
#│   ├──     .

identifier = u'narou-epub.' + sys.argv[1] + '.' + str(uuid.uuid4()).upper()
depth = 1
totalPageCount = len(shel['titles'])
maxPageNumber = len(shel['titles'])

bookLanguage_2moji, bookTitle, bookAuthor, bookLanguage_5moji, bookRights, bookPublisher = ['ja', shel['book_title'], shel['book_auther'], u'ja_JP', u'知らないよ！', u'小説家になろう']

#toc.ncx作成

toc_ncx = u'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="%s"/>
        <meta name="dtb:depth" content="%s"/>
        <meta name="dtb:totalPageCount" content="%s"/>
        <meta name="dtb:maxPageNumber" content="%s"/>
    </head>
    <doctitle>
        <text>%s</text>
    </doctitle>
    <navMap>''' % (identifier, depth, totalPageCount, maxPageNumber, bookTitle)

for i in range(0, len(shel['titles'])):
  toc_ncx += u'''
        <navPoint id="%s" playOrder="%s">
            <navLabel><text>%s</text></navLabel>
            <content src="%s.xhtml"/>
        </navPoint>''' % (i + 1, i + 1, shel['titles'][i], i + 1)

toc_ncx += u'''
    </navMap>
</ncx>'''


#content.opf作成

content_opf = u'''<package version="3.0" xml:lang="%s" unique-identifier="pub-id" xmlns="http://www.idpf.org/2007/opf">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>%s</dc:title>
        <dc:creator id="aut">%s</dc:creator>
        <dc:language>%s</dc:language>
        <dc:rights>%s</dc:rights>
        <dc:publisher>%s</dc:publisher>
        <dc:identifier id="BookId">%s</dc:identifier>
    </metadata>
    <manifest>
        <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml" />
        <item id="style" href="stylesheet.css" media-type="text/css" />''' % (bookLanguage_2moji, bookTitle, bookAuthor, bookLanguage_5moji, bookRights, bookPublisher, identifier)

for i in range(0, len(shel['titles'])):
  content_opf += u'''
        <item id="%s" href="%s.xhtml" media-type="application/xhtml+xml" properties="nav" />''' % (i + 1, i + 1)

content_opf += u'''
    </manifest>
    <spine toc="ncx">'''

for i in range(0, len(shel['titles'])):
  content_opf += u'''
        <itemref idref="%s" />''' % (i + 1)

content_opf += u'''
    </spine>
</package>'''

#xhtmlファイル(本体)作成

xhtmls = {}

for i in range(0, len(shel['titles'])):
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
</html>''' % (bookLanguage_2moji, bookLanguage_2moji, shel['titles'][i], shel['titles'][i], strdata)

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

#File minetype
f = open(os.path.join(rootdir, 'minetype'), 'w')
f.write('application/epub+zip')
f.close()

#Directory META-INF/ (container.xml)
os.mkdir(os.path.join(rootdir, 'META-INF'))

f = open(os.path.join(rootdir, 'META-INF/container.xml'), 'w')
f.write(container_xml)
f.close()

#Directory OEBPS/ (toc.ncx, content.opf, and xhtml documents)
os.mkdir(os.path.join(rootdir, 'OEBPS'))

f = open(os.path.join(rootdir, 'OEBPS/toc.ncx'), 'w')
f.write(toc_ncx)
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