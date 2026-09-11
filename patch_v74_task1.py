# -*- coding: utf-8 -*-
"""v74 任务1：登记租户 - 房间搜索/楼栋筛选 + PDF/Word(3M) 上传
原则：只做增量与显示层，不改任何现有业务数据流。"""
import io, sys

def patch(path, repls):
    with io.open(path, 'r', encoding='utf-8') as f:
        s = f.read()
    for old, new, cnt in repls:
        actual = s.count(old)
        if actual != cnt:
            print('FAIL [%s]: expect %d got %d' % (path, cnt, actual))
            print('--- anchor head:', old[:80].replace('\n', '\\n'))
            sys.exit(1)
        s = s.replace(old, new)
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(s)
    print('OK [%s]: %d hunks applied' % (path, len(repls)))

# ============ file_server.py ============
fs_old1 = """            ALLOWED_EXT = {'.jpg','.jpeg','.png','.gif','.webp','.bmp','.pdf','.heic','.heif'}
            if ext not in ALLOWED_EXT:
                self._json(400, {"error": "不支持的文件类型，仅允许图片和PDF"}); return
            length = int(self.headers.get("Content-Length", 0))
            if length > 20 * 1024 * 1024:
                self._json(413, {"error": "too large"}); return
            data = self.rfile.read(length)
            with open(target, "wb") as f:
                f.write(data)
            rel_path = "/".join(parts)"""
fs_new1 = """            DOC_EXT = {'.pdf','.doc','.docx'}
            ALLOWED_EXT = {'.jpg','.jpeg','.png','.gif','.webp','.bmp','.heic','.heif'} | DOC_EXT
            if ext not in ALLOWED_EXT:
                self._json(400, {"error": "不支持的文件类型，仅允许图片、PDF、Word"}); return
            # 合同文档(PDF/Word)单文件限3MB；图片等保持20MB不变
            size_limit = 3 * 1024 * 1024 if ext in DOC_EXT else 20 * 1024 * 1024
            # 合同类文件路径必须以本人用户ID开头(防越权写入他人目录;管理员不限)
            if parts[0] in ('contract-files','contract-photos'):
                owner_ok = (user["email"] in ADMIN_EMAILS) or (len(parts) >= 3 and parts[1] == user["uid"])
                if not owner_ok:
                    self._json(403, {"error": "forbidden"}); return
            length = int(self.headers.get("Content-Length", 0))
            if length > size_limit:
                self._json(413, {"error": "文件过大，合同文档请压缩到3MB以内"}); return
            # 分块流式写盘，避免整个文件读入内存
            remaining = length
            tmp_target = target + ".tmp"
            try:
                with open(tmp_target, "wb") as f:
                    while remaining > 0:
                        chunk = self.rfile.read(min(65536, remaining))
                        if not chunk:
                            break
                        f.write(chunk)
                        remaining -= len(chunk)
                os.replace(tmp_target, target)
            except Exception:
                try:
                    if os.path.exists(tmp_target):
                        os.remove(tmp_target)
                except Exception:
                    pass
                self._json(500, {"error": "save failed"}); return
            rel_path = "/".join(parts)"""

fs_old2 = """            rel = path[len("/files/"):]
            fp = os.path.normpath(os.path.join(UPLOAD_DIR, rel))
            if not fp.startswith(UPLOAD_DIR):
                self._json(403, {"error": "forbidden"}); return
            try:
                os.remove(fp)"""
fs_new2 = """            rel = path[len("/files/"):]
            fp = os.path.normpath(os.path.join(UPLOAD_DIR, rel))
            if not fp.startswith(UPLOAD_DIR):
                self._json(403, {"error": "forbidden"}); return
            # 合同类文件仅本人或管理员可删除(房间图片为全房东共用路径,维持登录可删)
            segs = [s for s in rel.split("/") if s]
            if segs and segs[0] in ("contract-files", "contract-photos"):
                is_owner = len(segs) >= 2 and segs[1] == user["uid"]
                if not is_owner and user["email"] not in ADMIN_EMAILS:
                    self._json(403, {"error": "无权删除他人文件"}); return
            try:
                os.remove(fp)"""

patch('file_server.py', [(fs_old1, fs_new1, 1), (fs_old2, fs_new2, 1)])

# ============ i18n.js ============
i18n_old_zh = '''    "tenant.max1File": "最多上传1个文件",'''
i18n_new_zh = '''    "tenant.max1File": "最多上传1个文件",
    "tenant.maxFiles": "最多上传10个文件",
    "tenant.delFileConfirm": "确定删除这个合同文件吗？",
    "tenant.roomSearch": "搜索房间",
    "tenant.roomSearchPh": "输入房号或楼栋名",'''
i18n_old_en = '''    "tenant.max1File": "Maximum 1 file",'''
i18n_new_en = '''    "tenant.max1File": "Maximum 1 file",
    "tenant.maxFiles": "Up to 10 files",
    "tenant.delFileConfirm": "Delete this contract file?",
    "tenant.roomSearch": "Search room",
    "tenant.roomSearchPh": "Room no. or building",'''
i18n_hint_zh = '''"common.fileHint": "支持 PDF、Word 格式，单个文件不超过 1MB，最多 1 个",'''
i18n_hint_zh_new = '''"common.fileHint": "支持 PDF、Word 格式，单个文件不超过 3MB，最多 10 个",'''
i18n_hint_en = '''"common.fileHint": "Supports PDF, Word format; max 1MB; up to 1 file",'''
i18n_hint_en_new = '''"common.fileHint": "Supports PDF, Word; each file up to 3MB; up to 10 files",'''

patch('i18n.js', [
    (i18n_old_zh, i18n_new_zh, 1),
    (i18n_old_en, i18n_new_en, 1),
    (i18n_hint_zh, i18n_hint_zh_new, 1),
    (i18n_hint_en, i18n_hint_en_new, 1),
])

print('phase1 done')
