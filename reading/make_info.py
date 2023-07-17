# from asyncio.windows_events import NULL
from enum import auto
import os, sys, traceback, json, urllib.parse, requests, argparse, yaml, platform, time, threading, re, base64, fnmatch
from datetime import datetime, timedelta
from urllib.parse import quote
from difflib import SequenceMatcher 
import shutil, copy
import zipfile


if platform.system() == 'Windows':
    sys.path += ["D:\SJVA3\lib2", "D:\SJVA3\data\custom", "D:\SJVA3_DEV"]
else:
    sys.path += ["/root/SJVA3/lib2", "/root/SJVA3/data/custom", '/root/SJVA3_DEV']
from support.base import get_logger, d, default_headers, SupportFile, SupportString
logger = get_logger()

from site_naver_book import SiteNaverBook
from site_naver_series import SiteNaverSeries
from site_kakao_page import SiteKakaoPage
from site_kakao_book import SiteKakaoBook
from site_ridi_book import SiteRidiBooks
from site_ridi import SiteRidi

C_END     = "\033[0m"
C_BOLD    = "\033[1m"
C_INVERSE = "\033[7m"
 
C_BLACK  = "\033[30m"
C_RED    = "\033[31m"
C_GREEN  = "\033[32m"
C_YELLOW = "\033[33m"
C_BLUE   = "\033[34m"
C_PURPLE = "\033[35m"
C_CYAN   = "\033[36m"
C_WHITE  = "\033[37m"
 
C_BGBLACK  = "\033[40m"
C_BGRED    = "\033[41m"
C_BGGREEN  = "\033[42m"
C_BGYELLOW = "\033[43m"
C_BGBLUE   = "\033[44m"
C_BGPURPLE = "\033[45m"
C_BGCYAN   = "\033[46m"
C_BGWHITE  = "\033[47m"


