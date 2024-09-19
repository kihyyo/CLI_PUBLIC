from email import header
import os, sys, traceback, json, urllib.parse, requests, argparse, yaml, platform, time, threading, re, base64, fnmatch

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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
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
                    entity['premiered'] = re.search('\d{2}\.\d{2}\.\d{2}', data['altText']).group().replace('.','').strip()
                    entity['author'] = re.search('작가\s([^,]+)',data['altText']).group().replace('작가 ','').strip()
                    entity['thumbnail']= data['thumbnail']
                    entity['overall'] = data['altText']
                    ret.append(entity)
            else:
                return
            return ret
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @classmethod
    def info(cls, code, select_item):
        encoded_string = urllib.parse.quote(select_item['title'])
        cls.headers['Referer'] = f"https://page.kakao.com/search/result?keyword={encoded_string}"
        try:
            url = f"https://page.kakao.com/graphql"
            data = {
            "query": "\n    query contentHomeInfo($seriesId: Long!) {\n  contentHomeInfo(seriesId: $seriesId) {\n    about {\n      id\n      themeKeywordList {\n        uid\n        title\n        scheme\n      }\n      description\n      screenshotList\n      authorList {\n        id\n        name\n        role\n        roleDisplayName\n      }\n      detail {\n        id\n        publisherName\n        retailPrice\n        ageGrade\n        category\n        rank\n      }\n      guideTitle\n      characterList {\n        thumbnail\n        name\n        description\n      }\n      detailInfoList {\n        title\n        info\n      }\n    }\n    recommend {\n      id\n      seriesId\n      list {\n        ...ContentRecommendGroup\n      }\n    }\n  }\n}\n    \n    fragment ContentRecommendGroup on ContentRecommendGroup {\n  id\n  impLabel\n  type\n  title\n  description\n  items {\n    id\n    type\n    ...PosterViewItem\n  }\n}\n    \n\n    fragment PosterViewItem on PosterViewItem {\n  id\n  type\n  showPlayerIcon\n  scheme\n  title\n  altText\n  thumbnail\n  badgeList\n  ageGradeBadge\n  statusBadge\n  subtitleList\n  rank\n  rankVariation\n  ageGrade\n  selfCensorship\n  eventLog {\n    ...EventLogFragment\n  }\n  seriesId\n}\n    \n\n    fragment EventLogFragment on EventLog {\n  fromGraphql\n  click {\n    layer1\n    layer2\n    setnum\n    ordnum\n    copy\n    imp_id\n    imp_provider\n  }\n  eventMeta {\n    id\n    name\n    subcategory\n    category\n    series\n    provider\n    series_id\n    type\n  }\n  viewimp_contents {\n    type\n    name\n    id\n    imp_area_ordnum\n    imp_id\n    imp_provider\n    imp_type\n    layer1\n    layer2\n  }\n  customProps {\n    landing_path\n    view_type\n    helix_id\n    helix_yn\n    helix_seed\n    content_cnt\n    event_series_id\n    event_ticket_type\n    play_url\n    banner_uid\n  }\n}\n    ",
            "variables": {
                "seriesId": code
            }
            }
            res = requests.post(url, json=data, headers=cls.headers).json()
            ret = {}
            ret['title'] = select_item['title']
            ret['desc'] = res['data']['contentHomeInfo']['about']['description']
            ret['poster'] = 'https:' + select_item['thumbnail']
            ret['author'] = res['data']['contentHomeInfo']['about']['authorList'][0]['name']
            ret['publisher'] = res['data']['contentHomeInfo']['about']['detail']['publisherName']
            ret['is_completed'] = '연재' if '연재중' in select_item['overall'] else '완결'
            ret['tag'] = ['카카오페이지']
            ret['genre'] = res['data']['contentHomeInfo']['about']['detail']['category'].split(' | ')
            ret['premiered'] = '20' + select_item['premiered'] if len(select_item['premiered']) == 6 else select_item['premiered']
            themeKeywordList = res['data']['contentHomeInfo']['about']['themeKeywordList']
            tags = []
            for theme in themeKeywordList:
                title = theme['title']
                if title not in tags:  # 중복 태그 방지
                    tags.append(title)
            ret['tag'] = tags
            return ret
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
       


if __name__ == '__main__':
    data = SiteKakaoPage.search('악녀를 죽여 줘')
    logger.debug(d(data))
    data = SiteKakaoPage.info(data[0]['code'])
    logger.debug(d(data))



