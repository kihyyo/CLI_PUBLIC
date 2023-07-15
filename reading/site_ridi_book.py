import os, sys, traceback, json, urllib.parse, requests, argparse, yaml, platform, time, threading, re, base64, fnmatch
from tkinter.messagebox import NO
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


class SiteRidiBooks():
    api_key = ""
    site_name = 'ridibook'
    default_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
    "Referer": "https://select.ridibooks.com/",
}
    @classmethod
    def search_api(cls, titl):
        # logger.debug(f"책 검색 : [{titl}] [{auth}] ")
        try:
            logger.debug(titl)
            # url = f"https://ridibooks.com/api/search-api/search?adult_exclude=n&keyword={py_urllib.quote(titl)}&site=ridi-select&what=base&start=0"
            # url = f"https://search-api.ridibooks.com/search?site=ridi-select&where=book&what=instant&keyword={py_urllib.quote(titl)}"
            url = f"https://ridibooks.com/api/search-api/search?adult_exclude=n&keyword={py_urllib.quote(titl)}=author&site=ridi-store"
            # https://select.ridibooks.com/search?q={py_urllib.quote(titl)}&type=Books
            # https://search-api.ridibooks.com/search?keyword=%EC%98%A4%EB%A7%8C%EA%B3%BC+%ED%8E%B8%EA%B2%AC+%EA%B7%B8%EB%A6%AC%EA%B3%A0+%EC%A2%80%EB%B9%84&where=book&site=ridi-select&what=base&start=0
            # https://search-api.ridibooks.com/search?site=ridi-select&where=book&what=instant&keyword=%EC%98%A4%EB%A7%8C%EA%B3%BC+%ED%8E%B8%EA%B2%AC+%EA%B7%B8%EB%A6%AC%EA%B3%A0+%EC%A2%80%EB%B9%84
            requesturl = py_urllib2.Request(url)
            response = py_urllib2.urlopen(requesturl)
            data = response.read()

            data = json.loads(data)
            # data = data['book']['books'] # ridi
            data = data['books'] # ridi-select
            rescode = response.getcode()
            if rescode == 200:
                return data
            else:
                print(rescode)
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @classmethod
    def search(cls, titl):
        data = cls.search_api(titl)
        #logger.warning(d(data))
        result_list = []
        ret = {}

        if len(data) != '0':
            tmp = data
            for idx, item in enumerate(tmp):
                
                entity = {}
                entity['code'] = "RD"+item["b_id"]
                entity['title'] = item['title']
                entity['author'] = item['author']
                entity['publisher'] = item['publisher']
                entity['description'] = "" #item['desc']
                # print(entity)
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
        return text.replace('<p>', '').replace('</p>', '').replace('<br/>', '\n').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&apos;', '‘').replace('&quot;', '"').replace('&#13;', '').replace('<b>', '').replace('</b>', '').strip()


    @classmethod 
    def get_tree(cls, url, proxy_url=None, headers=None, post_data=None, cookies=None, verify=None):
        text = cls.get_text(url, proxy_url=proxy_url, headers=headers, post_data=post_data, cookies=cookies, verify=verify)
        #logger.debug(text)
        if text is None:
            return "none"
        return html.fromstring(text)
    
    @classmethod 
    def get_text(cls, url, proxy_url=None, headers=None, post_data=None, cookies=None, verify=None):
        res = cls.get_response(url, proxy_url=proxy_url, headers=headers, post_data=post_data, cookies=cookies, verify=verify)
        logger.debug('url: %s, %s', res.status_code, url)
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
        # url = 'https://select-api.ridibooks.com/api/books/' + code[2:]
        url = 'https://ridibooks.com/books/' + code[2:]
        entity = {}
        cls.default_headers['cookie'] = 'ruid=42aa8968-ruid-4c03-b787-701cb514453a; PHPSESSID=f242f703-5ef5-45be-9b61-c5b78beb221e; ridi-al=1; ridi-rt=0e6714b1-82b6-4117-9b90-8adb7af88485; ch-veil-id=19d8a0aa-955d-4310-a25a-8bf33a809cbb; ridi-ffid=a5da8c31-fc68-4ca7-affb-046f98b50e90; pvid=48786289-pvid-4539-b170-fa407bca9be5; user_device_type=PC; _rdt_info=%7B%22_rdt_sid%22%3A%22author%22%2C%22_rdt_idx%22%3A%220%22%2C%22_rdt_loc%22%3A%22%5C%2Fbooks%5C%2F111007813%22%2C%22_rdt_ref%22%3A%22https%3A%5C%2F%5C%2Fridibooks.com%5C%2Fauthor%5C%2F25585%3F_s%3Dsearch%26_q%3D%25EC%2584%25B8%25EC%258A%25A4%2B%25EA%25B7%25B8%25EB%25A0%2588%25EC%259D%25B4%25EC%2597%2584%2B%25EC%258A%25A4%25EB%25AF%25B8%25EC%258A%25A4%22%7D; ridi-at=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IlJTMDAwIn0.eyJjbGllbnRfaWQiOiJlUGdiS0tSeVB2ZEFGelR2RmcyRHZyUzdHZW5mc3RIZGtRMnV2Rk5kIiwiZXhwIjoxNjY0MjY0NTc2LCJzY29wZSI6ImFsbCIsInN1YiI6ImsyaGVvbiIsInVfaWR4IjoxNzAyNDczLCJ1c2VyX3Rva2VuX3V1aWQiOiIwZTY3MTRiMS04MmI2LTQxMTctOWI5MC04YWRiN2FmODg0ODUiLCJpYXQiOjE2NjQyNjA5NzZ9.ROC80gY-7VRON2tI1bwiRoWojUu4q89QKGp0e41fqJvulYGbY1IXQ7dJ9kSTbtVEgzozo_4rLsjC8akxzbvr_i-mdSuaCtmcNk0hzkHZg_t02vXrP4DjgmwY-GmqGH614PqzmYmqmdpOKLDLgPhbprRv8JWWhRDdYFzfuLelKkGQ6ZkR3Ezw2gia6g5p_zyE6YgjvsCHS8viTxkggOtHNdQNDF5J3aNPwVXj_cSfO51yvGLVbKy0TKLeX05m66Dh3IcW_HhG2Dhqg_H7fJC8Jea_TECoFZeUqe0XolADiQoGCioLwCzbYbVP8RHkSIHVR8dp4MWP8wuyVQJZSn1REPBGBWOsP6D7vrEoRKZ22R3XLHiqLI8OjXzN4-NvCvnxqBguECljfO0dvWJdA8VrBLTo6QkR-AeYizSEBmzcW_49eDdoZGDvgfpcy3Y3JbSI0na-Cb3xZLg9rgdhoC-I-3DvOOh7ohJDqCsV2XmLKzcVOf9MPsjObU6FIlpLLfOHImh_Q8ruhr67XqfX4unwoh6r922hL20kkop3BnvxnIYYiMpmmlbifNhQFjWczRwR3PLLhaMbrQdxREUzaRSLkzKfQ9g163J1WDhq7gx4uXPIzUkckhOWOLT6hXrGonRdb6ZprS5gokDYubpTpcfPJnptnuJBKCfDCKTWksiDjME'
        cls.default_headers['Host'] = 'select-api.ridibooks.com'

        requesturl = py_urllib2.Request(url,headers=cls.default_headers)
        response = py_urllib2.urlopen(requesturl)
        data = response.read()
        data = json.loads(data)
        print(data)

        # root = cls.get_tree(url, headers=cls.default_headers)
        entity['code'] = code[2:]
        entity['title'] = data['title']['main']
        entity['poster'] = data['thumbnail']['large']
        for author in data['authors']: 
            entity['author'] = data['authors'][author][0]['name']
            break
            
        entity['publisher'] = data['publisher']['name']
        p_data=""
        if data['publishing_date']['ridibooks_publish_date'] is not None:
            p_date = data['publishing_date']['ridibooks_publish_date'][:10].replace("-","")
        elif data['publishing_date']['ebook_publish_date'] is not None: 
            p_date = data['publishing_date']['ebook_publish_date'][:10].replace("-","")
        elif data['publishing_date']['paper_book_publish_date'] is not None: 
            p_date = data['publishing_date']['paper_book_publish_date'][:10].replace("-","")    

        entity['premiered'] = p_date
        entity['desc'] = data['introduction']
        try:
            if len(data['categories'][0]) > 1:
                entity['genre'] = data['categories'][0][0]['name']+","+data['categories'][0][1]['name']
            elif len(data['categories'][1]) >1:
                entity['genre'] = data['categories'][1][0]['name']+","+data['categories'][1][1]['name']
        except:
            entity['genre'] = ""
        entity['tag'] = ['리디셀렉트']
        print(entity)
        return entity

if __name__ == '__main__':
    data = SiteRidiBooks.search('아시아가 바꿀 미래')
    logger.debug(d(data))
    data = SiteRidiBooks.info(data['data'][0]['code'])
    print(d(data))
