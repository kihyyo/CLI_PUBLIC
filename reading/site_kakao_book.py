import os, sys, traceback, json, urllib.parse, requests, argparse, yaml, platform, time, threading, re, base64, fnmatch
import traceback, unicodedata
from datetime import datetime
import urllib.request as py_urllib2
import urllib.parse as py_urllib #urlencode

from lxml import html, etree
import xmltodict

if platform.system() == 'Windows':
    sys.path += ["D:\SJVA3\lib2", "D:\SJVA3\data\custom", "C:\SJVA3_DEV"]
else:
    sys.path += ["/root/SJVA3/lib2", "/root/SJVA3/data/custom", '/root/SJVA3_DEV']

from support.base import get_logger, d, default_headers, SupportFile, SupportString
logger = get_logger()



class SiteKakaoBook(object):
    site_name = 'kakao'
    default_headers = {
        'Authorization: KakaoAK '
    } 



class SiteKakaoBook(SiteKakaoBook):
    api_key = ""
    
    @classmethod
    def search_api(cls, titl, auth, cont, isbn, publ):
        # logger.debug(f"책 검색 : [{titl}] [{auth}] ")
        kakao_api_key = cls.api_key
        try:
            if kakao_api_key is None: 
                print(kakao_api_key)
                return ""
            #url = "https://openapi.naver.com/v1/search/book.json?query=%s&display=100" % py_urllib.quote(str(keyword))
            # curl -X GET "https://dapi.kakao.com/v3/search/book?sort=accuracy&page=1&size=50&query=%EC%8B%9C%ED%81%AC%EB%A6%BF&target=title" -H "Authorization: KakaoAK 8ec2aec15928b5038db52d64c8f0dedf"
            url = f"https://dapi.kakao.com/v3/search/book?sort=accuracy&page=1&size=50"
            url += f"&query={py_urllib.quote(str(titl))}"
            
            requesturl = py_urllib2.Request(url)
            requesturl.add_header("Authorization","KakaoAK " + kakao_api_key[0])
            print(kakao_api_key)
            response = py_urllib2.urlopen(requesturl)
            data = response.read()
            data = json.loads(data)
            #logger.warning(data)
            rescode = response.getcode()
            if rescode == 200:
                # print(data)
                # exit(0)
                # print(type(data))
                return data
            else:
                print(rescode)
                # exit(0)
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @classmethod
    def search(cls, titl, auth, cont, isbn, publ):
        data = cls.search_api(titl, auth, cont, isbn, publ)
        #logger.warning(d(data))
        result_list = []
        ret = {}

        if data['meta']['total_count'] != '0':
            tmp = data['documents']
            for idx, item in enumerate(tmp):
                
                entity = {}
                entity['code'] = 'BK'+item["isbn"]
                entity['title'] = item['title']
                entity['image'] = item['thumbnail']
                entity['pubdate'] = item['datetime']
                entity['author'] = item['authors'][0]
                entity['publisher'] = item['publisher']
                entity['description'] = item['contents']
                entity['is_completed'] = '완결'
                #logger.warning(idx)
                result_list.append(entity)
        else:
            logger.warning("검색 실패")
        if result_list:
            ret['ret'] = 'success'
            ret['data'] = result_list
        else:
            ret['ret'] = 'empty'
        # print(type(ret))            
        return ret

    
    @classmethod
    def change_for_plex(cls, text):
        return text.replace('<p>', '').replace('</p>', '').replace('<br/>', '\n').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&apos;', '‘').replace('&quot;', '"').replace('&#13;', '').replace('<b>', '').replace('</b>', '')


    @classmethod 
    def get_tree(cls, url, proxy_url=None, headers=None, post_data=None, cookies=None, verify=None):
        text = cls.get_text(url, proxy_url=proxy_url, headers=headers, post_data=post_data, cookies=cookies, verify=verify)
        #logger.debug(text)
        if text is None:
            return
        return html.fromstring(text)
    
    @classmethod 
    def get_text(cls, url, proxy_url=None, headers=None, post_data=None, cookies=None, verify=None):
        res = cls.get_response(url, proxy_url=proxy_url, headers=headers, post_data=post_data, cookies=cookies, verify=verify)
        #logger.debug('url: %s, %s', res.status_code, url)
        #if res.status_code != 200:
        #    return None
        return res.text

    @classmethod 
    def get_response(cls, url, proxy_url=None, headers=None, post_data=None, cookies=None, verify=None):
        proxies = None
        if proxy_url is not None and proxy_url != '':
            proxies = {"http"  : proxy_url, "https" : proxy_url}
        if headers is None:
            headers = cls.default_headers

        if post_data is None:
            if verify == None:
                res = requests.get(url, headers=headers, proxies=proxies, cookies=cookies)
            else:
                res = requests.get(url, headers=headers, proxies=proxies, cookies=cookies, verify=verify)
        else:
            if verify == None:
                res = requests.post(url, headers=headers, proxies=proxies, data=post_data, cookies=cookies)
            else:
                res = requests.post(url, headers=headers, proxies=proxies, data=post_data, cookies=cookies, verify=verify)
        
        #logger.debug(res.headers)
        #logger.debug(res.text)
        return res

    @classmethod
    def info(cls, code):
        entity = {}
        
        return entity
