#!/usr/bin/env python3
"""轻量文件存储服务 + 管理API - 替代Supabase Storage和Admin API"""
import os, json, uuid, mimetypes, hmac, hashlib, base64, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import urllib.parse, urllib.request

UPLOAD_DIR = "/opt/fangdong/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 加载.env
ENV = {}
env_path = "/opt/fangdong/.env"
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                ENV[k] = v

JWT_SECRET = ENV.get("JWT_SECRET", "")
OPERATOR_TOKEN = ENV.get("GOTRUE_OPERATOR_TOKEN", "")
AUTH_URL = "http://127.0.0.1:9999"
REST_URL = "http://127.0.0.1:3000"
SERVICE_KEY = None

ADMIN_EMAILS = ["332303155@qq.com", "18213501784@163.com"]

def _b64dec(s):
    s += "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)

def verify_jwt(token):
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        signing_input = f"{parts[0]}.{parts[1]}".encode()
        expected_sig = hmac.new(JWT_SECRET.encode(), signing_input, hashlib.sha256).digest()
        actual_sig = _b64dec(parts[2])
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        payload = json.loads(_b64dec(parts[1]))
        if payload.get("exp") and payload["exp"] < time.time():
            return None
        # 拒绝 anon 角色调用写操作（anon key 不应能上传/删除）
        if payload.get("role") == "anon":
            return None
        return payload
    except Exception as e:
        return None

