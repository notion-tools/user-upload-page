from flask import Flask, render_template, request
import threading
from notion_page import regist_page

app = Flask(__name__)

@app.route('/')
def hello():
    return "hello, world"

@app.route('/api/v1/user_page_upload', methods = ['POST'])
def result():
    if request.is_json:
        params = request.get_json()
        if '링크' in params and '제목' in params:
            print(params['링크'])
            link = str(params['링크'])
            title = str(params['제목'])
            t = threading.Thread(target=regist_page, args=(link, title))
            t.start()
            return 'ok'
        else:
            return '400 Bad Request', 400
    else:
        return '400 Bad Request', 400
    

if __name__ == '__main__':
    app.run(debug = True, port=3000, host='0.0.0.0')