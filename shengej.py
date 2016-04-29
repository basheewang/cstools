#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: taobao.py

import http.cookiejar
import urllib.request
from bs4 import BeautifulSoup
import re
import webbrowser
from selenium import webdriver
# from getpass import getpass
# import json
# import requests
from optparse import OptionParser
# import sys
from os import sep
from os import remove
from os.path import isdir
from os.path import getsize
from os import makedirs
# import socket
# import math
import time

# global subfolder
# global outputpath
syj_real_url = 'http://c19.shengejing.com/'
datacate = {
    'topbb': '热销宝贝TOP100',
    'topshop': '热销店铺TOP30',
    'submarket': '子行业成交量分布',
    'brand': '品牌成交量分布',
    'price': '宝贝价格分布',
    'prop': '属性成交量分布',
}


# For debug purpose.
def saveFile(data, s, coding='gbk'):
    # save_path = 'temp.out'
    f_obj = open('temp_' + s + '.html', 'wb')
    f_obj.write(bytes(data, coding))
    f_obj.close()


# parse subcat page, to get subcat of category.
def parse_sc_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    subcate = []
    for tt in soup.find_all('table'):
        # print(tt.attrs)
        if len(tt.attrs) == 0:
            for href in tt.find_all('a', attrs={'class', 'subcate'}):
                # print(href.text)
                subcate.append((href.text, syj_real_url + href.attrs['href']))
    return subcate


# Parse top level html to get a list of categories
def parse_ssc_html(mydrv, ssc_name, url):
    # soup = BeautifulSoup(html, 'html.parser')
    sscate = {}
    # for tt in soup.find_all('table'):
    #     # print(tt.attrs)
    #     if len(tt.attrs) == 0:
    #         for href in tt.find_all('a', attrs={'class', 'subcate'}):
    #             # print(href.text)
    #             subcat = (href.text, syj_real_url + href.attrs['href'])
    # print("Now getting a list of subcate for:", subcat[0])
    md = {}
    md['gcate'] = re.compile(r'gcate=(.*)&cate').search(url).group(1)
    bin_md = urllib.parse.urlencode(md, encoding='gbk')
    subcat_url = url.replace('gcate=' + md['gcate'], bin_md)
    mydrv.get(subcat_url)
    subcat_html = mydrv.page_source.encode('gbk', 'ignore').decode('gbk')
    subsoup = BeautifulSoup(subcat_html, 'html.parser')
    subcatsel = subsoup.find('select', attrs={'id': 'subcid'})
    subsubcate = []
    for sc in subcatsel.find_all('option'):
        if sc.attrs['value'] != '':
            sscname = sc.text.replace(u'\xa0', u' ').replace(u'\u3000', u' ')
            ssc_url = subcat_url + \
                "&subcid=" + sc.attrs['value']
            subsubcate.append((sscname, ssc_url))
    # print(subsubcate)
    sscate[ssc_name] = subsubcate
    return sscate

    # subcatdict = {}
    # for span in tt.find_all('a', attrs={'class', 'goods'}):
    #     if 'cat' in span.attrs['id']:
    #         # print("\t" + span.text)
    #         subcatid = span.text

    # subcatiddetail = {}
    # for href1 in tt.find_all('a', attrs={'class', 'hot'}):
    #     if 'subcid' in href1.attrs['href']:
    #         # print("\t\t" + href1.text + " -> " +
    #         #       href1.attrs['href'])
    #         subcatiddetail[href1.text] = href1.attrs['href']
    #         subcatdict[subcatid] = subcatiddetail

    # for span in tt.find_all('a', attrs={'class', 'goods'}):
    #     if 'pp' in span.attrs['id']:
    #         # print("\t" + span.text)
    #         subcatpp = span.text

    # subcatppdetail = {}
    # for href1 in tt.find_all('a', attrs={'class', 'hot'}):
    #     if 'brand' in href1.attrs['href']:
    #         # print("\t\t" + href1.text + " -> " +
    #         #       href1.attrs['href'])
    #         subcatppdetail[href1.text] = href1.attrs['href']
    #         subcatdict[subcatpp] = subcatppdetail

    # dataall[root] = subcatdict


