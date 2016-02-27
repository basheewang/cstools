#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: TieBa.py

# Time-stamp: <Coeus Wang: 2016-02-28 00:07:01>

import http.cookiejar
import urllib
from bs4 import BeautifulSoup
import ipdb
import pickle
import webbrowser
# import requests
import re
import sys
import urllib.request
from optparse import OptionParser
from os import listdir, sep
from os.path import isfile, realpath
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


# refresh tieba DB
def RefreshDB(url):
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
    tb_dict = {}
    i = 0
    j = 0
    for menu in sorted(all_cat.keys()):
        i += 1
        if i == 1:
            continue
        elif i > 2:
            break
        for smenu in all_cat[menu]:
            j += 1
            print('Now refresh:', menu, ' -> ', smenu, 'please wait...')
            # tb_dict.update(getTieBaList(menu, smenu))
            if not isfile('pkl' + sep + menu + '_' + smenu + '.pkl'):
                tb_dict = getTieBaList(menu, smenu)
                # ipdb.set_trace()
                save_obj(tb_dict, 'pkl' + sep + menu + '_' + smenu)
            # if j >= 2:
            #     break

    # save_obj(tb_dict, 'tiebaDB')
    print('DB refresh done!')


# Save an obj to a pickle file
def save_obj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
    print('Save obj to file:', name + '.pkl')


# load an obj from a pickle file
def load_obj(name):
    with open(name, 'rb') as f:
        return pickle.load(f)


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

    # ipdb.set_trace()
    if options.ignoreDB is False:
        all_tb = {}
        for pkl in [x for x in listdir('pkl') if '.pkl' in x]:
            all_tb.update(load_obj('pkl' + sep + pkl))
        work_tb = {k: v for k, v in all_tb.items() if options.tbname in k}
        if len(work_tb) == 0:
            print('Not found in DB, you may need to refresh DB.')
            sys.exit()
        GetTBDetails(work_tb)
    else:
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
    # ipdb.set_trace()
    try:
        totalpage = soup.find('div', attrs={'class': 'pagination'}).\
            find_all('a')[-1]['href'].split('&')[-1].split('=')[-1]
    except:
        totalpage = 1
    all_tb = {}
    for i in range(int(totalpage)):
        print('Now working on page:', i + 1, ': Total page:', totalpage)
        md['pn'] = i + 1
        temp_url = tbl_url + urllib.parse.urlencode(md, encoding='gbk')
        sub_html_data = getURLData(temp_url)
        # print(temp_url)
        sub_soup = BeautifulSoup(sub_html_data, 'html.parser')
        try:
            tblist = sub_soup.find('div', attrs={'class': 'sub_dir_box'}).\
                find('table').find_all('a', attrs={'target': '_blank'})
        except:
            print('Category not existed!')
            continue
        for tb in tblist:
            if len(tb.text) > 0:
                all_tb[tb.text] = tb['href']

    if options.refreshDB is True:
        return all_tb

    if options.tbname is not None:
        work_tb = {k: v for k, v in all_tb.items() if options.tbname in k}
    else:
        work_tb = all_tb
    GetTBDetails(work_tb)


def GetTBDetails(work_tb):
    n = 0
    tb_detail = {}

    for kw in sorted(work_tb.keys()):
        n += 1
        print(n, ".", "Now getting data for:", kw, work_tb[kw])
        tb_info = gettbDetail(work_tb[kw])
        # ipdb.set_trace()
        if tb_info is None:
            continue
        print(n, '.', kw, end='\t')
        for tbi in tb_info[:-2]:
            print(tbi, end='\t')
        print(work_tb[kw])
        if options.listsubject is True:
            m = 0
            for sj in tb_info[-1]:
                m += 1
                print('    ', '(' + str(m) + ')',
                      sj[0], sj[2], sj[3], sj[4], sj[1], sep='    ')
        if options.listsubject is True and options.readsubject is True:
            GetSubjectContent(tb_info)

        input("Press Enter to continue...")
        tb_detail[kw] = tb_info


