#!/usr/bin/env python3
"""百度OCR代理服务 - 监听127.0.0.1:8889，nginx反代 /api/ocr/"""

import json
import time
import os
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# ===== 配置（从环境变量读取） =====
API_KEY = os.environ.get('BAIDU_OCR_API_KEY', '')
SECRET_KEY = os.environ.get('BAIDU_OCR_SECRET_KEY', '')

# 缓存access_token
_token_cache = {'token': None, 'expires': 0}

def get_access_token():
    """获取百度access_token，缓存30天"""
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
    """调用百度OCR API"""
    token = get_access_token()

    if accurate:
        # 高精度版（每天免费500次）
        url = f'https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic?access_token={token}'
    else:
        # 标准版（每天免费1000次）
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

    # 提取文字
    words = []
    if 'words_result' in result:
        for item in result['words_result']:
            words.append(item.get('words', ''))
    return words


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

            # 去掉data URL前缀
            if ',' in image_b64:
                image_b64 = image_b64.split(',', 1)[1]

            # 图片太大时压缩提示（百度限制base64后4M，原图约6M）
            if len(image_b64) > 5_600_000:
                self._json_resp(400, {'error': '图片太大，请裁剪或压缩后再试'})
                return

            words = baidu_ocr(image_b64, accurate)
            self._json_resp(200, {'words': words})

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
        pass  # 静默日志


if __name__ == '__main__':
    if not API_KEY or not SECRET_KEY:
        print("ERROR: 请设置 BAIDU_OCR_API_KEY 和 BAIDU_OCR_SECRET_KEY 环境变量")
        exit(1)

    server = HTTPServer(('127.0.0.1', 8889), OCRHandler)
    print("OCR代理服务启动: 127.0.0.1:8889")
    server.serve_forever()