# Get avaiable Years and Months
def getyandm(html):
    ymm = re.compile('(yearmonthmap\[\d{4}\].*);\s+\$')
    if ymm.search(html):
        ymm_list = ymm.search(html).group(1).\
            replace('&lt;', '<').replace('&gt;', '>').split(';')
        ymmdict = {}
        for y in ymm_list:
            year = y.split('[')[1].split(']')[0]
            months = re.findall('>(\d\d)<', y)
            ymmdict[year] = months

    # if len(ymmdict.keys()) > 1:
    #     print("There are several year's data as below:")
    #     i = 0
    #     for y in sorted(ymmdict.keys()):
    #         i += 1
    #         print(i, '. ' + y)
    #     print(i + 1, '. ALL')
    #     y_select = input("Please select a year: ")
    #     if y_select != 'ALL':
    #         j = 0
    #         for m in sorted(ymmdict[y_select]):
    #             j += 1
    #         print(j, '. ' + m)
    #         print(j + 1, '. ALL')
    #         m_select = input("Please select a month: ")
    # return y_select, m_select
    return ymmdict


# To save csv files
def getcsv(mydrv, url, y, m, outputpath):
    print("The current data is for: " + y + "_" + m)
    dmd = {}
    dmd['year'] = y
    dmd['month'] = m
    if 'subfunc' not in url:
        dmd['subfunc'] = 'topbb'
    bin_dmd = urllib.parse.urlencode(dmd, encoding='gbk')

    # Get 热销宝贝TOP100
    topbb_url = url + "&" + bin_dmd
    print("  Now trying to get 热销宝贝TOP100...", end="")
    savetopbb(mydrv, topbb_url, y, m, outputpath)

    # Get 热销店铺TOP30
    topshop_url = topbb_url.replace('topbb', 'topshop')
    print("  Now trying to get 热销店铺TOP30...", end="")
    savetopshop(mydrv, topshop_url, y, m, outputpath)

    # Get 子行业成交量分布
    submarket_url = topbb_url.replace('topbb', 'submarket')
    print("  Now trying to get 子行业成交量分布...", end="")
    savesubmarket(mydrv, submarket_url, y, m, outputpath)

    # Get 品牌成交量分布
    brand_url = topbb_url.replace('topbb', 'brand')
    print("  Now trying to get 品牌成交量分布...", end="")
    savebrand(mydrv, brand_url, y, m, outputpath)

    # Get 宝贝价格分布
    price_url = topbb_url.replace('topbb', 'price')
    print("  Now trying to get 宝贝价格分布...", end="")
    saveprice(mydrv, price_url, y, m, outputpath)

    # Get 属性成交量分布
    prop_url = topbb_url.replace('topbb', 'prop')
    print("  Now trying to get 属性成交量分布...")
    saveprop(mydrv, prop_url, y, m, outputpath)


def fetchdata(mydrv, url, outputpath):
    cjk_pat = re.compile(r'[\u4e00-\u9fa5]+')
    if cjk_pat.search(url):
        md = {}
        md['gcate'] = re.compile(r'gcate=(.*)&cate').search(url).group(1)
        bin_md = urllib.parse.urlencode(md, encoding='gbk')
        url = url.replace('gcate=' + md['gcate'], bin_md)

    mydrv.get(url)
    time.sleep(2)
    detaildata = mydrv.page_source.encode('gbk', 'ignore').decode('gbk')

    ymmdict = getyandm(detaildata)
    if options.alldate is False:
        if len(ymmdict.keys()) > 1:
            print("There are several year's data as below:")
            i = 0
            for y in sorted(ymmdict.keys()):
                i += 1
                print(i, '. ' + y)
            print(i + 1, '. ALL')
            y_idx_select = input("Please select a year: ")
            if int(y_idx_select) <= i:
                y_select = sorted(list(ymmdict.keys()))[int(y_idx_select) - 1]
            else:
                y_select = 'ALL'
            if y_select != 'ALL':
                j = 0
                for m in sorted(ymmdict[y_select]):
                    j += 1
                    print(j, '. ' + m)
                print(j + 1, '. ALL')
                m_idx_select = input("Please select a month: ")
                if int(m_idx_select) <= j:
                    m_select = sorted(ymmdict[y_select])[int(m_idx_select) - 1]
                else:
                    m_select = 'ALL'
    else:
        y_select = 'ALL'
        m_select = 'ALL'

    if y_select != 'ALL' and m_select != 'ALL':
        getcsv(mydrv, url, y_select, m_select, outputpath)
    elif y_select != 'ALL' and m_select == 'ALL':
        for m in sorted(ymmdict[y_select]):
            getcsv(mydrv, url, y_select, m, outputpath)
    elif y_select == 'ALL':
        for y in sorted(ymmdict.keys()):
            for m in sorted(ymmdict[y]):
                getcsv(mydrv, url, y, m, outputpath)


