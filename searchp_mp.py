#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: searchp.py

import http.cookiejar
import urllib
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
import re
# import webbrowser
# from getpass import getpass
import json
import requests
from optparse import OptionParser
import sys
import os
from os import sep
import datetime
from time import time as timer
import multiprocessing as mp
# from os import remove
# from os.path import isdir
# from os.path import getsize
from os import makedirs
# import socket
import math
import ipdb


# For debug purpose.
def saveFile(data, s, coding='gbk'):
    # save_path = 'temp.out'
    f_obj = open('temp_' + s + '.html', 'wb')
    f_obj.write(bytes(data, coding))
    f_obj.close()


# To get a list of searched product's urls
def getprodurl(html):
    prod_list = []
    list_pat = re.compile(r'g_page_config\s=\s({.*});\n')
    # ipdb.set_trace()
    if list_pat.search(html):
        p_list = json.loads(list_pat.search(html).group(1))
        # cur_page = p_list['mods']['pager']['data']['currentPage']
        # print("Now checking page is", cur_page)
        i = 0
        # ipdb.set_trace()
        for l in p_list['mods']['itemlist']['data']['auctions']:
            i += 1
            # print(i)
            # if i == 36:
            # ipdb.set_trace()
            try:
                real_url = l['detail_url'].replace('\u003d',
                                                   '=').replace('\u0026', '&')
            except:
                continue
            if 'https' not in real_url:
                real_url = 'https:' + real_url
            # print("\tChecking item", i, "now...")
            # urlhead = requests.head(real_url, timeout=10)
            # if urlhead.status_code == 302 and urlhead.is_redirect is True:
            #     real_url = requests.get(real_url).url
            # print(real_url)
            title = BeautifulSoup(l['title'], "html.parser").text
            # print(title)
            if '//click.simba' in real_url:
                real_url = requests.get(real_url).url

            if '//item.taobao' in real_url:
                web = 'tb'
            elif '//detail.tmall' in real_url:  # and \
                # '天猫超市' not in l['nick'] and \
                # '天猫超市' not in title:
                web = 'tm'
            elif '//ju.taobao' in real_url:
                web = 'ju'
            elif '天猫超市' in l['nick'] or '天猫超市' in title:
                web = 'cs'
            else:
                try:
                    if 'tmall' in l['icon'][1]['url']:
                        web = 'tm'
                    else:
                        web = 'tb'
                except KeyError:
                    web = 'tb'
                except IndexError:
                    web = 'tb'
            # ipdb.set_trace()
            try:
                prod_list.append((title, l['nick'], real_url, web,
                                  l['view_price'], l['view_fee'],
                                  l['item_loc'], l['view_sales']))
            except:
                continue
    else:
        print("No Json data was found!")

    return prod_list


# To get a brief data
def getBrief(p_list):
    try:
        prod_no = p_list['mods']['pager']['data']['totalCount']
        print("There are total", prod_no, "products found.")
        pagesize = p_list['mods']['pager']['data']['pageSize']
        pagenum = p_list['mods']['pager']['data']['totalPage']
        # cur_page = p_list['mods']['pager']['data']['currentPage']
    except:
        # "pager":{"pageSize":44,"totalPage":1,"currentPage":1,"totalCount":23}
        prod_no = p_list['mods']['sortbar']['data']['pager']['totalCount']
        print("There are total", prod_no, "products found.")
        pagesize = p_list['mods']['sortbar']['data']['pager']['pageSize']
        pagenum = p_list['mods']['sortbar']['data']['pager']['totalPage']
        # cur_page = p_list['mods']['pager']['data']['currentPage']
    print("There are total", pagenum, "pages, and each page contains",
          pagesize, 'items')
    return prod_no, pagesize, pagenum