# Get subject detail
def GetSubjectContent(tb_info, getnext='N'):
    # ipdb.set_trace()
    if re.match('y', getnext, re.IGNORECASE):
        sub_select = input("please select one: ")
    elif re.match('\d+', getnext):
        sub_select = getnext
    elif getnext == 'N':
        sub_select = input("please select one: ")

    if sub_select is None or sub_select == '':
        return

    s_subject = tb_info[-1][int(sub_select) - 1]
    print("You select subject index [", sub_select, "] ->", s_subject)
    sub_url = tb_info[-1][int(sub_select) - 1][1]
    html_data = getURLData(sub_url, 'utf-8')
    soup = BeautifulSoup(html_data, 'html.parser')
    totalpage = soup.find('li', attrs={'class': 'l_reply_num'}).\
        find_all('span')[-1].text.strip()
    name_list = []
    content_list = []
    for page in range(int(totalpage)):
        print("Now getting page:", page + 1, "Total page:", totalpage)
        html_data = getURLData(sub_url + '?pn=' + str(page + 1), 'utf-8')
        soup = BeautifulSoup(html_data, 'html.parser')

        name_list += soup.find('div', attrs={'class': 'p_postlist'}).\
            find_all('li', attrs={'class': 'd_name',
                                  'data-field': True})
        # content_list = soup.find('div', attrs={'class': 'p_postlist'}).\
        #     find_all('div', attrs={'class': 'd_post_content ' +
        #                            'j_d_post_content  clearfix'})
        # ipdb.set_trace()
        content_list += soup.find('div', attrs={'class': 'p_postlist'}).\
            find_all('div', attrs={'class': re.compile(r'j_d_post_content')})

    # To print to a pdf file
    if options.print2html is True:
        Print2HTML(name_list, content_list)
    else:
        Print2Console(name_list, content_list)

    getnext = input("Read another subject(Y/(N)/number):")
    # ipdb.set_trace()
    if re.match('y', getnext, re.IGNORECASE):
        GetSubjectContent(tb_info, getnext)
    elif re.match('\d+', getnext):
        GetSubjectContent(tb_info, getnext)
    # print('Hi')


# print simple content to console:
def Print2Console(name_list, content_list):
    for ci in range(len(name_list)):
        # ipdb.set_trace()
        if ci == 0:
            print('[LZ]', name_list[ci].text.strip(), ':',
                  content_list[ci].text)
        else:
            try:
                print('[' + str(ci + 1) + 'L]',
                      name_list[ci].text.strip(), ':',
                      content_list[ci].text.replace(u'\xa0', u' '))
            except:
                print("Undisplay character!")


# TO print subject to html file without any ad - TBC
def Print2HTML(name_list, content_list):
    temp_html = open('temp.html', 'w')
    print('<link rel="stylesheet" type="text/css"' +
          ' href="style.css" />',
          file=temp_html)
    print('<table>', file=temp_html)
    for si in range(len(name_list)):
        floor = ''
        if si == 0:
            floor = '[LZ]'
        else:
            floor = '[' + str(si + 1) + 'L]'
        print('<tr>', file=temp_html)
        print('<td>', floor, '</td>', file=temp_html)
        print('<td>', name_list[si].text.strip(), '</td>',
              file=temp_html)
        # if 'BDE_Image' in str(content_list[si]):
        #     gi = 0
        #     for img in content_list[si].\
        #             find_all('img', attrs={'class': 'BDE_Image'}):
        #         gi += 1
        #         # print(img['src'])
        #         img_name = str(si + 1) + '_' + str(gi) + '_' +\
        #             img['src'].split('/')[-1]
        #         urllib.request.urlretrieve(img['src'], img_name)
        try:
            print('<td>', content_list[si], '</td>', file=temp_html)
        except:
            print('<td>', 'unsupport character...', '</td>', file=temp_html)
        print('</tr>', file=temp_html)
    print('</table>', file=temp_html)
    temp_html.close()
    webbrowser.open('file:///' + realpath('temp.html'))
    # ipdb.set_trace()
    # print('Hi')


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
    if re.compile(r'本吧暂不开放').search(str(html_data)):
        print("Not a valid TieBa based on Legal.")
        return
    elif re.compile(r'name="keywords"').search(str(html_data)):
        return ParseSC2(html_data)
    else:
        return ParseSC1(html_data)


def ParseSC1(html_data):
    soup = BeautifulSoup(html_data, 'html.parser')
    # ipdb.set_trace()
    cont_html = soup.\
        find('code',
             attrs={'id': 'pagelet_html_frs-list/pagelet/thread_list'})
    body = BeautifulSoup(str(cont_html).
                         replace('<!--', '').replace('-->', ''),
                         'html.parser').\
        find('ul', attrs={'class': 'threadlist_bright j_threadlist_bright'})
    try:
        sub_list = body.find_all('li',
                                 attrs={'class': ' j_thread_list clearfix'})
    except:
        print('No subject for this tieba.')
        return
    subinfo_list = []
    # ipdb.set_trace()
    ii = 0
    for sj in sub_list:
        ii += 1
        # print(ii)
        # if ii == 10:
        #     ipdb.set_trace()
        try:
            subtitle_soup = sj.\
                find('div',
                     attrs={'class':
                            'threadlist_title pull_left j_th_tit '})
            subtitle = subtitle_soup.text.strip()
            subtitle_link = main_url + subtitle_soup.find('a')['href']
        except:
            subtitle_soup = sj.\
                find('div',
                     attrs={'class':
                            'threadlist_title pull_left j_th_tit' +
                            ' member_thread_title_frs '})
            subtitle = subtitle_soup.text.strip()
            subtitle_link = main_url + subtitle_soup.find('a')['href']

        reply_num = sj.\
            find('span',
                 attrs={'class': 'threadlist_rep_num center_text'}).text

        try:
            author = sj.\
                find('span', attrs={'class': 'tb_icon_author '}).text.strip()
        except:
            author = sj.\
                find('span', attrs={'class': 'tb_icon_author ' +
                                    'no_icon_author'}).text.strip()

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


