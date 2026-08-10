#!/usr/bin/env python3
import json,time,os,urllib.request,urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
API_KEY=os.environ.get('BAIDU_OCR_API_KEY','')
SECRET_KEY=os.environ.get('BAIDU_OCR_SECRET_KEY','')
_tc={'t':None,'e':0}
def get_token():
    now=time.time()
    if _tc['t'] and now<_tc['e']-86400: return _tc['t']
    url='https://aip.baidubce.com/oauth/2.0/token'
    data=urllib.parse.urlencode({'grant_type':'client_credentials','client_id':API_KEY,'client_secret':SECRET_KEY}).encode()
    req=urllib.request.Request(url,data=data,method='POST')
    req.add_header('Content-Type','application/x-www-form-urlencoded')
    with urllib.request.urlopen(req,timeout=10) as r:
        d=json.loads(r.read())
    _tc['t']=d['access_token'];_tc['e']=now+d.get('expires_in',2592000)
    return _tc['t']

def baidu_ocr(img_b64,accurate=True):
    token=get_token()
    endpoint='accurate_basic' if accurate else 'general_basic'
    url=f'https://aip.baidubce.com/rest/2.0/ocr/v1/{endpoint}?access_token={token}'
    data=urllib.parse.urlencode({
        'image':img_b64,
        'language_type':'CHN_ENG',
        'detect_direction':'true',
        'paragraph':'true'
    }).encode()
    req=urllib.request.Request(url,data=data,method='POST')
    req.add_header('Content-Type','application/x-www-form-urlencoded')
    with urllib.request.urlopen(req,timeout=30) as r:
        result=json.loads(r.read())
    if 'error_code' in result:
        raise Exception(f"{result['error_code']}:{result.get('error_msg','')}")
    words_list=result.get('words_result',[])
    paragraphs=result.get('paragraphs_result',[])
    if paragraphs and words_list:
        texts=[]
        for p in paragraphs:
            idxs=p.get('words_result_idx',[])
            line=''.join(words_list[i].get('words','') for i in idxs if i < len(words_list))
            if line.strip(): texts.append(line.strip())
        return '\n\n'.join(texts)
    lines=[w.get('words','').strip() for w in words_list if w.get('words','').strip()]
    return '\n'.join(lines)

class H(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200);self._cors();self.end_headers()
    def do_POST(self):
        if self.path!='/api/ocr': self.send_response(404);self.end_headers();return
        try:
            body=self.rfile.read(int(self.headers.get('Content-Length',0)))
            d=json.loads(body);img=d.get('image','')
            if not img: self._resp(400,{'error':'缺少图片'});return
            if ',' in img: img=img.split(',',1)[1]
            if len(img)>5600000: self._resp(400,{'error':'图片太大'});return
            text=baidu_ocr(img,d.get('accurate',True))
            self._resp(200,{'text':text})
        except Exception as e:
            self._resp(500,{'error':str(e)})
    def _resp(self,code,obj):
        b=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(code);self._cors()
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
    def _cors(self):
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
    def log_message(self,*a): pass

if __name__=='__main__':
    if not API_KEY or not SECRET_KEY: print('ERROR: missing keys');exit(1)
    print('OCR proxy started on 127.0.0.1:8889')
    HTTPServer(('127.0.0.1',8889),H).serve_forever()
