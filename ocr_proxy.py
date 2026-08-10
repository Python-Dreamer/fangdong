#!/usr/bin/env python3
"""百度OCR代理服务 - 监听127.0.0.1:8889，nginx反代 /api/ocr/
返回结构化数据：text(纯文本) + paragraphs(带位置的段落) + lines(带位置的行)
"""

import json
import time
import os
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

API_KEY = os.environ.get('BAIDU_OCR_API_KEY', '')
SECRET_KEY = os.environ.get('BAIDU_OCR_SECRET_KEY', '')

_token_cache = {'token': None, 'expires': 0}

def get_access_token():
    now = time.time()
    if _token_cache['token'] and now < _token_cache['expires'] - 86400:
        return _token_cache['token']
    url = 'https://aip.baidubce.com/oauth/2.0/token'
    params = urllib.parse.urlencode({
        'grant_type': 'client_credentials',
        'client_id': API_KEY,
        'client_secret': SECRET_KEY
    }).encode()
    req = urllib.request.Request(url, data=params, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    _token_cache['token'] = data['access_token']
    _token_cache['expires'] = now + data.get('expires_in', 2592000)
    return _token_cache['token']


def baidu_ocr(image_base64, accurate=True):
    token = get_access_token()
    if accurate:
        url = f'https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic?access_token={token}'
    else:
        url = f'https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={token}'

    post_data = urllib.parse.urlencode({
        'image': image_base64,
        'language_type': 'CHN_ENG',
        'detect_direction': 'true',
        'paragraph': 'true'
    }).encode()

    req = urllib.request.Request(url, data=post_data, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())

    if 'error_code' in result:
        raise Exception(f"百度API错误 {result['error_code']}: {result.get('error_msg', '')}")

    words_list = result.get('words_result', [])
    paragraphs_raw = result.get('paragraphs_result', [])
    direction = result.get('direction', 0)

    # 构建带位置的行对象
    lines = []
    for i, w in enumerate(words_list):
        loc = w.get('location', {})
        text = w.get('words', '').strip()
        if text:
            lines.append({
                'i': i,
                'text': text,
                'top': loc.get('top', 0),
                'left': loc.get('left', 0),
                'width': loc.get('width', 0),
                'height': loc.get('height', 0)
            })

    # 构建带位置的段落对象
    paras = []
    if paragraphs_raw:
        for p in paragraphs_raw:
            idxs = p.get('words_result_idx', [])
            valid = [i for i in idxs if i < len(words_list)]
            if not valid:
                continue
            text = ''.join(words_list[i].get('words', '') for i in valid).strip()
            if not text:
                continue
            tops = [words_list[i].get('location', {}).get('top', 0) for i in valid]
            lefts = [words_list[i].get('location', {}).get('left', 0) for i in valid]
            rights = [words_list[i].get('location', {}).get('left', 0) + words_list[i].get('location', {}).get('width', 0) for i in valid]
            bots = [words_list[i].get('location', {}).get('top', 0) + words_list[i].get('location', {}).get('height', 0) for i in valid]
            paras.append({
                'text': text,
                'top': min(tops),
                'left': min(lefts),
                'width': max(rights) - min(lefts),
                'height': max(bots) - min(tops),
                'line_indices': valid
            })
    else:
        for l in lines:
            paras.append({
                'text': l['text'],
                'top': l['top'],
                'left': l['left'],
                'width': l['width'],
                'height': l['height'],
                'line_indices': [l['i']]
            })

    # 估算图片尺寸
    img_w = max((l['left'] + l['width'] for l in lines), default=1000)
    img_h = max((l['top'] + l['height'] for l in lines), default=1000)
    img_w = max(img_w, int(img_w * 1.05))
    img_h = max(img_h, int(img_h * 1.05))

    plain = '\n\n'.join(p['text'] for p in paras)

    return {
        'text': plain,
        'words': [l['text'] for l in lines],
        'lines': lines,
        'paragraphs': paras,
        'image_width': img_w,
        'image_height': img_h,
        'direction': direction
    }


class OCRHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path != '/api/ocr':
            self.send_response(404)
            self.end_headers()
            return

        try:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            data = json.loads(body)

            image_b64 = data.get('image', '')
            accurate = data.get('accurate', True)

            if not image_b64:
                self._json_resp(400, {'error': '缺少图片数据'})
                return

            if ',' in image_b64:
                image_b64 = image_b64.split(',', 1)[1]

            if len(image_b64) > 5_600_000:
                self._json_resp(400, {'error': '图片太大，请裁剪或压缩后再试'})
                return

            result = baidu_ocr(image_b64, accurate)
            self._json_resp(200, result)

        except Exception as e:
            self._json_resp(500, {'error': str(e)})

    def _json_resp(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self._cors_headers()
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def log_message(self, fmt, *args):
        pass


if __name__ == '__main__':
    if not API_KEY or not SECRET_KEY:
        print("ERROR: 请设置 BAIDU_OCR_API_KEY 和 BAIDU_OCR_SECRET_KEY 环境变量")
        exit(1)
    server = HTTPServer(('127.0.0.1', 8889), OCRHandler)
    print("OCR代理服务启动: 127.0.0.1:8889")
    server.serve_forever()