# Filter select
def selFilter(pf_list):
    filterkw = []
    filter_data = {}
    print("You have enabled filter function, there are:")
    pf_idx = 0
    for pf in pf_list:
        pf_idx += 1
        print(pf_idx, ".", pf['text'], end='')
        if pf['isMulti'] is True:
            print('[多选]')
        else:
            print()
        sub_pf_idx = 0
        for sub_pf in pf['sub']:
            sub_pf_idx += 1
            print("\t", str(sub_pf_idx) + ").", sub_pf['text'])
    pf_sel_idx = input("Please select a filter" +
                       "(1-1, 1-2,3, or ENTER to select all): ")
    sel_pa = re.compile('^\d+\-\d+[,?\d{1,3}]?.*$')
    while(not sel_pa.search(pf_sel_idx)):
        if pf_sel_idx != '':
            pf_sel_idx = input("Your input wrong format, please reselect: ")
        else:
            break

    if pf_sel_idx == '':
        None
    else:
        pf_sel = int(pf_sel_idx.split('-')[0])
        sub_pf_sel_list = [int(n) for n in pf_sel_idx.split('-')[1].split(',')]
        for sub_pf_sel in sub_pf_sel_list:
            while(pf_sel >= len(pf_list) + 1 or
                  sub_pf_sel >= len(pf_list[pf_sel - 1]['sub']) + 1):
                pf_sel_idx = input("You have input wrong index, " +
                                   "please reselect: ")
                pf_sel = int(pf_sel_idx.split('-')[0])
                sub_pf_sel = int(pf_sel_idx.split('-')[1])
            else:
                sub_pf_sel = pf_list[pf_sel - 1]['sub'][sub_pf_sel - 1]
                filterkw.append(sub_pf_sel['text'])
                if sub_pf_sel['key'] not in filter_data.keys():
                    filter_data[sub_pf_sel['key']] = sub_pf_sel['value']
                else:
                    filter_data[sub_pf_sel['key']] += ';' + sub_pf_sel['value']
    return filter_data, filterkw, pf_sel_idx


