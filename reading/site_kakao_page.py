from email import header
import os, sys, traceback, json, urllib.parse, requests, argparse, yaml, platform, time, threading, re, base64, fnmatch
import traceback, unicodedata
from datetime import datetime
import urllib.request as py_urllib2
import urllib.parse as py_urllib #urlencode

from lxml import html, etree
import xmltodict

if platform.system() == 'Windows':
    sys.path += ["C:\SJVA3\lib2", "C:\SJVA3\data\custom", "C:\SJVA3_DEV"]
else:
    sys.path += ["/root/SJVA3/lib2", "/root/SJVA3/data/custom", '/root/SJVA3_DEV']

from support.base import get_logger, d, default_headers, SupportFile, SupportString
logger = get_logger()
from urllib.parse import quote
import lxml.html
from lxml import etree
import re
from collections import OrderedDict 



class SiteKakaoPage():

    headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
    }
    @classmethod
    def search(cls, title, auth=''):
        query = '''
            query SearchKeyword($input: String!) {
            searchKeyword(searchKeywordInput: { keyword: $input }) {
                id
                list {
                ...NormalListViewItem
                }
                total
                isEnd
                keyword
                sortOptionList {
                ...SortOption
                }
                selectedSortOption {
                ...SortOption
                }
                categoryOptionList {
                ...SortOption
                }
                selectedCategoryOption {
                ...SortOption
                }
                showOnlyComplete
                page
            }
            }

            fragment NormalListViewItem on NormalListViewItem {
            id
            type
            altText
            # ... 프래그먼트 내용은 동일하게 유지합니다.
            }

            fragment SortOption on SortOption {
            id
            name
            param
            }
            '''
        try:
            url = f'https://page.kakao.com/search/result?keyword={quote(title)}'
            cls.headers['Referer'] = url
            variables = {"input": title}
            data = {
                'query': query,
                'variables': variables
            }
            res = requests.post('https://page.kakao.com/graphql', json=data, headers=cls.headers)
            ret = []
            if res.status_code == 200:
                for data in res.json()['data']['searchKeyword']['list']:
                    entity = {}
                    entity['code'] = re.search('\d+',data['id']).group()
                    entity['title'] = re.search('작품,([^,]+)',data['altText']).group().replace('작품,','').strip()
                    entity['premiered'] = re.search('\d{4}\.\d{2}\.\d{2}', data['altText']).group().replace('.','').strip()
                    entity['author'] = re.search('작가\s([^,]+)',data['altText']).group().replace('작가 ','').strip()
                    entity['overall'] = data['altText']
                    ret.append(entity)
            else:
                return
            return ret
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @classmethod
    def info(cls, code):
        try:
            url = f"https://page.kakao.com/_next/data/2.12.2/ko/content/{code}.json?tab_type=about&seriesId={code}"
            res = requests.get(url, headers=cls.headers).json()
            ret = {}
            ret['title'] = res['pageProps']['metaInfo']['ogTitle']
            ret['desc'] = res['pageProps']['metaInfo']['description']
            ret['poster'] = 'https:' + res['pageProps']['metaInfo']['image']
            ret['author'] = res['pageProps']['metaInfo']['author']
            ret['publisher'] = res['pageProps']['dehydratedState']['queries'][0]['state']['data']['contentHomeAbout']['detail']['publisherName']
            url = f'https://page.kakao.com/content/{code}'
            response = requests.get(url, headers=cls.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            ret['is_completed'] = soup.find("meta", attrs={"property": "article:section"})['content'].replace('연재물', '연재')
            ret['tag'] = ['카카오페이지']
            ret['genre'] = res['pageProps']['dehydratedState']['queries'][0]['state']['data']['contentHomeAbout']['detail']['category'].split(' | ')
            return ret
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
       


if __name__ == '__main__':
    data = SiteKakaoPage.search('악녀를 죽여 줘')
    logger.debug(d(data))
    data = SiteKakaoPage.info(data[0]['code'])
    logger.debug(d(data))



