import os, sys, traceback, json, urllib.parse, requests, argparse, yaml, platform, time, threading, re, base64, fnmatch
from datetime import datetime, timedelta
from urllib.parse import quote
from difflib import SequenceMatcher 
import shutil, copy
import zipfile
from site_kakao_book import SiteKakaoBook

if platform.system() == 'Windows':
    sys.path += ["D:\SJVA3\lib2", "D:\SJVA3\data\custom", "D:\SJVA3_DEV"]
else:
    sys.path += ["/root/SJVA3/lib2", "/root/SJVA3/data/custom", '/root/SJVA3_DEV']
from support.base import get_logger, d, default_headers, SupportFile, SupportString
logger = get_logger()

from site_naver_book import SiteNaverBook


class ReadingProcess:

    def __init__(self, config):
        self.config = config


    def make_xml(self):
        
        def input_title(folder, is_first=True):
            while True:
                if is_first:
                    search_name = '0'
                    is_first = False
                else:
                    search_name = input("책 제목 입력 (m:NO META 이동): ")
                if search_name == '':
                    return
                if search_name in ['.', '0']:
                    search_name = folder
                    search_name = search_name.replace('@ 完', '').replace('㉿ 完', '').strip()
                    #search_name = search_name.replace('(소설)', '').strip()
                    search_name = re.sub("\(.*?\)", '', search_name).strip()
                    if is_folder == False:
                        search_name = os.path.splitext(search_name)[0]
                    match = re.search('\[(?P<author>.*?)\]', search_name)
                    if match:
                        search_name = re.sub("\[.*?\]", '', search_name).strip()
                        search_name += f"|{match.group('author')}"
                if search_name.lower() in ['m', 'ㅡ']:
                    target = os.path.join(self.config['no_meta_target'])
                    logger.warning("노 메타 폴더 이동 : ")
                    shutil.move(os.path.join(self.config['source'], folder), target)
                    return

                tmp = search_name.split('|')
                if len(tmp) == 1:
                    data = SiteNaverBook.search(search_name, '', '', '', '')
                else:
                    data = SiteNaverBook.search(tmp[0], tmp[1], '', '', '')
            
                if data['ret'] != 'success':
                    logger.error("책 없음")
                    continue
                return data

        source = self.config['source']
        target = self.config['target']
        for folder in os.listdir(source):
            try:
                pass_flag = False
                filepath = os.path.join(source, folder)
                is_folder = True
                if os.path.isdir(filepath):
                    logger.info(f"현재폴더 : {folder}")
                    child = os.listdir(os.path.join(source, folder))
                    """
                    for c in child:
                        if c.lower().endswith('.txt'):
                            logger.error("텍스트 포함")
                            #shutil.move(filepath, self.config["텍스트 이동"])
                            pass_flag = True
                            break
                    else:
                        logger.debug(d(child))
                    """
                    if pass_flag:
                        continue
                elif os.path.splitext(filepath)[-1].lower() == '.epub':
                    logger.info(f"현재파일 : {folder}")
                    is_folder = False
                
                if self.append_page_count(filepath) == False:
                    logger.error("변환 에러")
                    continue

                

                data = input_title(folder)
                if data == None:
                    continue

                while True:
                    
                    for idx, item in enumerate(data['data']):
                        #logger.debug(d(item))
                        logger.warning(f"[{idx}] {item['title']} / {item['author']}")

                    index = input("책 선택 (00:책 입력): ")
                    if index == '':
                        pass_flag = True
                        break
                    elif index == '00':
                        data = input_title(folder, is_first=False)
                        if data == None:
                            pass_flag = True
                            break
                        continue
                    try:
                        index = int(index)
                    except:
                        logger.error("다시 입력")
                        continue

                    try:
                        select_item = data['data'][index]
                        info = SiteNaverBook.info(data['data'][index]['code'])
                    except:
                        info = None
                    
                    
                    if info == None:
                        logger.error("책 정보 가져올수 없음")
                        info = {}
                        info['title'] = re.sub('\s\d+$', '', select_item['title']).strip()
                        info['poster'] = select_item['image'].split('?')[0]
                        info['desc'] = select_item['description']
                        info['publisher'] = select_item['publisher']
                        info['premiered'] = select_item['image'].split('date=')[1]
                        info['author'] = select_item['author']


                    logger.debug(d(info))    
                        

                    ans = input("처리 여부 (00:책선택) : ")
                    if ans == '00':
                        continue
                    if ans.lower() not in ['y', 'ㅛ', '0']:
                        pass_flag = True
                        break
                    break
                
                if pass_flag:
                    continue
                
                # 폴더명 변경
                title = info['title'].replace('. 1', '').strip()
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
                
                # makexml
                xml = '''<?xml version="1.0"?>
<ComicInfo xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Title>{title}</Title>
  <Series>{title}</Series>
  <Summary>{desc}</Summary>
  <Writer>{author}</Writer>
  <Publisher>{publisher}</Publisher>
  <Genre></Genre>
  <Tags></Tags>
  <LanguageISO>ko</LanguageISO>
  <Notes>완결</Notes>
  <CoverArtist></CoverArtist>
  <Penciller></Penciller>
  <Inker></Inker>
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
                    
                tmp = xml.format(
                    title = change(title),
                    desc = change(info['desc']),
                    author = change(info['author']),
                    publisher = change(info['publisher']),
                    year = info['premiered'][0:4],
                    month = info['premiered'][4:6] if len(info['premiered']) > 4 else '01',
                    day = info['premiered'][6:8] if len(info['premiered']) > 6 else '01',
                )
                SupportFile.write_file(os.path.join(targetpath, 'info.xml'), tmp)
                continue
            except Exception as exception:
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())



    def append_page_count(self, folderpath):
        for file in os.listdir(folderpath):
            zipfilepath = os.path.join(folderpath, file)
            filename_except_ext, filename_ext = os.path.splitext(file)
            if filename_ext not in ['.zip', '.cbz']:
                continue
            match = re.search('#\d+$', filename_except_ext)
            if match:
                continue
            zip_ins = zipfile.ZipFile(zipfilepath)
            count = 0
            zipfilelist = zip_ins.namelist()
            logger.warning(f"파일수 : {len(zipfilelist)}")
            for file_on_zip in zipfilelist:
                tmps = os.path.splitext(file_on_zip)
                if tmps[1].lower() in ['.png', '.jpg', '.gif', '.jpeg', '.webp']:
                    count +=1
                else:
                    logger.error(f"이미지 파일 아님: {file_on_zip}")
                    #return
            if len(zipfilelist) != count:
                logger.error("파일수다름")
                #return
            newfilename = f"{filename_except_ext}#{count}{filename_ext}"
            logger.warning(f"{file} {newfilename}")
            os.rename(zipfilepath, os.path.join(folderpath, newfilename))


    def 파일수추가(self):
        #source = "/host/mnt/etc1/MP2/웹툰/유저"
        source = "/host/mnt/etc1/MP2/만화/모음/수박이"
        for cate in os.listdir(source):
            catepath = os.path.join(source, cate)
            for folder in os.listdir(catepath):
                folderpath = os.path.join(catepath, folder)
                if os.path.isfile(folderpath):
                    continue
                logger.debug(folderpath)
                if self.append_page_count(folderpath) == False:
                    return















    def upload_process(self):
        source = self.config['upload_source']

        for folder in os.listdir(source):
            folderpath = os.path.join(source, folder)
            logger.debug(f"현재폴더 : {folderpath}")
            if folder[0] == '[':
                continue
            if os.path.isfile(folderpath):
                logger.error(f"파일 : {folderpath}")
            for f in os.listdir(folderpath):
                tmps = os.path.splitext(f)
                if tmps[1] in ['.txt']:
                    logger.warning(f"폴더 이동 txt : {folderpath}")
                    shutil.move(folderpath, os.path.join(os.path.dirname(folderpath), '[txt]'))
                    break
                elif tmps[1] in ['.epub']:
                    logger.warning(f"폴더 이동 epub : {folderpath}")
                    shutil.move(folderpath, os.path.join(os.path.dirname(folderpath), '[epub]'))
                    break
                elif tmps[1] in ['.pdf']:
                    logger.warning(f"폴더 이동 pdf : {folderpath}")
                    shutil.move(folderpath, os.path.join(os.path.dirname(folderpath), '[pdf]'))
                    break
                elif tmps[1] in ['.zip', '.cbz']:
                    logger.warning(f"폴더 이동 zip : {folderpath}")
                    shutil.move(folderpath, os.path.join(os.path.dirname(folderpath), '[zip]'))
                    break


    def test(self):
        source = "/host/mnt/etc1/MP2/책/모음/판타지1"

        for folder in os.listdir(source):
            folderpath = os.path.join(source, folder)
            logger.debug(f"현재폴더 : {folderpath}")
            coverjpg = os.path.join(folderpath, '0.jpg')
            if os.path.exists(coverjpg):
                os.rename(coverjpg, os.path.join(folderpath, 'cover.jpg'))
                
            tmp = folder
            tmp = tmp.replace(' [NB]', '')
            tmp = tmp.replace('完', '')
            tmp = tmp.replace('(완)', '')
            tmp = tmp.strip()
            if folder != tmp:
                logger.debug(folderpath)
                logger.debug(tmp)
                shutil.move(folderpath, os.path.join(source, tmp))

    
    
    

    def web(self):

        def move(new_folder, sourcefilepath):
            try:
                target_folderpath = os.path.join(target, SupportString.get_cate_char_by_first(new_folder), new_folder)
                if os.path.exists(target_folderpath):
                    logger.error(f"폴더 있음 : {folder}")
                    return False
                os.makedirs(target_folderpath)

                logger.warning(f"이동 : {folder}")
                shutil.move(sourcefilepath, target_folderpath)
                return True
            except Exception as exception:
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())
            return False

        source = self.config['web_source']
        target = self.config['web_target']
        for folder in os.listdir(source):
            try:
                flag = False
                filepath = os.path.join(source, folder)
                if os.path.isfile(filepath):
                    for ch in ['@', '㉿', 'ⓞ', 'ⓑ']:
                        tmps = folder.split(ch)
                        if len(tmps) == 2:
                            new_folder = SupportFile.text_for_filename(tmps[0].strip())
                            move(new_folder, filepath)
                            flag = True
                            break
                if flag == False:
                    tmp = folder.replace('完', '').strip()
                    new_folder = SupportFile.text_for_filename(tmp)
                    move(new_folder, filepath)

            except Exception as exception:
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())




    

    def test2(self):
        source = "/host/mnt/etc1/MP/Book/웹소설"

        def move(new_folder, sourcefilepath):
            try:
                target_folderpath = os.path.join(target, SupportString.get_cate_char_by_first(new_folder), new_folder)
                if os.path.exists(target_folderpath):
                    logger.error(f"폴더 있음 : {folder}")
                    return False
                os.makedirs(os.path.dirname(target_folderpath), exist_ok=True)

                logger.warning(f"이동 : {folder}")
                shutil.move(sourcefilepath, target_folderpath)
                return True
            except Exception as exception:
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())
            return False


        for folder in os.listdir(source):
            folderpath = os.path.join(source, folder)
            logger.debug(f"현재폴더 : {folderpath}")
            if folder[0] == '[':
                continue
            if os.path.isfile(folderpath):
                logger.error(f"파일 : {folderpath}")
            pdf_count = 0
            zip_count = 0
            for f in os.listdir(folderpath):
                tmps = os.path.splitext(f)
                if tmps[1] in ['.txt']:
                    logger.warning(f"폴더 이동 txt : {folderpath}")
                    shutil.move(folderpath, os.path.join(os.path.dirname(folderpath), '[txt]'))
                    break
                elif tmps[1] in ['.pdf']:
                    pdf_count += 1
                elif tmps[1] in ['.zip', '.cbz']:
                    zip_count += 1
            
            if zip_count >0 and pdf_count > 0 :
                logger.warning(f"폴더 이동 짬뽕zip : {folderpath}")
                shutil.move(folderpath, os.path.join(os.path.dirname(folderpath), '[mix]'))
                continue
            
            target = self.config['web_target']
            flag = False
            for ch in ['@', '㉿', 'ⓞ', 'ⓑ']:
                tmps = folder.split(ch)
                if len(tmps) == 2:
                    new_folder = SupportFile.text_for_filename(tmps[0].strip())
                    move(new_folder, folderpath)
                    flag = True
                    break

            if flag == False:
                tmp = folder.replace('完', '').strip()
                new_folder = SupportFile.text_for_filename(tmp)
                move(new_folder, folderpath)
            
            #return

    def make_dir(self):
        source = "/host/mnt/etc1/MP2/만화/[make_dir]"
        target = "/host/mnt/etc1/MP2/만화/[source]"
        
        for folder in os.listdir(source):
            folderpath = os.path.join(source, folder)
            logger.debug(f"현재폴더 : {folderpath}")
            #if folder[0] == '[':
            #    continue
            if os.path.isfile(folderpath):
                logger.error(f"파일 : {folderpath}")
                tmps = os.path.splitext(folder)
                tmp = tmps[0]
                tmp = re.sub('\(?1[-|~]\d+완\)?', '', tmp)
                tmp = re.sub('\(?전?\d+권\)?', '', tmp)
                tmp = re.sub('\(?\d+권\)?', '', tmp)
                tmp = re.sub('\s완', '', tmp)
                tmp = re.sub('\d+완', '', tmp)
                tmp = re.sub('\d+完', '', tmp)
                tmp = tmp.replace('(완)', '')
                tmp = tmp.replace('(完)', '')
                

                new_path = os.path.join(target, tmp)
                if os.path.exists(new_path) == False:
                    os.makedirs(new_path)
                    shutil.move(folderpath, new_path)
                    logger.warning(f"폴더 이동 : {tmp}")
                    #return

    def webtoon(self):
        #source = "/host/mnt/etc1/MP2/웹툰/완결"
        source = "/host/mnt/etc1/MP2/웹툰/다운로드/카카오웹툰"
        count = 0
        for cate in os.listdir(source):
        #for cate in ['/host/mnt/etc1/MP2/웹툰/완결']:
        #if True:
            catepath = os.path.join(source, cate)
            folder_list = os.listdir(catepath)
            count += len(folder_list)
            for folder in folder_list:
                folderpath = os.path.join(catepath, folder)
                if os.path.isfile(folderpath):
                    continue
                logger.debug(f"현재폴더 : {folderpath}")
                infopath = os.path.join(folderpath, 'info.xml')
                jsonpath = os.path.join(folderpath, 'series.json')
                if os.path.exists(infopath):
                    continue
                """
                for file in os.listdir(folderpath):
                    zipfilepath = os.path.join(folderpath, file)
                    filename_except_ext, filename_ext = os.path.splitext(file)
                    if filename_ext not in ['.zip', '.cbz']:
                        continue
                    match = re.search('#\d+$', filename_except_ext)
                    if match:
                        continue
                    logger.warning(zipfilepath)
                    zip_ins = zipfile.ZipFile(zipfilepath)
                    count = 0
                    zipfilelist = zip_ins.namelist()
                    logger.warning(f"파일수 : {len(zipfilelist)}")
                    for file_on_zip in zipfilelist:
                        tmps = os.path.splitext(file_on_zip)
                        if tmps[1].lower() in ['.png', '.jpg', '.gif', '.webp', '.jpeg']:
                            count +=1
                        else:
                            logger.error("이미지 파일 아님")
                            return
                    if len(zipfilelist) != count:
                        logger.error("파일수다름")
                        return
                    newfilename = f"{filename_except_ext}#{count}{filename_ext}"
                    logger.warning(f"{file} {newfilename}")
                    os.rename(zipfilepath, os.path.join(folderpath, newfilename))
                """

                if os.path.exists(infopath) == False and os.path.exists(jsonpath):
                    data = SupportFile.read_json(jsonpath)
                    #logger.warning(d(data))
                    xml_data, author = self.get_xml_data(data)
                    logger.error(xml_data)
                    SupportFile.write_file(infopath, xml_data)     

                """
                tmp = re.sub("\[.*?\]", '', folder).strip()
                newfolderpath = SupportFile.text_for_filename(f"{tmp} [{author}]")
                if folder != newfolderpath:
                    os.rename(folderpath, os.path.join(catepath, newfolderpath))
                """

                
        
        logger.warning(f"총 폴더 : {count}")
       


    def get_xml_data(self, data):
        if 'key' in data:
            author = []
            inker = []
            publisher = []
            for tmp in data['content']['authors']:
                if tmp['type'] == 'AUTHOR':
                    author.append(tmp['name'])
                elif tmp['type'] == 'ILLUSTRATOR':
                    inker.append(tmp['name'])
                elif tmp['type'] == 'PUBLISHER':
                    publisher.append(tmp['name'])
                else:
                    logger.error(tmp['type'])
            
            xml_data = XML.format(
                title = change(data['content']['title']),
                desc = change(data['content']['catchphraseTwoLines']),
                author = change(', '.join(author)),
                inker = change(', '.join(inker)),
                publisher = change(', '.join(publisher)),
                tags = ', '.join(data['content']['seoKeywords']).replace('#', ''),
                year = data['content']['serialStartDateTime'][0:4],
                month = data['content']['serialStartDateTime'][5:7],
                day = data['content']['serialStartDateTime'][8:10],
            )
            return xml_data, author[0] if len(author) > 0 else ''
        elif 'titleid' in data: #네이버
            xml_data = XML.format(
                title = change(data['title']),
                desc = change(data['desc']),
                author = change(data['author']),
                inker = "",
                publisher = "네이버 웹툰",
                tags = "",
                year = data['episodes'][0]['date'][0:4],
                month = data['episodes'][0]['date'][5:7],
                day = data['episodes'][0]['date'][8:10],
            )
            return xml_data, data['author']
            


    @classmethod
    def process_cli(cls):
        import yaml, argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--config', default='config.yaml', help='config filepath')
        parser.add_argument('--mode', default='info', help='rename / clear')

        args = parser.parse_args()
        with open(args.config, encoding='utf8') as file:
            config = yaml.load(file, Loader=yaml.FullLoader)
        SiteNaverBook.api_key = config['naver_api_key']
        SiteKakaoBook.api_key = config['kakao_api_key']
        ins = ReadingProcess(config)
        if args.mode == 'info':
            from make_info import MakeInfo
            MakeInfo(ins, config).start()
        elif args.mode == 'epub':
            from text2epub import Text2Epub
            Text2Epub(ins, config).start()

        elif args.mode == 'upload':
            ins.upload_process()
        elif args.mode == 'test':
            ins.test()
        elif args.mode == 'web':
            ins.web()
        elif args.mode == 'test2':
            ins.test2()
        elif args.mode == 'make_dir':
            ins.make_dir()
        elif args.mode == 'webtoon':
            ins.webtoon()
        elif args.mode == '파일수추가':
            ins.파일수추가()
        



XML = '''<?xml version="1.0"?>
<ComicInfo xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Title>{title}</Title>
  <Series>{title}</Series>
  <Summary>{desc}</Summary>
  <Writer>{author}</Writer>
  <Publisher>{publisher}</Publisher>
  <Genre></Genre>
  <Tags>{tags}</Tags>
  <LanguageISO>ko</LanguageISO>
  <Notes>완결</Notes>
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
                    
                


if __name__ == '__main__':
    ReadingProcess.process_cli()