# To search a product and return a list of product's urls
def searchproduct(url, kw):
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

    temp_url = ''
    if options.searchurl != '':
        # res = urllib.request.urlopen(options.searchurl).read()
        temp_url = options.searchurl
    else:
        search_data = {}
        search_data['q'] = kw
        search_data['initiative_id'] = 'staobaoz_20120515'
        return_data = urllib.parse.urlencode(search_data, encoding='utf-8')
        print("Now trying to get data for: ", kw)
        # res = urllib.request.urlopen(url + return_data).read()
        temp_url = url + return_data

    pg_data = ''
    while len(pg_data) < 30000:
        pg_data = urllib.request.urlopen(temp_url).read().\
            decode('utf-8', 'ignore')
        print("The length of return data =", len(pg_data))

    list_pat = re.compile(r'g_page_config\s=\s({.*});\n')

    filter_kw = []
    if list_pat.search(pg_data):
        p_list = json.loads(list_pat.search(pg_data).group(1))
        (prod_no, pagesize, pagenum) = getBrief(p_list)

        # Now getting filters
        filter_data = {}
        pf_list = p_list['mods']['nav']['data']['common']
        if options.enfilter is True and len(pf_list) > 0:
            (filter_data, filterkw, pf_sel_idx) = selFilter(pf_list)
            filter_kw += filterkw
            while(pf_sel_idx != ''):
                print("You have selected a filter, now rescrape...")
                pfk = [k for k in filter_data.keys()][0]
                if pfk in search_data.keys():
                    search_data[pfk] += ';' + filter_data[pfk]
                else:
                    search_data.update(filter_data)
                return_data = urllib.parse.urlencode(search_data,
                                                     encoding='utf-8')
                print("Now trying to get data for: ", kw, end=',')
                for fw in filter_kw:
                    print(fw, end='|')
                print()
                res = urllib.request.urlopen(url + return_data)
                data = res.read().decode('utf-8', 'ignore')
                if list_pat.search(data):
                    p_list = json.loads(list_pat.search(data).group(1))
                    (prod_no, pagesize, pagenum) = getBrief(p_list)
                    try:
                        pf_list = p_list['mods']['nav']['data']['common']
                        (filter_data, filterkw,
                         pf_sel_idx) = selFilter(pf_list)
                        filter_kw += filterkw
                    except:
                        break

        # Now getting sort list
        sort_data = {}
        if options.ensort is True:
            sort_type = p_list['mods']['sortbar']['data']['sortList']
            price_sort = sort_type[4]['dropdownList']
            for ps in price_sort:
                ps['key'] = 'sort'
            sort_type = sort_type[:4] + price_sort
            print("There are several sort types as below")
            st_idx = 0
            for st in sort_type:
                st_idx += 1
                print(st_idx, ".", st['tip'])
            st_sel_idx = input("Please select one(Enter for default): ")
            if st_sel_idx == '':
                None
            elif int(st_sel_idx) <= st_idx:
                st_sel = sort_type[int(st_sel_idx) - 1]
                sort_data[st_sel['key']] = st_sel['value']
    else:
        print("No Json data was found, now exit.")
        sys.exit()

    if options.searchurl != '':
        res = urllib.request.urlopen(options.searchurl)
    elif len(sort_data) > 0:
        print("You have selected to sort, now rescrape...")
        search_data.update(sort_data)
        return_data = urllib.parse.urlencode(search_data, encoding='utf-8')
        res = urllib.request.urlopen(url + return_data)
        data = res.read().decode('utf-8', 'ignore')

        if list_pat.search(data):
            p_list = json.loads(list_pat.search(data).group(1))
            (prod_no, pagesize, pagenum) = getBrief(p_list)
        else:
            print("Data was not found, now exit.")
            sys.exit()

    qty = input("Please input a number to get(n or n-m): ")
    startno = 1
    if qty == '':
        qty = prod_no
        endno = prod_no
        target = pagenum
    elif '-' in qty:
        startno = int(qty.split('-')[0])
        endno = int(qty.split('-')[1])
        target = int(endno / pagesize) + 1
    else:
        endno = int(qty)
        target = int(int(qty) / pagesize) + 1
    print("You select", qty, "products to get data.")

    if options.ensort is True and len(sort_data) > 0:
        search_data.update(sort_data)
        return_data = urllib.parse.urlencode(search_data, encoding='utf-8')

    urls = []
    for i in range(1, target + 1):
        # ipdb.set_trace()
        html = ''
        if i == 1:
            if options.searchurl != '':
                prod_url = options.searchurl
            else:
                prod_url = url + return_data
            print("Now trying to get data for page No. ", i, "...")
            while len(html) < 30000:
                print("The length of return data =", len(html))
                res = urllib.request.urlopen(prod_url)
                html = res.read().decode('utf-8', 'ignore')
        else:
            if options.searchurl != '':
                prod_url = options.searchurl + '&s=' + str(pagesize * (i - 1))
            else:
                search_data['s'] = pagesize * (i - 1)
                return_data = urllib.parse.urlencode(search_data,
                                                     encoding='utf-8')
                prod_url = url + return_data
            print("Now trying to get data for page No. ", i, "...")
            while len(html) < 30000:
                print("The length of return data =", len(html))
                res = urllib.request.urlopen(prod_url)
                html = res.read().decode('utf-8', 'ignore')
        print("The length of return data =", len(html))
        urls += getprodurl(html)

    url_file = open('urls_' + kw, 'w', encoding='utf-8')
    url_file.write(str(urls))
    url_file.close()

    # try:
    return urls[startno - 1:endno], startno
    # except NameError:
    #     return urls[0:int(qty)]


