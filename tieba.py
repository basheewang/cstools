#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: TieBa.py

# Time-stamp: <Coeus Wang: 2016-02-24 00:03:56>

import http.cookiejar
import urllib
from bs4 import BeautifulSoup
import ipdb
# import requests
# import re
# import sys
import urllib.request
# from optparse import OptionParser
# from os import sep, path, makedirs, remove, chdir, system
# from PIL import Image
# from PyPDF2 import PdfFileMerger, PdfFileReader
# from subprocess import call

# script_path = path.dirname(path.abspath(__file__))


# For debug purpose.
def saveFile(data, s, coding='gbk'):
    # save_path = 'temp.out'
    f_obj = open('temp_' + s + '.html', 'wb')
    f_obj.write(bytes(data, coding))
    f_obj.close()


# Get URL data
def getURLData(url, coding='gbk'):
    res = urllib.request.urlopen(url)
    html_data = res.read().decode(coding, 'ignore')
    return html_data


def ParseTieBa(url):
    cj = http.cookiejar.LWPCookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cj))
    urllib.request.install_opener(opener)
    opener.addheaders = [
        ("User-agent",
         "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 " +
         "(KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"),
        ("Connection", "keep-alive"),
        ("Host", "login.taobao.com"),
        ("Referer", "https://login.taobao.com/member/login.jhtml")
    ]

    indexhtml = getURLData(url)
    soup = BeautifulSoup(indexhtml, 'html.parser')

    all_cat = {}
    for tbm in soup.find_all('div', attrs={'class': 'class-item'}):
        menu = tbm.find('a', attrs={'class': 'class-item-title'}).text
        sub_menu = [t.text for t in tbm.find_all('li')]
        all_cat[menu] = sub_menu

    print("There are following categorizes as below:")
    i = 0
    menu_list = []
    for m in sorted(all_cat.keys()):
        i += 1
        menu_list.append(m)
        print(i, '. ', m)
    m_select = input("please select one: ")
    s_menu = menu_list[int(m_select) - 1]
    print("You select menu index [", m_select, "] ->", s_menu)

    print("There are following sub-categorizes as below:")
    j = 0
    submenu_list = []
    for sm in all_cat[s_menu]:
        j += 1
        submenu_list.append(sm)
        print(j, '.', sm)
    sm_select = input("please select one: ")
    s_submenu = submenu_list[int(sm_select) - 1]
    print("You select sub menu index [", sm_select, "] ->", s_submenu)
    getTieBaList(s_menu, s_submenu)


# Get sub menu's tieba list:
def getTieBaList(s_menu, s_submenu):
    # tb_url = http://tieba.baidu.com/f/fdir? +
    # fd=%C8%CB%CE%C4%D7%D4%C8%BB&sd=%C6%E4%CB%FB%D7%D4%C8%BB%BB%B0%CC%E2&pn=1
    # fd = menu
    # sd = sub_menu
    # pn = page
    tbl_url = 'http://tieba.baidu.com/f/fdir?'
    md = {}
    md['fd'] = s_menu
    md['sd'] = s_submenu
    bin_md = urllib.parse.urlencode(md, encoding='gbk')
    tb_sub_cat_url = tbl_url + bin_md
    html_data = getURLData(tb_sub_cat_url)
    soup = BeautifulSoup(html_data, 'html.parser')
    totalpage = soup.find('div', attrs={'class': 'pagination'}).\
        find_all('a')[-1]['href'].split('&')[-1].split('=')[-1]
    all_tb = {}
    for i in range(int(totalpage)):
        print('Now working on page:', i + 1, ': Total page:', totalpage)
        md['pn'] = i + 1
        temp_url = tbl_url + urllib.parse.urlencode(md, encoding='gbk')
        sub_html_data = getURLData(temp_url)
        sub_soup = BeautifulSoup(sub_html_data, 'html.parser')
        tblist = sub_soup.find('div', attrs={'class': 'sub_dir_box'}).\
            find('table').find_all('a', attrs={'target': '_blank'})
        for tb in tblist:
            if len(tb.text) > 0:
                all_tb[tb.text] = tb['href']
    n = 0
    for kw in sorted(all_tb.keys()):
        n += 1
        print(n, ".", "Now getting data for:", kw)
        gettbDetail(all_tb[kw])


# Get Tie Ba Detail
def gettbDetail(tb_url):
    html_data = getURLData(tb_url, 'utf-8')
    soup = BeautifulSoup(html_data, 'html.parser')
    ipdb.set_trace()
    print('Hi')


# Main program
if __name__ == '__main__':
    # parser = OptionParser()
    # parser.add_option("-s", "--store_path", default=".", dest="storepath",
    #                   help="Input a path where the picture can be saved\
    #                   like: -p C:\\temp")
    # parser.add_option("-v", "--verbose", default=False, dest="verbose",
    #                   action="store_true",
    #                   help="Use this options to enable verbose mode.")
    # (options, args) = parser.parse_args()

    index_url = 'http://tieba.baidu.com/f/index/forumclass'
    ParseTieBa(index_url)
