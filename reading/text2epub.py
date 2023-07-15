import os, sys, traceback, json, urllib.parse, requests, argparse, platform
from tkinter import E
import xmltodict, shutil
from datetime import datetime
if platform.system() == 'Windows':
    sys.path += ["C:\SJVA3\lib2", "C:\SJVA3\data\custom", "C:\SJVA3_DEV"]
else:
    sys.path += ["/root/SJVA3/lib2", "/root/SJVA3/data/custom"]
from support.base import get_logger, d, default_headers, SupportFile
from support.base.discord import SupportDiscord


logger = get_logger()

class Text2Epub:
    def __init__(self, main_ins, config):
        self.main_ins = main_ins
        self.config = config

    def start(self):
        source = self.config['text2epub']['source_folderpath']
        for title_folder in sorted(os.listdir(source)):
            title_folderpath = os.path.join(source, title_folder)
            if os.path.isfile(title_folderpath):
                continue
            logger.info(f"현재폴더 : {title_folderpath}")
            cover_filepath = os.path.join(title_folderpath, 'cover.jpg')
            info_filepath = os.path.join(title_folderpath, 'info.xml')
            if os.path.exists(cover_filepath) == False:
                logger.warning(f"cover.jpg 없음 : {info_filepath}")
                continue
            if os.path.exists(info_filepath) == False:
                logger.warning(f"info.xml 없음 : {info_filepath}")
                continue
            ret = self.start_folder(title_folderpath)
            if ret == False:
                logger.error(f"에러 : {title_folder}")
    

    def start_folder(self, source):
        try:
            exist_text = False
            for text_file in sorted(os.listdir(source)):
                tmp = os.path.splitext(text_file)
                if tmp[1].lower() == '.txt':
                    exist_text = True
                    
                elif tmp[1].lower() == '.epub':
                    logger.info("epub 파일이 이미 있음")
                    return 
            if exist_text == False:
                logger.info("텍스트 파일 없음")
                return 
            

            info = self._load_info(source)
            info['templete_folderpath'] = self.템플릿복사(source, info)

            current_page = 1
            total_data = []
            for text_file in sorted(os.listdir(source)):
                tmp = os.path.splitext(text_file)
                if tmp[1].lower() != '.txt':
                    continue
                filepath = os.path.join(source, text_file)
                text_data = self.텍스트파일읽기(filepath)
                total_data.append(text_data)
                logger.info(f"라인수 : {text_data['total_line_count']}")

            self.EPUB생성(source, info, total_data)
            return True
        except Exception as e:
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
        return False
    
    def EPUB생성(self, source, info, data):
        templete_filepath = os.path.join(os.path.dirname(__file__), 'epub_templete', 'FILE', 'Section.xhtml')
        text = SupportFile.read_file(templete_filepath)
        #ret = self.인포삽입(text, info)
        info['CONTENT1'] = ''
        info['CONTENT2'] = ''
        info['MENU'] = ''
        total_number = 0
        for item in data:
            current_number = 0
            while True:
                start = current_number * self.config['text2epub']['HTML줄수']
                end = (current_number + 1) * self.config['text2epub']['HTML줄수']
                if item['total_line_count'] < end:
                    end = item['total_line_count']
                
                html = self.인포삽입(text, info, content='\n'.join(item['html'][start:end]))
                total_number += 1
                current_number += 1
                inner_filename = f'Section{str(total_number).zfill(4)}.xhtml'
                filepath = os.path.join(info['templete_folderpath'], 'OEBPS', 'Text', inner_filename)
                SupportFile.write_file(filepath, html)
                info['CONTENT1'] += f'\n    <item id="{inner_filename}" href="Text/{inner_filename}" media-type="application/xhtml+xml"/>'
                info['CONTENT2'] += f'\n    <itemref idref="{inner_filename}"/>'

                info['MENU'] += f'''
  <navPoint id="navPoint-1" playOrder="1">
    <navLabel>
      <text>{str(total_number).zfill(3)}</text>
    </navLabel>
    <content src="Text/{inner_filename}"/>
  </navPoint>'''   
                if end == item['total_line_count']:
                    break
        info['section_count'] = total_number

        # 커버
        templete_filepath = os.path.join(os.path.dirname(__file__), 'epub_templete', 'FILE', 'cover.xhtml')
        text = SupportFile.read_file(templete_filepath)
        text = self.인포삽입(text, info)
        filepath = os.path.join(info['templete_folderpath'], 'OEBPS', 'Text', f'cover.xhtml')
        SupportFile.write_file(filepath, text)

        # content.opf
        templete_filepath = os.path.join(os.path.dirname(__file__), 'epub_templete', 'FILE', 'content.opf')
        text = SupportFile.read_file(templete_filepath)
        text = self.인포삽입(text, info)
        filepath = os.path.join(info['templete_folderpath'], 'OEBPS', f'content.opf')
        SupportFile.write_file(filepath, text)

        # toc.ncx
        templete_filepath = os.path.join(os.path.dirname(__file__), 'epub_templete', 'FILE', 'toc.ncx')
        text = SupportFile.read_file(templete_filepath)
        text = self.인포삽입(text, info)
        filepath = os.path.join(info['templete_folderpath'], 'OEBPS', f'toc.ncx')
        SupportFile.write_file(filepath, text)

        #     <item id="Section0002.xhtml" href="Text/Section0002.xhtml" media-type="application/xhtml+xml"/>
        # <itemref idref="Section0001.xhtml"/>

        # cover
        shutil.copy(os.path.join(source, 'cover.jpg'), os.path.join(info['templete_folderpath'], 'OEBPS', 'Images'))
        
        self.makezip_all(info['templete_folderpath'], zip_extension='epub', remove_zip_path=True)

    
    def 인포삽입(self, text, info, content=None):
        if content == None:
            ret = text.format(**info, CONTENT="{CONTENT}")
        else:
            ret = text.format(**info, CONTENT=content)
        return ret


    
    def 텍스트파일읽기(self, filepath):
        text = SupportFile.read_file(filepath)

        ret = {
            'append_text_line': 0,
            'append_empty_line': 0,
            'html': [],
        }
        empty_line_count = 0
        
        for line in text.split('\n'):
            line = line.strip()
            if line == '':
                empty_line_count += 1
                if empty_line_count % self.config['text2epub']['EPUB_빈줄비율'] == 0:
                    ret['html'].append('\n<p class="basic-1"><br/></p>')
                    ret['append_empty_line'] += 1
                continue
            empty_line_count = 0
            ret['html'].append(f'\n<p class="basic-1">{self.replace_xml(line)}</p>')
            ret['append_text_line'] += 1
        ret['total_line_count'] = len(ret['html'])
        return ret


        

    def _load_info(self, source):
        info = SupportFile.read_file(os.path.join(source, 'info.xml'))
        #logger.debug(info)
        info = xmltodict.parse(info)
        info['TITLE'] = info['ComicInfo']['Title']
        info['AUTHOR'] = info['ComicInfo']['Writer']
        info['PUBLISHER'] = info['ComicInfo']['Publisher']
        info['DATE'] = f"{info['ComicInfo']['Year']}-{info['ComicInfo']['Month']}-{info['ComicInfo']['Day']}" 
        info['CURRENT_DATETIME'] = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        return info
        #logger.debug(d(info))
        #logger.info(d(info['ComicInfo']['Title']))

    def 템플릿복사(self, source, info):
        templete_folderpath = os.path.join(source, SupportFile.text_for_filename(f"{info['ComicInfo']['Title']} [{info['ComicInfo']['Writer']}] [txt]"))
        #logger.error(templete_folderpath)
        
        if os.path.exists(templete_folderpath):
            shutil.rmtree(templete_folderpath)

        original_templete_folderpath = os.path.join(os.path.dirname(__file__), 'epub_templete', 'COPY')
        shutil.copytree(original_templete_folderpath, templete_folderpath)
        os.makedirs(os.path.join(templete_folderpath, 'OEBPS', 'Text'), exist_ok=True)
        os.makedirs(os.path.join(templete_folderpath, 'OEBPS', 'Images'), exist_ok=True)
        return templete_folderpath


    def replace_xml(self, xml):
        tmp = [['&', '&amp;'], ['<', '&lt;'], ['>', '&gt;'], ['‘', '&apos;'], ['"', '&quot;']]
        for t in tmp:
            xml = xml.replace(t[0], t[1])
        return xml


    def makezip_all(self, zip_path, zip_filepath=None, zip_extension='zip', remove_zip_path=True):
        import zipfile, shutil
        from pathlib import Path
        try:
            if os.path.exists(zip_path) == False:
                return False
            if zip_filepath == None:
                zipfilepath = os.path.join(os.path.dirname(zip_path), f"{os.path.basename(zip_path)}.{zip_extension}")
            if os.path.exists(zipfilepath):
                os.remove(zipfilepath)
            zip = zipfile.ZipFile(zipfilepath, 'w')
            for (path, dir, files) in os.walk(zip_path):
                for file in files:
                    src = os.path.join(path, file)
                    target = src.replace(zip_path+'/', '').replace(zip_path+'\\', '')
                    zip.write(src, target, compress_type=zipfile.ZIP_DEFLATED)

            zip.close()

            if remove_zip_path:
                shutil.rmtree(zip_path)
            return zipfilepath
        except Exception as e:
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
        return None

if __name__ == '__main__':
    ins = Text2Epub()
    ins.process_args()