def saveprice(mydrv, url, year, month, outputpath):
    mydrv.get(url)
    html = mydrv.page_source.encode('gbk', 'ignore').decode('gbk')
    soup = BeautifulSoup(html, 'html.parser')
    makedirs(outputpath + sep + datacate['price'] + sep + year,
             exist_ok=True)
    csv = open(outputpath + sep + datacate['price'] + sep +
               year + sep + month + '.csv', 'w', encoding='gbk')
    # csv = sys.stdout
    for tt in soup.find_all('table', attrs={'name': 'markettable'}):
        for th in tt.find('thead'):
            thead = []
            for tr in th.find_all('th'):
                print(tr.text, end=',', file=csv)
                thead.append(tr.text)
            print(file=csv)

        for tb in tt.find_all('tbody'):
            for tr in tb.find_all('tr'):
                for td in tr.find_all('td'):
                    try:
                        print(td.text, end=',', file=csv)
                    except UnicodeEncodeError:
                        print(td.text.encode('gb18030'), end=',', file=csv)
                print(file=csv)
    csv.close()
    csvfile = outputpath + sep + datacate['price'] + sep + \
        year + sep + month + '.csv'
    if getsize(csvfile) < 50:
        print("\tThere is no price data for current year_month.")
        remove(csvfile)
    else:
        print("Data have been save to: " + csvfile)


def savesubmarket(mydrv, url, year, month, outputpath):
    mydrv.get(url)
    html = mydrv.page_source.encode('gbk', 'ignore').decode('gbk')
    self_pat = re.compile(r'子行业成交量分布')
    if not self_pat.search(html):
        print("No such category!")
        return

    soup = BeautifulSoup(html, 'html.parser')
    makedirs(outputpath + sep + datacate['submarket'] + sep + year,
             exist_ok=True)
    csv = open(outputpath + sep + datacate['submarket'] + sep +
               year + sep + month + '.csv', 'w', encoding='gbk')
    # csv = sys.stdout
    for tt in soup.find_all('table', attrs={'name': 'markettable'}):
        for th in tt.find('thead'):
            thead = []
            for tr in th.find_all('th'):
                print(tr.text, end=',', file=csv)
                thead.append(tr.text)
            print(file=csv)

        for tb in tt.find_all('tbody'):
            for tr in tb.find_all('tr'):
                for td in tr.find_all('td'):
                    try:
                        print(td.text, end=',', file=csv)
                    except UnicodeEncodeError:
                        print(td.text.encode('gb18030'), end=',', file=csv)
                print(file=csv)
    csv.close()
    csvfile = outputpath + sep + datacate['submarket'] + sep + \
        year + sep + month + '.csv'
    if getsize(csvfile) < 50:
        print("\tThere is no submarket data for current year_month.")
        remove(csvfile)
    else:
        print("Data have been save to: " + csvfile)


def savebrand(mydrv, url, year, month, outputpath):
    mydrv.get(url)
    html = mydrv.page_source.encode('gbk', 'ignore').decode('gbk')
    soup = BeautifulSoup(html, 'html.parser')
    makedirs(outputpath + sep + datacate['brand'] + sep + year,
             exist_ok=True)
    csv = open(outputpath + sep + datacate['brand'] + sep +
               year + sep + month + '.csv', 'w', encoding='gbk')
    # csv = sys.stdout
    for tt in soup.find_all('table', attrs={'name': 'markettable'}):
        for th in tt.find('thead'):
            thead = []
            for tr in th.find_all('th'):
                print(tr.text, end=',', file=csv)
                thead.append(tr.text)
            print(file=csv)

        for tb in tt.find_all('tbody'):
            for tr in tb.find_all('tr'):
                for td in tr.find_all('td'):
                    try:
                        print(td.text, end=',', file=csv)
                    except UnicodeEncodeError:
                        print(td.text.encode('gb18030'), end=',', file=csv)
                print(file=csv)
    csv.close()
    csvfile = outputpath + sep + datacate['brand'] + sep + \
        year + sep + month + '.csv'
    if getsize(csvfile) < 50:
        print("\tThere is no brand data for current year_month.")
        remove(csvfile)
    else:
        print("Data have been save to: " + csvfile)