class MakeInfo:

    def __init__(self, main, config):
        self.main = config
        self.config = config



    def start(self):
        source = self.config['source']
        target = self.config['target']
        auto_flag = self.config['semi_auto']
        for folder in sorted(os.listdir(source)):
            # 
            # info.xml 이 존재하면 스킵
            # if os.path.isfile(os.path.join(source,folder,"info.xml")):
            #     continue
            # 
            # 
            try:
                pass_flag = False
                filepath = os.path.join(source, folder)
                is_folder = True
                if os.path.isdir(filepath):
                    logger.info(f"현재폴더 : {folder}")
                    child = sorted(os.listdir(os.path.join(source, folder)))
                    if pass_flag:
                        continue
                elif os.path.splitext(filepath)[-1].lower() == '.epub':
                    logger.info(f"현재파일 : {folder}")
                    is_folder = False
                else:
                    continue

                org_title = folder
                search_name = folder

                if is_folder == False:
                    search_name = os.path.splitext(folder)[0]

                data,title_auth = self.input_title(search_name)
                
                if data is None:
                    continue

                print(title_auth)
                tmp = title_auth.split('|')
                if len(tmp) == 1:
                    title = tmp[0]
                    author = ''
                else:
                    title = tmp[0]
                    author = tmp[1]


                while True:
                    match_item = []
                    cnt=0
                    s_idx = -1
                    temp = []
                    for item in data:
                        d_temp = item
                        if org_title in d_temp['title'] :
                            temp.append(item)

                    if len(temp)>0:
                        data = temp

                    if auto_flag > 0:
                        for idx, item in enumerate(data):
                            # logger.debug(d(item))
                            # logger.info(f"[{idx}] {item['title']} / {item['author']}")

                            # if title in item['title'] and author[:3] in item['author']: # normal
                            try:
                                search_detail = f"[{idx}] "+ C_YELLOW + f"{item['title']} /" +C_GREEN + f" {item['author']} / {item['publisher']}"+C_END
                            except:
                                search_detail = f"[{idx}] "+ C_YELLOW + f"{item['title']} /" +C_GREEN + f" {item['author']}"+C_END
                            if title == item['title'] and author == item['author']: # for ridi

                                cnt+=1
                                print(search_detail)
                                s_idx = idx
                        if cnt == 0:
                            for idx, item in enumerate(data):
                                if author[:4] in item['author']:
                                    cnt+=1
                                    print(search_detail)
                                    s_idx = idx

                                
                    if cnt == 0:
                        for idx, item in enumerate(data):
                            try:
                                print(f"[{idx}] "+ C_YELLOW + f"{item['title']} /" +C_GREEN + f" {item['author']}/ {item['publisher']}"+C_END)
                            except:
                                print(f"[{idx}] "+ C_YELLOW + f"{item['title']} /" +C_GREEN + f" {item['author']}"+C_END)

                    if cnt==1:
                        index = str(s_idx)
                    else:
                        index = input("책 선택 (00:책 입력 ): ")

                    if index == '':
                        pass_flag = True
                        break
                    elif index == '00':
                        search_name = folder
                        if is_folder == False:
                            search_name = os.path.splitext(folder)[0]
                        data = self.input_title(search_name, is_first=False)
                        if data == None:
                            pass_flag = True
                            break
                        continue
                    try:
                        index = int(index)
                    except:
                        logger.error("다시 입력")
                        continue
                    
                    if data[index]['code'] != 'manual':
                        try:
                            select_item = data[index]
                            info = self.info(data[index]['code'], select_item)
                        except:
                            info = None
                    else:
                        info = data[0]

                    if info == None:
                        logger.error("info 에러")
                        continue
                    logger.debug(d(info))    
                        
                    if auto_flag < 2:
                        ans = input("처리 여부 (00:책선택) : ")
                        if ans == '00':
                            continue
                        if ans.lower() not in ['y', 'ㅛ', '0']:
                            pass_flag = True
                            break
                        break
                    else:
                        break
                        pass_flag = False

                if pass_flag:
                    continue
                
                # 폴더명 변경
                #title = info['title'].replace('. 1', '').strip()
                title = re.sub('\.\s\d+$', '', info['title']).strip()
                title = re.sub("\(양장본.|Hardcover\)","",title)
                if '개정판 ｜ ' in title:
                    title = title.replace('개정판 ｜ ','')+"(개정판)"
                # try:
                #     if int(title[-1:])>1:
                #         title = title[:-1].strip()
                # except:
                #     title = title
                # print(title)
                if target != None and target != '':
                    target_foldername = f"{title} [{info['author'].split(',')[0].strip()}]"
                    target_foldername = SupportFile.text_for_filename(target_foldername)
                    targetpath = os.path.join(target, target_foldername)
                    if self.config['use_cate']:
                        targetpath = os.path.join(target, SupportString.get_cate_char_by_first(target_foldername),  target_foldername)
                    else:
                        targetpath = os.path.join(target, target_foldername)

                    if is_folder:
                        if os.path.exists(targetpath):
                            logger.error("이미 폴더 있음")
                            continue
                        shutil.move(filepath, targetpath)
                    else:
                        os.makedirs(targetpath)
                        shutil.move(filepath, targetpath)
                else:
                    targetpath = filepath

                # 폴더안에 []로 작가 이름이 있으면 지움
                """
                for filename in os.listdir(targetpath):
                    #tmp = filename.replace(f"[{info['author']}]", '').strip()
                    tmp = re.sub("\[.*?\]", '', filename).strip()
                    #tmp = tmp.replace(' (소설)', '').strip()
                    tmp = re.sub("\s+\(.*?\)", '', tmp).strip()
                    if filename != tmp:
                        os.rename(os.path.join(targetpath, filename), os.path.join(targetpath, tmp))
                """
                coverfilepath = os.path.join(targetpath, '[Cover].jpg')
                if os.path.exists(coverfilepath):
                    os.remove(coverfilepath)


                # cover.jpg
                if self.config['cover']:
                    coverfilepath = os.path.join(targetpath, 'cover.jpg')
                    if os.path.exists(coverfilepath) == False:
                        ret = SupportFile.download(info['poster'], coverfilepath)
                        if ret == False:
                            logger.error("이미지 파일 없음")
                tmp = XML.format(
                    title = change(title),
                    desc = change(info['desc']),
                    author = change(info['author']),
                    publisher = change(info['publisher']),
                    year = info['premiered'][0:4],
                    is_completed = info['is_completed'],
                    month = info['premiered'][4:6] if len(info['premiered']) > 4 else '01',
                    day = info['premiered'][6:8] if len(info['premiered']) > 6 else '01',
                    tags = ','.join(info['tag']) if 'tag' in info  else '',
                    inker = '',
                    genre = ','.join(info['genre']) if 'genre' in info  else '',
                )
                SupportFile.write_file(os.path.join(targetpath, 'info.xml'), tmp)
                continue
            except Exception as exception:
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())


    def input_title(self, folder, is_first=True):
        while True:
            if is_first:
                search_name = '0'
                is_first = False
            else:
                search_name = input("책 제목 입력 (m:NO META 이동 i:수동입력): ")

            if search_name == '':
                return
            if search_name in ['.', '0']:
                search_name = folder
                search_name = search_name.replace('@ 完', '').replace('㉿ 完', '').strip()
                #search_name = search_name.replace('(소설)', '').strip()
                search_name = re.sub("\(.*?\)", '', search_name).strip()
        
                match = re.search('\[(?P<author>.*?)\]', search_name)
                if match:
                    search_name = re.sub("\[.*?\]", '', search_name).strip()
                    search_name += f"|{match.group('author')}"
            if search_name.lower() in ['m', 'ㅡ']:
                target = os.path.join(self.config['no_meta_target'])
                logger.warning("노 메타 폴더 이동 : ")
                shutil.move(os.path.join(self.config['source'], folder), target)
                return
            if search_name.lower() in ['ㅑ', 'i']:
                # info = {'title':'','author':'','publisher':'','desc':'','premiered':'','poster':''}
                info = {}
                info['title']  = input("책 제목 입력: ")
                info['author'] = input("책 저자 입력: ")
                info['publisher'] = input("출판사 입력: ")
                print("개요 입력(xxx : 종료)")
                tmp = ""
                while True:
                    b = sys.stdin.readline().strip()
                    if b == "xxx" or b == "ㅌㅌㅌ":
                        break
                    tmp += b
                info['desc'] = tmp
                info['premiered'] = input("출판일 [YYYYMMDD] 입력: ")
                info['poster'] = input("포스터 URL: ")
                data = []
                data.append(info)
                return data,info['title']+'|'+info['author']
                
            data = self.search(search_name)

            if data == None or len(data) == 0:
                logger.error("책 없음")
                continue

            return data , search_name


    def search(self, param):
        tmp = param.split('|')
        if len(tmp) == 1:
            title = tmp[0]
            author = ''
        else:
            title = tmp[0]
            author = tmp[1]

        if self.config['meta_source'] == 'naverbook':
            data = SiteNaverBook.search(title, author, '', '', '')
            if data['ret'] != 'success':
                return
            return data['data']

        elif self.config['meta_source'] == 'naverseries':
            data = SiteNaverSeries.search(title, author)
            logger.debug(data)
            return data
        elif self.config['meta_source'] == 'kakaopage':
            data = SiteKakaoPage.search(title, author)
            return data
        elif self.config['meta_source'] == 'kakaobook':
            data = SiteKakaoBook.search(title,author,'','','')
            if data['ret'] != 'success':
                return
            return data['data']
        elif self.config['meta_source'] == 'ridibook':
            data = SiteRidiBooks.search(title)
            if data['ret'] != 'success':
                return
            return data['data']
        elif self.config['meta_source'] == 'ridi':
            data = SiteRidi.search(title)
            logger.debug(data)
            if data['ret'] != 'success':
                return
            return data['data']

    def info(self, code, select_item=None):
        if self.config['meta_source'] == 'naverbook':
            try:
                info = SiteNaverBook.info(code)
            except:
                info = None
            
            if info == None:
                logger.error("책 정보 가져올수 없음")
                logger.debug(d(select_item))
                try:
                    info = {}
                    info['title'] = re.sub('\s\d+$', '', select_item['title']).strip()
                    info['poster'] = select_item['image'].split('?')[0]
                    info['desc'] = select_item['description']
                    info['publisher'] = select_item['publisher']
                    #info['premiered'] = select_item['image'].split('date=')[1]
                    info['premiered'] = select_item['pubdate']
                    info['author'] = select_item['author']
                    info['genre'] = ""
                    logger.debug(info)
                except Exception as exception:
                    logger.error('Exception:%s', exception)
                    logger.error(traceback.format_exc())
            return info

        elif self.config['meta_source'] == 'naverseries':
            data = SiteNaverSeries.info(code)
            return data
        elif self.config['meta_source'] == 'kakaopage':
            data = SiteKakaoPage.info(code)
            data['premiered'] = select_item['premiered']
            return data
        elif self.config['meta_source'] == 'kakaobook':
            info = {}
            info['title'] = select_item['title']
            info['poster'] = select_item['image']
            info['desc'] = select_item['description']
            info['publisher'] = select_item['publisher']
            tmp = select_item['pubdate'][:10]
            info['premiered'] = tmp.replace("-","")
            info['author'] = select_item['author']
            
            data = info
            return data
        elif self.config['meta_source'] == 'ridibook':
            try:
                info = SiteRidiBooks.info(code)
                logger.debug(info)
            except:
                info = None
            
            if info == None:
                logger.error("책 정보 가져올수 없음")
                logger.debug(d(select_item))
                try:
                    info = {}
                    info['title'] = re.sub('\s\d+$', '', select_item['title']).strip()
                    info['poster'] = select_item['image']
                    info['desc'] = select_item['description']
                    info['publisher'] = select_item['publisher']
                    info['premiered'] = select_item['pubdate']
                    info['author'] = select_item['author']
                    info['genre'] = select_item['genre']
                    logger.debug(info)
                except Exception as exception:
                    logger.error('Exception:%s', exception)
                    logger.error(traceback.format_exc())
            return info

        elif self.config['meta_source'] == 'ridi':
            try:
                info = SiteRidi.info(code)
                logger.debug(info)
            except:
                info = None
            
            if info == None:
                logger.error("책 정보 가져올수 없음")
                logger.debug(d(select_item))
                try:
                    info = {}
                    info['title'] = re.sub('\s\d+$', '', select_item['title']).strip()
                    info['poster'] = select_item['image']
                    info['desc'] = select_item['description']
                    info['publisher'] = select_item['publisher']
                    #info['premiered'] = select_item['image'].split('date=')[1]
                    info['premiered'] = select_item['pubdate']
                    info['author'] = select_item['author']
                    info['genre'] = select_item['genre']
                    logger.debug(info)
                except Exception as exception:
                    logger.error('Exception:%s', exception)
                    logger.error(traceback.format_exc())
            return info




XML = '''<?xml version="1.0"?>
<ComicInfo xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Title>{title}</Title>
  <Series>{title}</Series>
  <Summary>{desc}</Summary>
  <Writer>{author}</Writer>
  <Publisher>{publisher}</Publisher>
  <Genre>{genre}</Genre>
  <Tags>{tags}</Tags>
  <LanguageISO>ko</LanguageISO>
  <Notes>{is_completed}</Notes>
  <CoverArtist></CoverArtist>
  <Penciller></Penciller>
  <Inker>{inker}</Inker>
  <Colorist></Colorist>
  <Letterer></Letterer>
  <CoverArtist></CoverArtist>
  <Editor></Editor>
  <Characters></Characters>
  <Year>{year}</Year>
  <Month>{month}</Month>
  <Day>{day}</Day>
</ComicInfo>'''


def change(str):
    return str.replace('<', '"').replace('>', '"').replace('&', '&amp;').strip()
                    
                