# To get product detail by url
def getdetail(pu):
    # ipdb.set_trace()
    tm_prod_detail = {}
    tb_prod_detail = {}
    cs_prod_detail = {}
    ju_prod_detail = {}
    # ju_list = []
    error_list = []
    mydrv = webdriver.PhantomJS()
    tout = 100
    mydrv.set_page_load_timeout(tout)

    # print(pu[3], pu[0], pu[2], sep=',')
    try:
        starttime = datetime.datetime.now()
        to_flag = False
        try:
            mydrv.get(pu[2])
            prod_html = mydrv.page_source.encode('gbk', 'ignore').decode('gbk')
            # prod_html = urllib.request.urlopen(pu[2]).read().decode('gbk')
            soup = BeautifulSoup(prod_html, 'html.parser')
        except TimeoutException:
            print("This page is out of time(" + tout + "sec) to load.")
            to_flag = True

        if pu[3] == 'tb' and to_flag is False:
            ori_price = soup.find('div',
                                  attrs={'class': 'tb-property-cont'}).\
                text.replace('\n', '')
            if re.findall('div class="tb-promo-item-bd"', prod_html):
                prom_price = soup.find('div',
                                       attrs={'class':
                                              'tb-promo-item-bd'}).\
                    find('em', attrs={'id': 'J_PromoPriceNum'}).text
            else:
                prom_price = ori_price
            RateCounter = soup.find('strong',
                                    attrs={'id': 'J_RateCounter'}).text
            SellCounter = soup.find('strong',
                                    attrs={'id': 'J_SellCounter'}).text
            attr_list = soup.find('ul', attrs={'class': 'attributes-list'})
            attr_dict = {}
            try:
                for li in attr_list.find_all('li'):
                    attr_pat = re.compile(r'(.*):\s+(.*)')
                    if attr_pat.search(li.text):
                        attr_name = attr_pat.search(li.text).group(1)
                        attr_value = attr_pat.search(li.text).group(2)
                        attr_dict[attr_name] = attr_value
            except AttributeError:
                attr_dict['NA'] = 'NA'
            tb_prod_detail[pu] = [ori_price, prom_price,
                                  RateCounter, SellCounter,
                                  attr_dict]
            # f_tb.write(str(tb_prod_detail))
        elif pu[3] == 'tm' and to_flag is False:
            temp_price = []
            for p in soup.find_all('span', attrs={'class': 'tm-price'}):
                temp_price.append(p.text)
            if len(temp_price) == 1:
                ori_price = temp_price[0]
                prom_price = temp_price[0]
            elif len(temp_price) > 1:
                ori_price = temp_price[0]
                prom_price = temp_price[1]
            else:
                ori_price = ''
                prom_price = ''
            stats_data = []
            for span in soup.find_all('span', attrs={'class': 'tm-count'}):
                stats_data.append(span.text)
            if len(stats_data) > 1:
                MonthlySell = stats_data[0]
                RateCounter = stats_data[1]
            attr_list = soup.find('ul', attrs={'id': 'J_AttrUL'})
            attr_dict = {}
            for li in attr_list.find_all('li'):
                attr_pat = re.compile(r'(.*):\s+(.*)')
                if attr_pat.search(li.text):
                    attr_name = attr_pat.search(li.text).group(1)
                    attr_value = attr_pat.search(li.text).group(2).\
                        replace(u'\xa0', u' ')
                    attr_dict[attr_name] = attr_value
            tm_prod_detail[pu] = [ori_price, prom_price,
                                  RateCounter, MonthlySell,
                                  attr_dict]
            # f_tm.write(str(tm_prod_detail))
        elif pu[3] == 'cs' and to_flag is False:
            mydrv.quit()
            mydrv = webdriver.PhantomJS()
            try:
                redirectURL = requests.get(pu[2]).url
                # print("Hi2 - 1")
            except:
                redirectURL = pu[2]
                # print("Hi2 - 2")
            mydrv.get(redirectURL)
            prod_html = mydrv.page_source.encode('gbk', 'ignore').decode('gbk')
            soup = BeautifulSoup(prod_html, 'html.parser')
            pricelist = []
            for tp in soup.find_all('span', attrs={'class': 'tm-price'}):
                pricelist.append(tp.text)
            if len(pricelist) > 1:
                ori_price = pricelist[0]
                prom_price = pricelist[1]
            else:
                ori_price = pricelist[0]
                prom_price = pricelist[0]
            prodstats = []
            for tp in soup.find_all('span', attrs={'class': 'tm-count'}):
                prodstats.append(tp.text)
            if len(prodstats) > 1:
                MonthlySell = prodstats[0]
                RateCounter = prodstats[1]
            cs_prod_detail[pu] = [ori_price, prom_price,
                                  RateCounter, MonthlySell]
        elif pu[3] == 'ju' and to_flag is False:
            try:
                ori_price = soup.find('del',
                                      attrs={'class': 'originPrice'}).text
            except:
                ori_price = 'NA'
            try:
                prom_price = soup.find('div',
                                       attrs={'class': 'currentPrice'}).\
                    text.replace('\n', '')
            except:
                prom_price = 'NA'
            try:
                RateCounter = soup.find('li',
                                        attrs={'class': 'J_TabEval'}).\
                    find('strong').text
            except:
                RateCounter = 'NA'
            try:
                SellCounter = soup.find('li',
                                        attrs={'class': 'J_TabDeal'}).\
                    find('strong').text
            except:
                SellCounter = 'NA'
            ju_prod_detail[pu] = [ori_price, prom_price,
                                  RateCounter, SellCounter]

        # Get end time
        endtime = datetime.datetime.now()
        etime = (endtime - starttime).seconds
        print(" Elapsed time(sec): ", '[' + str(etime) + ']', "for: ", pu[0],
              ", from: ", pu[3])
    except:
        try:
            print("  [:(] Get data error for:", pu[0], "source:", pu[3],
                  ", skipped to next.")
        except:
            print(" Error for url: ", pu[2], ', skipped.')
        if requests.head(pu[2]).status_code == 302:
            redirectURL = requests.get(pu[2]).url
            error_list.append(pu[0] + '|' + pu[2] + '|' + redirectURL)
        else:
            error_list.append(pu[0] + '|' + pu[2])

    mydrv.quit()
    return tb_prod_detail, tm_prod_detail, cs_prod_detail, \
        ju_prod_detail, error_list