def savetopbb(mydrv, url, year, month, outputpath):
    mydrv.get(url)
    html = mydrv.page_source.encode('gbk', 'ignore').decode('gbk')
    soup = BeautifulSoup(html, 'html.parser')
    makedirs(outputpath + sep + datacate['topbb'] + sep + year,
             exist_ok=True)
    csv = open(outputpath + sep + datacate['topbb'] + sep +
               year + sep + month + '.csv', 'w', encoding='gbk')
    for tt in soup.find_all('table', attrs={'name': 'markettable'}):
        for th in tt.find('thead'):
            thead = []
            for tr in th.find_all('th'):
                if tr.attrs['id'] != '图片' and tr.attrs['id'] != '信用':
                    print(tr.text, end=',', file=csv)
                    thead.append(tr.text)
            print(file=csv)

        for tb in tt.find_all('tbody'):
            for tr in tb.find_all('tr'):
                for td in tr.find_all('td'):
                    if td.attrs['headers'][0] != '图片' \
                       and td.attrs['headers'][0] != '信用':
                        try:
                            print(td.text, end=',', file=csv)
                        except UnicodeEncodeError:
                            print(td.text.encode('gb18030'), end=',', file=csv)
                print(file=csv)
    csv.close()
    csvfile = outputpath + sep + datacate['topbb'] + sep + \
        year + sep + month + '.csv'
    if getsize(csvfile) < 50:
        print("\tThere is no topbb data for current year_month.")
        remove(csvfile)
    else:
        print("Data have been save to: " + csvfile)


def saveprop(mydrv, url, year, month, outputpath):
    mydrv.get(url)
    html = mydrv.page_source.encode('gbk', 'ignore').decode('gbk')
    soup = BeautifulSoup(html, 'html.parser')
    prop = {}
    for cate in soup.find_all('a', attrs={'class': 'cate'}):
        v_str = cate['onclick']
        pval = re.compile('value=\'(.*)\'').search(v_str).group(1)
        prop[cate.text] = '&prop=' + pval
    for pk in sorted(prop.keys()):
        makedirs(outputpath + sep + datacate['prop'] + sep + pk + sep + year,
                 exist_ok=True)
        csv = open(outputpath + sep + datacate['prop'] + sep + pk + sep +
                   year + sep + month + '.csv', 'w', encoding='gbk')
        mydrv.get(url + prop[pk])
        pkhtml = mydrv.page_source.encode('gbk', 'ignore').decode('gbk')
        pksoup = BeautifulSoup(pkhtml, 'html.parser')
        for tt in pksoup.find_all('table', attrs={'name': 'markettable'}):
            for th in tt.find('thead'):
                thead = []
                for tr in th.find_all('th'):
                    if tr.attrs['id'] != '信用' and tr.attrs['id'] != '店内热卖':
                        print(tr.text, end=',', file=csv)
                        thead.append(tr.text)
                print(file=csv)

            for tb in tt.find_all('tbody'):
                for tr in tb.find_all('tr'):
                    for td in tr.find_all('td'):
                        if td.attrs['headers'][0] != '信用' \
                           and td.attrs['headers'][0] != '店内热卖':
                            try:
                                print(td.text, end=',', file=csv)
                            except UnicodeEncodeError:
                                print(td.text.encode('gb18030'), end=',',
                                      file=csv)
                    print(file=csv)
        csv.close()
        csvfile = outputpath + sep + datacate['prop'] + sep + pk + sep + \
            year + sep + month + '.csv'
        if getsize(csvfile) < 50:
            print("\tThere is no prop data for current year_month:", pk)
            remove(csvfile)
        else:
            print(" " * 28 + "Data have been save to: " + csvfile)


def savetopshop(mydrv, url, year, month, outputpath):
    mydrv.get(url)
    html = mydrv.page_source.encode('gbk', 'ignore').decode('gbk')
    soup = BeautifulSoup(html, 'html.parser')
    makedirs(outputpath + sep + datacate['topshop'] + sep + year,
             exist_ok=True)
    csv = open(outputpath + sep + datacate['topshop'] + sep +
               year + sep + month + '.csv', 'w', encoding='gbk')
    for tt in soup.find_all('table', attrs={'name': 'markettable'}):
        for th in tt.find('thead'):
            thead = []
            for tr in th.find_all('th'):
                if tr.attrs['id'] != '信用' and tr.attrs['id'] != '店内热卖':
                    print(tr.text, end=',', file=csv)
                    thead.append(tr.text)
            print(file=csv)

        for tb in tt.find_all('tbody'):
            for tr in tb.find_all('tr'):
                for td in tr.find_all('td'):
                    if td.attrs['headers'][0] != '信用' \
                       and td.attrs['headers'][0] != '店内热卖':
                        try:
                            print(td.text, end=',', file=csv)
                        except UnicodeEncodeError:
                            print(td.text.encode('gb18030'), end=',', file=csv)
                print(file=csv)
    csv.close()
    csvfile = outputpath + sep + datacate['topshop'] + sep + \
        year + sep + month + '.csv'
    if getsize(csvfile) < 50:
        print("\tThere is no topshop data for current year_month.")
        remove(csvfile)
    else:
        print("Data have been save to: " + csvfile)


