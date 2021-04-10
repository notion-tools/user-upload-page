
#!/usr/local/bin/python3.8
import pickle, os, time, datetime, sys
from notion.client import NotionClient
from notion import block
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

def now():
    return datetime.datetime.now()

class Logging:
    def __init__(self):
        self.log = ""

    def write(self, message):
        print(message)
        self.log = self.log + f"[{now()}] {message}\n"

    def __str__(self):
        return self.log

def regist_page(link:str, title:str):
    log = Logging()

    # 데이터베이스 등록 지연 오류를 받기 위한 5초 지연
    log.write("요청을 받았습니다. 5초간 대기합니다.")
    log.write(f"요청 정보 : {link}({title})")
    time.sleep(5)

    # 설정
    '''설정 파일 (config.txt)
    
    1번째 줄 : token_v2
    2번째 줄 : 요청 데이터베이스 주소
    3번째 줄 : 메인 데이터베이스 주소

    '''
    if os.path.isfile('config.txt'):
        with open('config.txt', 'r', encoding='utf-8') as f:
            config_file = f.readlines()
            NOTION_TOKEN = config_file[0].replace('\n','')
            NOTION_DATABASE_LINK = config_file[1].replace('\n','')
            NOTION_REQUEST_DATABASE_LINK = config_file[2].replace('\n','')
            NOTION_LOG_LINK = config_file[3].replace('\n','')

    else:
        log.write(f'오류 설정 파일을 불러올 수 없습니다.')

    # 노션 클라이언트 연결
    client = NotionClient(token_v2=NOTION_TOKEN)

    # 요청 데이터베이스 조회
    log.write(f'요청 데이터베이스를 조회합니다.')
    page_row = None
    request_database_cv = client.get_collection_view(NOTION_REQUEST_DATABASE_LINK)
    for row in request_database_cv.collection.get_rows():
        if link == row.title:
            page_row = row
            break
    page_row.status = '🔨 작업 중'
    if not page_row:
        log.write(f'오류 - 조회 실패')
        notion_log = client.get_block(NOTION_LOG_LINK)
        notion_log_page = notion_log.children.add_new(block.PageBlock, title=link)
        notion_log_page.children.add_new(block.CodeBlock, title=log)
        return

    # 파이썬 링크 분류
    if link.startswith('https://www.notion.so/') or link.startswith("https://notion.so/"): page_type = "Notion"
    elif link.startswith("https://"): page_type = "Website"
    else:
        log.write(f'등록 불가 - 올바르지 않은 링크')
        page_row.status = '⚠ 등록 불가 - 링크가 올바르지 않음'
        notion_log = client.get_block(NOTION_LOG_LINK)
        notion_log_page = notion_log.children.add_new(block.PageBlock, title=link)
        notion_log_page.children.add_new(block.CodeBlock, title=log)
        return

    # 금지된 페이지 필터링
    with open('ban.txt', 'r', encoding='utf-8') as f:
        baned_pages = f.readlines()
    for i in baned_pages:
        if link.startswith(i):
            page_row.status = '⚠ 등록 불가 - 금지된 페이지'
            notion_log = client.get_block(NOTION_LOG_LINK)
            notion_log_page = notion_log.children.add_new(block.PageBlock, title=link)
            notion_log_page.children.add_new(block.CodeBlock, title=log)
            return

    # 중복된 페이지 필터링
    main_database_cv = client.get_collection_view(NOTION_DATABASE_LINK)
    already_pages = []
    for row in main_database_cv.collection.get_rows(): already_pages.append(row.link)
    if link in already_pages:
        log.write(f'등록 불가 - 중복된 페이지')
        page_row.status = '⚠ 등록 불가 - 중복된 페이지'
        notion_log = client.get_block(NOTION_LOG_LINK)
        notion_log_page = notion_log.children.add_new(block.PageBlock, title=link)
        notion_log_page.children.add_new(block.CodeBlock, title=log)
        return

    # 작업 시작
    log.write(f'페이지 작업을 시작합니다.')
    page_row.status = '🔨 작업 중 - 페이지 불러오는 중'
    page_tags = page_row.tags
    page_row.title = title
    page_row.type = page_type

    # 기존 페이지 스크린샷
    try:
        log.write(f'썸네일을 캡쳐합니다.')
        page_screenshot_name = now().strftime("%Y%m$d%H%M%S")
        option = Options()
        option.add_argument('headless')
        option.add_argument('--window-size=1920,1080')
        option.add_argument('--no-sandbox')
        option.add_argument('--disable-dev-shm-usage')
        browser = webdriver.Chrome(executable_path='chromedriver.exe', options=option)
        browser.get(link)
        log.write(f'[{now()}] 브라우저 로딩 완료, 5초 대기')
        time.sleep(5)
        browser.save_screenshot(f"./img/{page_screenshot_name}.png")
        browser.quit
        log.write(f'[{now()}] 캡쳐 완료')
    except Exception as e:
        log.write(f'캡쳐 오류 {e}')
        page_row.status = '⚠ 등록 불가 - 링크가 올바르지 않음'
        notion_log = client.get_block(NOTION_LOG_LINK)
        notion_log_page = notion_log.children.add_new(block.PageBlock, title=link)
        notion_log_page.children.add_new(block.CodeBlock, title=log)
        return

    # 페이지 생성
    page_row.status = '🔨 작업 중 - 페이지 생성 중'
    notion_database = client.get_block(NOTION_DATABASE_LINK)
    log.write(f'페이지를 생성합니다.')
    new_page = notion_database.collection.add_row()
    new_page.set_property('link', link)
    new_page.set_property('태그', page_tags)
    new_page.title = title

    # 페이지 코드 블록 추가
    log.write(f'코드 블록을 추가합니다.')
    with open('codeblock.txt', 'r', encoding="utf-8") as f:
        codeblock_code = f.read()
        codeblock = new_page.children.add_new(block.CodeBlock, title=codeblock_code)
        codeblock.language = "html"

    # 페이지 썸네일 추가
    log.write(f'이미지를 추가합니다.')
    new_img_block = new_page.children.add_new(block.ImageBlock)
    new_img_block.upload_file(path=f'./img/{page_screenshot_name}.png')
    log.write(f'이미지 파일을 삭제합니다.')
    os.remove(f'./img/{page_screenshot_name}.png')

    # 페이지 북마크 추가
    log.write(f'북마크를 추가합니다.')
    new_bookmark_block = new_page.children.add_new(block.BookmarkBlock)
    new_bookmark_block.set_new_link(link)

    # 등록 완료
    page_row.status = '🎉 등록 완료'
    log.write(f'등록 완료')

    # 로그 전송
    log.write(f'로그 업로드')
    notion_log = client.get_block(NOTION_LOG_LINK)
    notion_log_page = notion_log.children.add_new(block.PageBlock, title=link)
    notion_log_page.children.add_new(block.CodeBlock, title=log)

    return True
    
if __name__ == '__main__':
    regist_page('', '')