# To get product details by a list of product lists
def getproddetail(prod_urls):
    # i = 0
    # print("Now enable PhantomJS, please wait...")
    # mydrv = webdriver.PhantomJS()
    # ipdb.set_trace()
    tm_prod_detail = {}
    tb_prod_detail = {}
    cs_prod_detail = {}
    ju_prod_detail = {}
    error_list = []
    idx = 0
    # f_tb = open('tb_dict', 'a')
    # f_tm = open('tm_dict', 'a')
    np = int(options.process)
    myp = mp.Pool(np)
    results = myp.imap_unordered(getdetail, prod_urls)
    total = len(prod_urls)
    while(results._index != int(total)):
        if idx != results._index:
            print("\tThere are", '-' + str(int(total) - results._index) + '-',
                  "tasks to go...Please be patient")
        idx = results._index
    myp.close()
    for tb, tm, cs, ju, el in results:
        tb_prod_detail.update(tb)
        tm_prod_detail.update(tm)
        cs_prod_detail.update(cs)
        ju_prod_detail.update(ju)
        error_list += el
        # print(tb)

    # print("Hi")
    # f_tb.close()
    # f_tm.close()
    return tb_prod_detail, tm_prod_detail, cs_prod_detail, \
        ju_prod_detail, error_list
    # saveFile(data, '11')


def SaveList2File(urls, name):
    filename = options.output + sep + name + '_' + options.product + '.txt'
    filehd = open(filename, 'a', encoding='utf-8')
    for l in urls:
        print(l, file=filehd)
    print(' ', name, 'Lists have been save to file: ',
          filename, ', records: ', len(urls))


# Save data to a file
# tb -> product_name, price, RateCounter, SellCounter, attr_name, attr_value
def SaveTBData(tb_prod_detail):
    tb_csv_name = options.output + sep + 'tb_' + options.product + '.tab'
    tb_csv = open(tb_csv_name, 'a', encoding='utf-8')
    if 'Product_Name' not in open(tb_csv_name, encoding='utf-8').readline():
        print('Product_Name', 'Product_url',
              'Ori_Price', 'Prom_Price',
              'RateCounter', 'SellCounter',
              'attr_name', 'attr_value', sep='\t', file=tb_csv)
    for k in tb_prod_detail.keys():
        prop = tb_prod_detail[k][4]
        # ipdb.set_trace()
        if options.lessdata is True:
            prop = {k: prop[k] for k in prop.keys()
                    if k == '品牌' or k == '口味'}
        for pl in ['品牌', '口味']:
            if pl not in prop.keys():
                prop[pl] = "Others"
        for ak in sorted(prop.keys()):
            print(k[0], k[2],
                  tb_prod_detail[k][0],
                  tb_prod_detail[k][1],
                  tb_prod_detail[k][2],
                  tb_prod_detail[k][3],
                  ak,
                  prop[ak],
                  sep='\t', file=tb_csv)
    tb_csv.close()
    print(" All products from Taobao have been saved to file: ",
          tb_csv_name, ", Records: ", len(tb_prod_detail))