def charlogin(url, html, login_data):
    charcode_pat = re.compile(r'请输入验证码')
    slide_pat = re.compile(r'请拖动滑块完成验证')
    if charcode_pat.search(html):
        print("You need input char code.")
        soup = BeautifulSoup(html, 'html.parser')
        char_url = soup.find('img',
                             attrs={'id': "J_StandardCode_m"})['data-src']
        # char_pat = re.compile(r'<img id="J_StandardCode_m.*?' +
        #                       'data-src="(.*?)"')
        # if char_pat.search(html):
        #     char_url = char_pat.search(html).group(1)
        webbrowser.open(char_url)
        charcode = input("Please input char code: ")
        login_data['TPL_checkcode'] = charcode

        return_data = urllib.parse.urlencode(login_data,
                                             encoding='gbk')
        bin_data = return_data.encode('gbk')
        req = urllib.request.Request(url, bin_data)
        print("Now trying to login to taobao with char code...")
        res = urllib.request.urlopen(req)
        data = res.read().decode('gbk', 'ignore')

        ht_pat = re.compile(r'\"J_HToken\"\s+value=\"([\w\-]*)\"')
        if ht_pat.search(data):
            print("Char code correctly, login successfully!")
            return
        else:
            print("You have input wrong char code! Check carefully.")
            charlogin(url, html, login_data)
    elif slide_pat.search(html):
        print('You need slide to verify...')
        mydrv = webdriver.Chrome()
        mydrv.get(url)
        time.sleep(2)
        input("Press Enter to continue...")
        # login_html = mydrv.page_source.encode('gbk', 'ignore').decode('gbk')
        loginbtn = mydrv.find_element_by_id('J_SubmitStatic')
        loginbtn.click()
        time.sleep(10)
        syj_url = 'https://fuwu.taobao.com/using/serv_using.htm?' + \
                  'service_code=APP_SERVICE_TOP_SEJ'
        mydrv.get(syj_url)
        time.sleep(10)
        # mydrv.get('http://c19.shengejing.com/index.php?login=true')
        # time.sleep(5)
        syj_data_url = 'http://c19.shengejing.com/index.php?tab=3'
        mydrv.get(syj_data_url)
        time.sleep(5)
        data_html = mydrv.page_source.encode('gbk', 'ignore').decode('gbk')
        getData(mydrv, data_html)
        # print('hi')
        mydrv.close()
    else:
        print("strange error,  now exit.")
        exit()


