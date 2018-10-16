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

#===============
#ここからページ取得
#===============

try:
  soup = BeautifulSoup(requests.get('http://www.mai-net.net/bbs/sst/sst.php?act=dump&cate=16&all=' + sys.argv[1] + '&n=53#kiji').content.decode('utf-8'), "html.parser")
except:
  sys.exit('Novel not found')

shel = shelve.open(sys.argv[1] + '.' + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-") + "%03d" % (datetime.now().microsecond // 1000) + '.shelve', writeback=True)

shel['book_title']       = sys.argv[1]

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
    soup = BeautifulSoup(requests.get('http://ncode.syosetu.com/' + sys.argv[1] + '/' + str(i) + '/').content.decode('utf-8'), "html.parser")
    
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