# tm -> product_name, price, RateCounter, MonthlySell, attr_name, attr_value
def SaveTMData(tm_prod_detail):
    tm_csv_name = options.output + sep + 'tm_' + options.product + '.tab'
    tm_csv = open(tm_csv_name, 'a', encoding='utf-8')
    if 'Product_Name' not in open(tm_csv_name, encoding='utf-8').readline():
        print('Product_Name', 'Product_Url',
              'OriPrice', 'Prom_Price',
              'RateCounter', 'MonthlySell',
              'attr_name', 'attr_value', sep='\t', file=tm_csv)
    for k in tm_prod_detail.keys():
        prop = tm_prod_detail[k][4]
        if options.lessdata is True:
            prop = {k: prop[k] for k in prop.keys()
                    if k == '品牌' or k == '口味'}
        for pl in ['品牌', '口味']:
            if pl not in prop.keys():
                prop[pl] = "Others"
        for ak in sorted(prop.keys()):
            print(k[0], k[2],
                  tm_prod_detail[k][0],
                  tm_prod_detail[k][1],
                  tm_prod_detail[k][2],
                  tm_prod_detail[k][3],
                  ak,
                  prop[ak],
                  sep='\t', file=tm_csv)
    tm_csv.close()
    print(" All products from Tmall have been saved to file: ",
          tm_csv_name, ", Records: ", len(tm_prod_detail))


# cs -> product_name, ori_price, prom_price, RateCounter, MonthlySell
def SaveCSData(cs_prod_detail):
    cs_csv_name = options.output + sep + 'cs_' + options.product + '.tab'
    cs_csv = open(cs_csv_name, 'a', encoding='utf-8')
    if 'Product_Name' not in open(cs_csv_name, encoding='utf-8').readline():
        print('Product_Name', 'Product_Url',
              'OriPrice', 'Prom_Price',
              'RateCounter', 'MonthlySell',
              'Attr_Name', 'Attr_Value',
              sep='\t', file=cs_csv)
    for k in cs_prod_detail.keys():
        print(k[0], k[2],
              cs_prod_detail[k][0],
              cs_prod_detail[k][1],
              cs_prod_detail[k][2],
              cs_prod_detail[k][3],
              '品牌', 'Others',
              sep='\t', file=cs_csv)
    cs_csv.close()
    print(" All products from Tmall Chaoshi have been saved to file: ",
          cs_csv_name, ", Records: ", len(cs_prod_detail))


# ju -> product_name, ori_price, prom_price, RateCounter, MonthlySell
def SaveJUData(ju_prod_detail):
    ju_csv_name = options.output + sep + 'ju_' + options.product + '.tab'
    ju_csv = open(ju_csv_name, 'a', encoding='utf-8')
    if 'Product_Name' not in open(ju_csv_name, encoding='utf-8').readline():
        print('Product_Name', 'Product_Url',
              'OriPrice', 'Prom_Price',
              'RateCounter', 'MonthlySell',
              'Attr_Name', 'Attr_Value',
              sep='\t', file=ju_csv)
    for k in ju_prod_detail.keys():
        print(k[0], k[2],
              ju_prod_detail[k][0],
              ju_prod_detail[k][1],
              ju_prod_detail[k][2],
              ju_prod_detail[k][3],
              '品牌', 'Others',
              sep='\t', file=ju_csv)
    ju_csv.close()
    print(" All products from Tmall Juhuasuan have been saved to file: ",
          ju_csv_name, ", Records: ", len(ju_prod_detail))


# Save Raw data
def SaveRaw(prod_urls):
    raw_file_name = options.output + sep + 'raw_' + options.product + '.tab'
    raw_file = open(raw_file_name, 'w', encoding='utf-8')
    print('Product_Name', 'Product_Url', 'Store_Name', 'Source', 'Price',
          'Fee', 'Location', 'Sell', sep='\t', file=raw_file)
    for pu in prod_urls:
        print(pu[0], pu[2], pu[1], pu[3],
              pu[4], pu[5], pu[6], pu[7],
              sep='\t', file=raw_file)
    raw_file.close()
    print("Raw data have been saved to file:", raw_file_name,
          ", Records:", len(prod_urls))