def getData(mydrv, html):
    soup = BeautifulSoup(html, "html.parser")
    prod_list = {}
    for item in soup.find_all(href=True):
        if 'cate' in item.attrs['href']:
            prod_list[item.text] = syj_real_url + \
                                   item.attrs['href']

    if len(prod_list.keys()) > 1:
        print("There are several categories as below:")
        i1_c = 0
        for p in sorted(prod_list.keys()):
            i1_c += 1
            print(i1_c, '. ', p)
        print(i1_c + 1, '.  ALL')
        c_sel = input("Please choose index or input ALL for all: ")
        if c_sel != 'ALL' and int(c_sel) != i1_c + 1:
            selected_cate = sorted(list(prod_list.keys()))[int(c_sel) - 1]
            prod_list = {k: v for k, v in prod_list.items()
                         if k == selected_cate}

    for lvl1 in sorted(prod_list.keys()):
        print("Now checking category: " + lvl1)
        temp_list = prod_list[lvl1].split("&")
        md_list = temp_list[-1].split("=")
        md = {}
        md[md_list[0]] = md_list[1]
        md_data = urllib.parse.urlencode(md, encoding='gbk')
        cate_url = "&".join(temp_list[:-1]) + "&" + md_data

        mydrv.get(cate_url)
        time.sleep(5)
        lvl2_html = mydrv.page_source.encode('gbk', 'ignore').decode('gbk')
        subcate = parse_sc_html(lvl2_html)

        if len(subcate) > 1:
            print("There are several sub-cats as below:")
            i2_sc = 0
            for sc in sorted(subcate):
                i2_sc += 1
                print(i2_sc, '. ', sc[0])
            print(i2_sc + 1, '.  ALL')
            print(i2_sc + 2, '.  SELF')
            sc_sel = input("Please choose index or input " +
                           "ALL for all subcategories or " +
                           "SELF for itself: ")
            if int(sc_sel) <= i2_sc:
                seled_sc = sorted(subcate)[int(sc_sel) - 1]
                subcate = [l for l in subcate if l == seled_sc]

        if sc_sel == 'SELF' or int(sc_sel) == i2_sc + 2:
            print("Here is a list of sub-catefories:")
            i2_sc = 0
            for sc in sorted(subcate):
                i2_sc += 1
                print(i2_sc, '. ', sc[0])
            print(i2_sc + 1, '. ALL')
            sc_sel = input("Please choose index or input ALL for all: ")
            if int(sc_sel) <= i2_sc:
                seled_sc = sorted(subcate)[int(sc_sel) - 1]
                subcate = [l for l in subcate if l == seled_sc]
            for sc in sorted(subcate):
                print("Now extract data for: " + sc[0])
                subfolder = lvl1 + sep + \
                    sc[0].replace('/', '_') + \
                    sep + "SELF"
                outputpath = options.output + sep + subfolder
                makedirs(outputpath, exist_ok=True)
                pk_url = sc[1]
                fetchdata(mydrv, pk_url, outputpath)
        else:
            for sc in sorted(subcate):
                print("Now checking sub-category: " + sc[0])
                sscate = parse_ssc_html(mydrv, sc[0], sc[1])
                if len(sscate[sc[0]]) > 1:
                    print("There are several sub-sub-cates as below:")
                    i3_d = 0
                    for d in sscate[sc[0]]:
                        i3_d += 1
                        print(i3_d, '. ', d[0])
                    print(i3_d + 1, '. ALL')
                    d_sel = input("Please choose index or ALL for all: ")
                if d_sel != 'ALL' and int(d_sel) != i3_d + 1:
                    seled_d = sscate[sc[0]][int(d_sel) - 1]
                    sscate[sc[0]] = [l for l in sscate[sc[0]]
                                     if l == seled_d]
                for ssc in sscate[sc[0]]:
                    print("\n -> Now checking details for: " + ssc[0])
                    subfolder = lvl1 + sep + \
                        sc[0].replace('/', '_') + sep + \
                        ssc[0].replace('/', '_').\
                        replace(' ', '').\
                        replace('|--', '')
                    outputpath = options.output + sep + subfolder
                    makedirs(outputpath, exist_ok=True)
                    # print(subprod_url)
                    fetchdata(mydrv, ssc[1], outputpath)


def login(url):

    user = '廖记棒棒鸡旗舰店:数据中心'
    # user = input("Please input your user name: ")
    # pwd = getpass("Please input password for " + user + ": ")
    pwd = 'a1230456'

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
    login_data = {
        # 'ua': myua,
        # 'TPL_checkcode': '',
        'TPL_username': user,
        'TPL_password_2': pwd,
    }
    return_data = urllib.parse.urlencode(login_data, encoding='gbk')
    bin_data = return_data.encode('gbk')
    req = urllib.request.Request(url, bin_data)
    print("Now trying to login to taobao...")
    res = urllib.request.urlopen(req)
    data = res.read().decode('gbk', 'ignore')

    if res.code == 200:
        print("Now send login request to taobao...")
        charlogin(url, data, login_data)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-o", "--output", default='.' + sep, dest="output",
                      help="Input an output path, default is script folder.")
    parser.add_option("-t", "--token", default='', dest="token",
                      help="Input the token of shengejing.")
    parser.add_option("-a", "--alldate", default=False, dest="alldate",
                      action="store_true",
                      help="Use this options to get all date data.")
    parser.add_option("-s", "--subcate", default=False, dest="subcate",
                      action="store_true",
                      help="Use this options to get data fro sub-category.")
    (options, args) = parser.parse_args()

    login_page = "https://login.taobao.com/member/login.jhtml"
    if not isdir(options.output):
        makedirs(options.output)
    login(login_page)