def ParseSC2(html_data):
    soup = BeautifulSoup(html_data, 'html.parser')
    # ipdb.set_trace()
    sub_list = soup.find_all('li',
                             attrs={'class': 'j_thread_list clearfix'})
    subinfo_list = []
    # ipdb.set_trace()
    ii = 0
    for sj in sub_list:
        ii += 1
        # print(ii)
        # if ii == 36:
        #     ipdb.set_trace()
        try:
            subtitle_soup = sj.\
                find('div',
                     attrs={'class':
                            'threadlist_text ' +
                            'threadlist_title j_th_tit '})
            subtitle = subtitle_soup.text.strip()
            subtitle_link = main_url + subtitle_soup.find('a')['href']
        except:
            try:
                subtitle_soup = sj.\
                    find('div',
                         attrs={'class':
                                'threadlist_title pull_left j_th_tit' +
                                ' member_thread_title_frs '})
                subtitle = subtitle_soup.text.strip()
                subtitle_link = main_url + subtitle_soup.find('a')['href']
            except:
                subtitle_soup = sj.\
                    find('div',
                         attrs={'class':
                                'threadlist_text' +
                                ' threadlist_title' +
                                ' j_th_tit' +
                                ' member_thread_title_frs '})
                subtitle = subtitle_soup.text.strip()
                subtitle_link = main_url + subtitle_soup.find('a')['href']

        # ipdb.set_trace()
        reply_num = sj.\
            find('div',
                 attrs={'class': 'threadlist_rep_num'}).text

        try:
            createtime = sj.\
                find('span',
                     attrs={'class':
                            'tb_icon_author '}).find('span').text.strip()
        except:
            createtime = sj.\
                find('span',
                     attrs={'class':
                            'pull-right is_show_create_time'}).text.strip()

        try:
            author = sj.\
                find('span',
                     attrs={'class': 'tb_icon_author '}).\
                find('a').text.strip()
        except:
            try:
                author = sj.\
                    find('span',
                         attrs={'class': 'tb_icon_author '}).text.strip().\
                    replace(createtime, '')
            except:
                author = sj.\
                    find('span', attrs={'class': 'tb_icon_author ' +
                                        'no_icon_author'}).\
                    find('a').text.strip()

        try:
            lastreplytime = sj.\
                find('span',
                     attrs={'class':
                            'threadlist_reply_date j_reply_data'}).\
                text.strip()
        except:
            lastreplytime = ''

        sub_info = (subtitle, subtitle_link, reply_num,
                    author, createtime, lastreplytime)
        subinfo_list.append(sub_info)

    footer = soup.find('div', attrs={'class': 'th_footer_l'})
    subject = footer.find_all('span')[0].text
    post = footer.find_all('span')[1].text
    members = footer.find_all('span')[2].text
    member_link = main_url + footer.find('a')['href']
    tb_info = (subject, post, members, member_link, subinfo_list)
    # ipdb.set_trace()
    return tb_info


# Main program
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-n", "--tbname", default=None, dest="tbname",
                      help="Input a tieba name want to check: -n ABCD")
    parser.add_option("-p", "--print2html", default=False, dest="print2html",
                      action="store_true",
                      help="Print the subject to a pdf file.")
    parser.add_option("-l", "--listsubject", default=False, dest="listsubject",
                      action="store_true",
                      help="Use this options to get subject list(1 page).")
    parser.add_option("-r", "--readsubject", default=False, dest="readsubject",
                      action="store_true",
                      help="Use this options to read subject content(1 page).")
    parser.add_option("-R", "--refreshDB", default=False, dest="refreshDB",
                      action="store_true",
                      help="To refresh tieba DB(careful to use, long time!).")
    parser.add_option("-i", "--ignoreDB", default=False, dest="ignoreDB",
                      action="store_true",
                      help="Use this options to ignore DB file.")
    (options, args) = parser.parse_args()

    index_url = 'http://tieba.baidu.com/f/index/forumclass'
    main_url = 'http://tieba.baidu.com'
    if options.refreshDB is True:
        RefreshDB(index_url)
    else:
        if options.tbname is None:
            sys.exit()
        ParseTieBa(index_url)