# Save data
def Save2File(prod_urls):
    (tb_prod_detail, tm_prod_detail, cs_prod_detail,
     ju_prod_detail, error_list) = getproddetail(prod_urls)

    try:
        SaveList2File(error_list, "Error")
    except:
        print('There is error to write problematic url lists to a file!')
    try:
        SaveTBData(tb_prod_detail)
    except:
        print('There is error to write tb products to a file!')
    try:
        SaveTMData(tm_prod_detail)
    except:
        print('There is error to write tm products to a file!')
    try:
        SaveCSData(cs_prod_detail)
    except:
        print('There is error to write cs products to a file!')
    try:
        SaveJUData(ju_prod_detail)
    except:
        print('There is error to write JU products to a file!')


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-o", "--output", default='.' + sep, dest="output",
                      help="Input an output path, default is script folder.")
    parser.add_option("-p", "--product", default='宜家同款', dest="product",
                      help="Input an output path, default is script folder.")
    parser.add_option("-n", "--quantity", default=100, dest="quantity",
                      help="Input a number to indicate how many products\
                      to split to get. like: -n 50")
    parser.add_option("-m", "--process", default=os.cpu_count(),
                      dest="process",
                      help="Input a number to indicate how many process\
                      to get. like: -m 4")
    parser.add_option("-f", "--enfilter", default=False, dest="enfilter",
                      action="store_true",
                      help="Use this options to enable filter.")
    parser.add_option("-s", "--ensort", default=False, dest="ensort",
                      action="store_true",
                      help="Use this options to enable sort.")
    parser.add_option("-l", "--lessdata", default=False, dest="lessdata",
                      action="store_true",
                      help="Use this options to enable sort.")
    parser.add_option("-r", "--rawdata", default=False, dest="rawdata",
                      action="store_true",
                      help="Use this options to extract raw data only.")
    parser.add_option("-u", "--url", default='', dest="searchurl",
                      help="Input a url to get data, url should be included\
                      by double quote.")
    (options, args) = parser.parse_args()

    if options.product == '':
        print("Wanring: You need to input at least one product name, Exiting.")
        sys.exit()
    if options.output != '.' + sep:
        makedirs(options.output, exist_ok=True)
    if options.searchurl != '' and options.product == '宜家同款':
        print("You have to input a product name by -p <product>, now exit.")
        sys.exit()
    # if options.enfilter is False or options.ensort is False:
    print("Filter enabled: ", options.enfilter)
    print("Sort enabled: ", options.ensort)
    print("Less data enabled: ", options.lessdata)

    starttime = timer()
    url = 'https://s.taobao.com/search?'
    # try:
    (prod_urls, startno) = searchproduct(url, options.product)
    # except ValueError:
    #     prod_urls = searchproduct(url, options.product)
    # total_list = prod_urls
    # i = 0
    # for pu in prod_urls:
    #     i += 1
    #     if pu[3] == 'ju':
    #         print(i, pu[3])
    # prod_urls = [
    #  ('wiwiwiwi',
    #   'hihihi',
    #   'https://chaoshi.detail.tmall.com/item.htm?&ns=1&abbucket=0&userBucket=12&id=21046163406',
    #   'cs'),
    # ]

    if options.rawdata is True:
        SaveRaw(prod_urls)
    else:
        n = int(options.quantity)
        if n > len(prod_urls):
            Save2File(prod_urls)
        else:
            iters = math.ceil(len(prod_urls) / n)
            for i in range(iters):
                if i == iters - 1:
                    try:
                        print("Now getting data for: ", i * n + startno,
                              "to", len(prod_urls) + startno - 1)
                    except:
                        print("Now getting data for: ", i * n + 1,
                              "to", len(prod_urls))
                else:
                    try:
                        print("Now getting data for: ", i * n + startno,
                              "to", (i + 1) * n + startno - 1)
                    except:
                        print("Now getting data for: ", i * n + 1,
                              "to", (i + 1) * n)
                # if i == iters - 1:
                #     split_urls = prod_urls[i * n:]
                # else:
                split_urls = prod_urls[i * n:(i + 1) * n]
                Save2File(split_urls)

    print("Elapsed time(sec): ", timer() - starttime)
