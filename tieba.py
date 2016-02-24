#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: TieBa.py

# Time-stamp: <Wang, Chen: 2016-02-24 17:30:44>

import http.cookiejar
import urllib
from bs4 import BeautifulSoup
import ipdb
# import requests
import re
# import sys
import urllib.request
from optparse import OptionParser
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
    # Add below manually.
    all_cat['网友俱乐部'] = ['个人贴吧', '网友俱乐部', '虚拟角色扮演',
                        '百度知道用户团队', '其他']
    # ipdb.set_trace()

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
    # tb_url = http://tieba.baidu.com/f/fdir?
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
    tb_detail = {}
    for kw in sorted(all_tb.keys()):
        n += 1
        print(n, ".", "Now getting data for:", kw, all_tb[kw])
        tb_info = gettbDetail(all_tb[kw])
        if tb_info is None:
            continue
        ipdb.set_trace()
        print(n, '.', kw, end='\t')
        for tbi in tb_info[:-2]:
            print(tbi, end='\t')
        print(all_tb[kw])
        if options.listsubject is True:
            m = 0
            for sj in tb_info[-1]:
                m += 1
                print('\t', m, sj[0], sj[2], sj[3], sj[4], sj[1], sep='\t')
        ipdb.set_trace()
        tb_detail[kw] = tb_info


# Get Tie Ba Detail
def gettbDetail(tb_url):
    '''
    Data need to be get:
    1. 主题数
    2. 帖子数
    3. 会员人数 = 关注人数
    4. 会员页面链接
    5. 主题内容：主题名称，主题链接，回复数量，主题作者，创建时间，最后回复时间
    '''
    html_data = getURLData(tb_url, 'utf-8')
    if re.compile('本吧暂不开放').search(str(html_data)):
        print("Not a valid TieBa based on Legal.")
        return

    soup = BeautifulSoup(html_data, 'html.parser')
    # ipdb.set_trace()
    cont_html = soup.\
        find('code',
             attrs={'id': 'pagelet_html_frs-list/pagelet/thread_list'})
    body = BeautifulSoup(str(cont_html).
                         replace('<!--', '').replace('-->', ''),
                         'html.parser').\
        find('ul', attrs={'class': 'threadlist_bright j_threadlist_bright'})
    sub_list = body.find_all('li',
                             attrs={'class': ' j_thread_list clearfix'})
    subinfo_list = []
    ipdb.set_trace()
    ii = 0
    for sj in sub_list:
        ii += 1
        print(ii)
        subtitle_soup = sj.\
            find('div',
                 attrs={'class':
                        'threadlist_title pull_left j_th_tit '})
        subtitle = subtitle_soup.text.strip()
        subtitle_link = main_url + subtitle_soup.find('a')['href']
        reply_num = sj.\
            find('span',
                 attrs={'class': 'threadlist_rep_num center_text'}).text
        author = sj.\
            find('span', attrs={'class': 'tb_icon_author '}).text.strip()
        createtime = sj.\
            find('span',
                 attrs={'class':
                        'pull-right is_show_create_time'}).text.strip()
        lastreplytime = sj.\
            find('span',
                 attrs={'class':
                        'threadlist_reply_date pull_right j_reply_data'}).\
            text.strip()
        sub_info = (subtitle, subtitle_link, reply_num,
                    author, createtime, lastreplytime)
        subinfo_list.append(sub_info)

    footer = BeautifulSoup(str(cont_html).
                           replace('<!--', '').replace('-->', ''),
                           'html.parser').find_all('div')[-1]
    subject = footer.find_all('span')[0].text
    post = footer.find_all('span')[1].text
    members = footer.find_all('span')[2].text
    member_link = main_url + footer.find('a')['href']
    tb_info = (subject, post, members, member_link, subinfo_list)
    return tb_info


# Main program
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-n", "--tbname", default=".", dest="tbname",
                      help="Input a tieba name want to check: -n ABCD")
    parser.add_option("-l", "--listsubject", default=True, dest="listsubject",
                      action="store_true",
                      help="Use this options to get subject list (1 page).")
    (options, args) = parser.parse_args()

    index_url = 'http://tieba.baidu.com/f/index/forumclass'
    main_url = 'http://tieba.baidu.com'
    ParseTieBa(index_url)
