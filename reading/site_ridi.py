import os, sys, traceback, json, urllib.parse, requests, argparse, yaml, platform, time, threading, re, base64, fnmatch
import traceback
if platform.system() == 'Windows':
    sys.path += ["C:\SJVA3\lib2", "C:\SJVA3\data\custom", "C:\SJVA3_DEV"]
else:
    sys.path += ["/root/SJVA3/lib2", "/root/SJVA3/data/custom", '/root/SJVA3_DEV']

from support.base import get_logger, d, default_headers, SupportFile, SupportString
logger = get_logger()
from urllib.parse import quote
from lxml import etree
from collections import OrderedDict 
try:
    from bs4 import BeautifulSoup
except:
    try:
        os.system("pip install beautifulsoup4")
        from bs4 import BeautifulSoup
    except Exception as e: 
        logger.error(f"Exception:{str(e)}")
        logger.error(traceback.format_exc())

class SiteRidi(object):
    site_name = 'ridi'
    default_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79",
    "Referer": "https://ridibooks.com/",
    }

    @classmethod
    def search(cls, title):
        url = f'https://ridibooks.com/api/search-api/search?keyword={quote(title)}&adult_exclude=n&where%5B%5D=book&where%5B%5D=author&what=instant&site=ridi-store'
        response = requests.get(url, headers=cls.default_headers)
        ret = {}
        result_list = []
        if response.status_code == 200 :   
            res = response.json()
            for r in res['book']['books']:
                if r['series_prices_info'] != []:
                    entity = {}
                    entity['code'] = r['series_prices_info'][0]['series_id']
                    entity['title'] = r['web_title_title'].strip()
                    entity['author'] = ''
                    for author in r['authors_info']:
                        if author['role'] == 'original_author':
                            entity['author'] = author['name']
                    entity['publisher'] = r['publisher']
                    result_list.append(entity)
            ret['ret'] = 'success'
            ret['data'] = result_list
        else:
            logger.warning("검색 실패")
            ret['ret'] = 'empty'
        return ret
    
    @classmethod
    def info(cls, code):
        try:
            url = f'https://ridibooks.com/books/{code}'
            res = requests.get(url, headers=default_headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            date = soup.select('.info_reg_date')[0].text.strip()
            cover = "https:"+soup.select('.thumbnail')[0].get('data-original-cover')
            author_list = []
            author = soup.select('.js_author_detail_link')
            for author in author:
                author_list.append(author.text.strip())
            ret = {}
            ret['title'] =  soup.select('.info_title_wrap')[0].text.strip()
            try:
                ret['desc'] = soup.select('.introduce_paragraph > br')[0].text.strip()
            except:
                try:
                    ret['desc'] = soup.select('.introduce_paragraph')[0].text.strip()
                except Exception as exception:
                    logger.error('Exception:%s', exception)
                    logger.error(traceback.format_exc())
            ret['premiered'] = re.search('\d{4}\.\d{2}\.\d{2}\.', date).group().replace('.','').strip()
            ret['poster'] = cover
            genre_list = []
            for genre in soup.select('.info_category_wrap > a'):
                genre_list.append(genre.text.strip())
            ret['genre'] = list(set(genre_list))
            ret['author'] = str(author_list).replace('[','').replace(']','').replace("'",'').replace(', ',',')
            ret['publisher'] = soup.select('.publisher_detail_link')[-1].text.strip()
            ret['is_completed'] = soup.select('.metadata_item')[-1].text.strip()
            tags = []
            keyword = soup.select('.keyword_button')
            for keyword in keyword:
                tags.append(keyword.text.replace('#',''))
            #ret['tag'] = str(tags).replace('[','').replace(']','').replace("'",'').replace(', ',',')
            ret['tag'] = tags
            return ret
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
       
if __name__ == '__main__':
    data = SiteRidi.search('게임 속 낮져밤이가 되었다')
    logger.debug(d(data))
    data = SiteRidi.info(data[0]['code'])
    logger.debug(d(data))