def get_service_key():
    global SERVICE_KEY
    if SERVICE_KEY:
        return SERVICE_KEY
    def b64(b):
        return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
    header = b64(json.dumps({"alg":"HS256","typ":"JWT"}).encode())
    now = int(time.time())
    payload = b64(json.dumps({
        "iss":"supabase","ref":"fangdong-local",
        "role":"service_role","iat":now,"exp":now+315360000
    }).encode())
    sig = b64(hmac.new(JWT_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
    SERVICE_KEY = f"{header}.{payload}.{sig}"
    return SERVICE_KEY

def get_user_email_from_token(payload):
    """GoTrue签发的JWT中email在payload.email里，sub是user_id"""
    if not payload:
        return None, None
    email = payload.get("email") or payload.get("user_metadata",{}).get("email")
    uid = payload.get("sub") or payload.get("user_id") or payload.get("id")
    return email, uid

def auth_request(handler):
    """普通登录用户校验：任何有效JWT（非anon）即可"""
    auth = handler.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        # 兼容 apikey header
        ak = handler.headers.get("apikey", "")
        if ak and ak.count(".") == 2:
            payload = verify_jwt(ak)
            if payload and payload.get("role") != "anon":
                email, uid = get_user_email_from_token(payload)
                return {"email": email, "uid": uid, "payload": payload}
        return None
    token = auth[7:]
    payload = verify_jwt(token)
    if not payload:
        return None
    email, uid = get_user_email_from_token(payload)
    return {"email": email, "uid": uid, "payload": payload}

def auth_admin_request(handler):
    user = auth_request(handler)
    if not user:
        return None
    if user["email"] in ADMIN_EMAILS:
        return user
    return None

def http_request(method, url, headers=None, data=None):
    req = urllib.request.Request(url, method=method, headers=headers or {})
    if data is not None:
        req.data = json.dumps(data).encode() if isinstance(data, dict) else data
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body)
        except:
            return e.code, {"error": body}

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class FileHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,DELETE,PUT,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,Authorization,apikey")

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)

        # 管理API - 用户列表
        if path == "/admin/users":
            admin = auth_admin_request(self)
            if not admin:
                self._json(403, {"error": "无权限"})
                return
            status, resp = http_request("GET", f"{AUTH_URL}/admin/users?page=1&per_page=200",
                {"Authorization": f"Bearer {get_service_key()}", "apikey": get_service_key()})
            if status == 200:
                users = resp.get("users", [])
                sk = get_service_key()
                ws, wresp = http_request("GET", f"{REST_URL}/whitelist?select=*",
                    {"apikey": sk, "Authorization": f"Bearer {sk}"})
                wl_map = {}
                if ws == 200:
                    for w in wresp:
                        wl_map[w["email"]] = w
                result = []
                for u in users:
                    w = wl_map.get(u.get("email", ""))
                    result.append({
                        "id": u.get("id"),
                        "email": u.get("email", ""),
                        "created_at": u.get("created_at", ""),
                        "last_sign_in": u.get("last_sign_in_at", ""),
                        "confirmed": u.get("email_confirmed_at") is not None,
                        "tier": w.get("tier", "free") if w else "free",
                        "expires_at": w.get("expires_at") if w else None,
                        "is_admin": u.get("email", "") in ADMIN_EMAILS
                    })
                self._json(200, {"users": result})
            else:
                self._json(status, resp)
            return

        # 文件读取（保持公开：图片要在<img>标签里加载）
        if path.startswith("/files/"):
            rel = path[len("/files/"):]
            fp = os.path.normpath(os.path.join(UPLOAD_DIR, rel))
            if not fp.startswith(UPLOAD_DIR) or not os.path.isfile(fp):
                self.send_response(404); self._cors(); self.end_headers()
                return
            mime, _ = mimetypes.guess_type(fp)
            self.send_response(200)
            self.send_header("Content-Type", mime or "application/octet-stream")
            self.send_header("Cache-Control", "public, max-age=31536000")
            self._cors()
            self.end_headers()
            with open(fp, "rb") as f:
                self.wfile.write(f.read())
            return

        self._json(404, {"error": "not found"})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)

        # 管理API - 创建用户
        if path == "/admin/create-user":
            admin = auth_admin_request(self)
            if not admin:
                self._json(403, {"error": "无权限"})
                return
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            email = body.get("email", "").strip().lower()
            password = body.get("password", "").strip()
            tier = body.get("tier", "free")
            duration = body.get("duration", "1year")

            if not email or "@" not in email:
                self._json(400, {"error": "邮箱格式不正确"})
                return
            if len(password) < 6:
                self._json(400, {"error": "密码至少6位"})
                return

            status, resp = http_request("POST", f"{AUTH_URL}/admin/users",
                {"Authorization": f"Bearer {get_service_key()}", "apikey": get_service_key(),
                 "Content-Type": "application/json"},
                {"email": email, "password": password, "email_confirm": True})

            if status not in (200, 201):
                err_msg = resp.get("msg", resp.get("error", resp.get("message", "创建失败")))
                self._json(status, {"error": err_msg})
                return

            user_id = resp.get("id", "")

            if tier in ("pro", "basic"):
                expires_at = None
                if duration != "forever":
                    months = {"1month":1, "3months":3, "1year":12}.get(duration, 12)
                    exp = time.time() + months * 30 * 86400
                    expires_at = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(exp))
                sk = get_service_key()
                wdata = {"email": email, "tier": tier, "expires_at": expires_at}
                http_request("POST", f"{REST_URL}/whitelist",
                    {"apikey": sk, "Authorization": f"Bearer {sk}",
                     "Content-Type": "application/json", "Prefer": "return=representation"},
                    wdata)

            self._json(200, {"ok": True, "user_id": user_id, "email": email, "tier": tier})
            return

        # 文件上传（需登录）
        if path.startswith("/upload/"):
            user = auth_request(self)
            if not user:
                self._json(401, {"error": "请先登录"})
                return
            rel = path[len("/upload/"):]
            parts = [p.replace("..","").replace("/","") for p in rel.split("/") if p]
            if not parts:
                self._json(400, {"error": "invalid path"}); return
            target_dir = os.path.join(UPLOAD_DIR, *parts[:-1])
            os.makedirs(target_dir, exist_ok=True)
            target = os.path.normpath(os.path.join(target_dir, parts[-1]))
            if not target.startswith(UPLOAD_DIR):
                self._json(403, {"error": "forbidden"}); return
            # 文件类型白名单（只允许图片和PDF，防止上传HTML/JS等可执行文件）
            import re as _re
            ext = os.path.splitext(parts[-1])[1].lower()
            ALLOWED_EXT = {'.jpg','.jpeg','.png','.gif','.webp','.bmp','.pdf','.heic','.heif'}
            if ext not in ALLOWED_EXT:
                self._json(400, {"error": "不支持的文件类型，仅允许图片和PDF"}); return
            length = int(self.headers.get("Content-Length", 0))
            if length > 20 * 1024 * 1024:
                self._json(413, {"error": "too large"}); return
            data = self.rfile.read(length)
            with open(target, "wb") as f:
                f.write(data)
            rel_path = "/".join(parts)
            self._json(200, {"path": rel_path, "Key": rel_path})
            return

        self._json(404, {"error": "not found"})

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)

        # 管理API - 删除用户
        if path.startswith("/admin/users/"):
            admin = auth_admin_request(self)
            if not admin:
                self._json(403, {"error": "无权限"})
                return
            user_id = path[len("/admin/users/"):]
            status, resp = http_request("DELETE", f"{AUTH_URL}/admin/users/{user_id}",
                {"Authorization": f"Bearer {get_service_key()}", "apikey": get_service_key()})
            if status in (200, 204):
                sk = get_service_key()
                us, uresp = http_request("GET", f"{AUTH_URL}/admin/users/{user_id}",
                    {"Authorization": f"Bearer {get_service_key()}", "apikey": get_service_key()})
                if us == 200 and uresp.get("email"):
                    uemail = uresp["email"]
                    http_request("DELETE", f"{REST_URL}/whitelist?email=eq.{uemail}",
                        {"apikey": sk, "Authorization": f"Bearer {sk}"})
                self._json(200, {"ok": True})
            else:
                self._json(status, resp)
            return

        # 文件删除（需登录）
        if path.startswith("/files/"):
            user = auth_request(self)
            if not user:
                self._json(401, {"error": "请先登录"})
                return
            rel = path[len("/files/"):]
            fp = os.path.normpath(os.path.join(UPLOAD_DIR, rel))
            if not fp.startswith(UPLOAD_DIR):
                self._json(403, {"error": "forbidden"}); return
            try:
                os.remove(fp)
                self._json(200, {"deleted": True})
            except FileNotFoundError:
                self._json(404, {"error": "not found"})
            return

        self._json(404, {"error": "not found"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8888))
    server = ThreadingHTTPServer(("127.0.0.1", port), FileHandler)
    print(f"File+Admin server on http://127.0.0.1:{port}")
    server.serve_forever()
