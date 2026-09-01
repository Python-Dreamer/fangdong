"""
每日综合提醒脚本（缴费 + 生日，邮件+微信推送）
- 查询所有设置了notification_email的房东
- 查询每个房东的租户中即将到期/逾期的账单
- 查询每个房东的生日台账中即将到来的生日（支持农历/公历）
- 生成合并提醒并通过QQ SMTP发送邮件
- 同时通过PushPlus推送微信消息
"""
import json, os, sys, smtplib, urllib.request, urllib.parse, time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SB_URL = "https://ruilifangfong.site"
SB_KEY = "eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJpc3MiOiAic3VwYWJhc2UiLCAicmVmIjogImZhbmdkb25nLWxvY2FsIiwgInJvbGUiOiAic2VydmljZV9yb2xlIiwgImlhdCI6IDE3ODYwMzg4OTEsICJleHAiOiAyMTAxMzk4ODkxfQ.1abYjQ22lj38I02Ki6XZXFNo9IOZJnKaH4pdLEqW25Q"

# QQ邮箱SMTP配置
SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 587
SMTP_USER = "332303155@qq.com"
SMTP_AUTH = "yjdhoaxqlfocbhhe"

# PushPlus微信推送配置
PUSHPLUS_URL = "https://www.pushplus.plus/send/"

# 生日提醒窗口（提前N天提醒）
BIRTHDAY_REMIND_DAYS = 7

HEADERS = {
    "apikey": SB_KEY,
    "Authorization": f"Bearer {SB_KEY}",
    "Content-Type": "application/json"
}

# ========== 农历转换核心 ==========
lunarInfo = [
    0x04bd8,0x04ae0,0x0a570,0x054d5,0x0d260,0x0d950,0x16554,0x056a0,0x09ad0,0x055d2,
    0x04ae0,0x0a5b6,0x0a4d0,0x0d250,0x1d255,0x0b540,0x0d6a0,0x0ada2,0x095b0,0x14977,
    0x04970,0x0a4b0,0x0b4b5,0x06a50,0x06d40,0x1ab54,0x02b60,0x09570,0x052f2,0x04970,
    0x06566,0x0d4a0,0x0ea50,0x06e95,0x05ad0,0x02b60,0x186e3,0x092e0,0x1c8d7,0x0c950,
    0x0d4a0,0x1d8a6,0x0b550,0x056a0,0x1a5b4,0x025d0,0x092d0,0x0d2b2,0x0a950,0x0b557,
    0x06ca0,0x0b550,0x15355,0x04da0,0x0a5b0,0x14573,0x052b0,0x0a9a8,0x0e950,0x06aa0,
    0x0aea6,0x0ab50,0x04b60,0x0aae4,0x0a570,0x05260,0x0f263,0x0d950,0x05b57,0x056a0,
    0x096d0,0x04dd5,0x04ad0,0x0a4d0,0x0d4d4,0x0d250,0x0d558,0x0b540,0x0b6a0,0x195a6,
    0x095b0,0x049b0,0x0a974,0x0a4b0,0x0b27a,0x06a50,0x06d40,0x0af46,0x0ab60,0x09570,
    0x04af5,0x04970,0x064b0,0x074a3,0x0ea50,0x06b58,0x05ac0,0x0ab60,0x096d5,0x092e0,
    0x0c960,0x0d954,0x0d4a0,0x0da50,0x07552,0x056a0,0x0abb7,0x025d0,0x092d0,0x0cab5,
    0x0a950,0x0b4a0,0x0baa4,0x0ad50,0x055d9,0x04ba0,0x0a5b0,0x15176,0x052b0,0x0a930,
    0x07954,0x06aa0,0x0ad50,0x05b52,0x04b60,0x0a6e6,0x0a4e0,0x0d260,0x0ea65,0x0d530,
    0x05aa0,0x076a3,0x096d0,0x04afb,0x04ad0,0x0a4d0,0x1d0b6,0x0d250,0x0d520,0x0dd45,
    0x0b5a0,0x056d0,0x055b2,0x049b0,0x0a577,0x0a4b0,0x0aa50,0x1b255,0x06d20,0x0ada0,
    0x14b63,0x09370,0x049f8,0x04970,0x064b0,0x168a6,0x0ea50,0x06b20,0x1a6c4,0x0aae0,
    0x092e0,0x0d2e3,0x0c960,0x0d557,0x0d4a0,0x0da50,0x05d55,0x056a0,0x0a6d0,0x055d4,
    0x052d0,0x0a9b8,0x0a950,0x0b4a0,0x0b6a6,0x0ad50,0x055a0,0x0aba4,0x0a5b0,0x052b0,
    0x0b273,0x06930,0x07337,0x06aa0,0x0ad50,0x14b55,0x04b60,0x0a570,0x054e4,0x0d160,
    0x0e968,0x0d520,0x0daa0,0x16aa6,0x056d0,0x04ae0,0x0a9d4,0x0a4d0,0x0d150,0x0f252,
    0x0d520
]

def leapMonth(y): return lunarInfo[y-1900] & 0xf
def leapDays(y):
    if leapMonth(y): return 30 if (lunarInfo[y-1900] & 0x10000) else 29
    return 0
def monthDays(y,m): return 30 if (lunarInfo[y-1900] & (0x10000 >> m)) else 29
def yearDays(y):
    s = 348
    for i in [0x8000,0x4000,0x2000,0x1000,0x800,0x400,0x200,0x100,0x80,0x40,0x20,0x10]:
        s += 1 if (lunarInfo[y-1900] & i) else 0
    return s + leapDays(y)

def lunarToSolarDate(y,m,d):
    """农历转公历，返回date对象"""
    offset = 0
    for i in range(1900, y):
        offset += yearDays(i)
    lm = leapMonth(y)
    for i in range(1, m):
        if i == lm: offset += leapDays(y)
        offset += monthDays(y, i)
    offset += d - 1
    base = datetime(1900, 1, 31).date()
    return base + timedelta(days=offset)

lunarMonthNames = ['正','二','三','四','五','六','七','八','九','十','冬','腊']
lunarDayNames = ['初一','初二','初三','初四','初五','初六','初七','初八','初九','初十',
    '十一','十二','十三','十四','十五','十六','十七','十八','十九','二十',
    '廿一','廿二','廿三','廿四','廿五','廿六','廿七','廿八','廿九','三十']

def formatLunar(m, d):
    return f"农历{lunarMonthNames[m-1]}月{lunarDayNames[d-1]}"

def getNextBirthdayDate(b, today):
    """计算下一个生日的公历日期"""
    year = today.year
    if b.get('type') == 'solar':
        try:
            this_year = datetime(year, b['solarMonth'], b['solarDay']).date()
        except: return None
    else:
        try:
            this_year = lunarToSolarDate(year, b['lunarMonth'], b['lunarDay'])
        except: return None

    if this_year >= today:
        return this_year

    # 今年已过，算明年
    next_year = year + 1
    if b.get('type') == 'solar':
        try:
            return datetime(next_year, b['solarMonth'], b['solarDay']).date()
        except: return None
    else:
        try:
            return lunarToSolarDate(next_year, b['lunarMonth'], b['lunarDay'])
        except: return None

# ========== HTTP / 邮件 / 推送 ==========
def today_str():
    return datetime.now().strftime("%Y-%m-%d")

def http_get(url, params=None, max_retries=3, retry_delay=5):
    original_url = url
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except (ConnectionRefusedError, urllib.error.URLError, OSError) as e:
            if attempt < max_retries - 1:
                print(f"Network error (attempt {attempt+1}/{max_retries}): {e}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print(f"Network error after {max_retries} attempts: {e}")
                raise

def send_reminder_email(to_email, subject, body_html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    html_part = MIMEText(body_html, "html", "utf-8")
    msg.attach(html_part)
    for attempt in range(3):
        try:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
            server.starttls()
            server.login(SMTP_USER, SMTP_AUTH)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
            server.quit()
            return True, "OK"
        except (ConnectionRefusedError, OSError, smtplib.SMTPException) as e:
            if attempt < 2:
                time.sleep(5)
            else:
                return False, str(e)
        except Exception as e:
            return False, str(e)

def send_pushplus(token, title, content, max_retries=3, retry_delay=5):
    payload = json.dumps({
        "token": token, "title": title, "content": content, "template": "html"
    }).encode("utf-8")
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(PUSHPLUS_URL, data=payload,
                headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode())
                if result.get("code") == 200:
                    return True, "OK"
                return False, result.get("msg", "Unknown error")
        except (ConnectionRefusedError, urllib.error.URLError, OSError) as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                return False, str(e)
        except Exception as e:
            return False, str(e)

# ========== 生日数据获取 ==========
def fetch_birthdays(owner_id):
    """从国内数据库birthday_book表获取用户的生日数据"""
    try:
        rows = http_get(f"{SB_URL}/rest/v1/birthday_book", {
            "select": "name,type,solar_month,solar_day,lunar_month,lunar_day",
            "owner_id": f"eq.{owner_id}"
        })
        result = []
        for r in rows:
            b = {"name": r["name"], "type": r["type"]}
            if r["type"] == "solar":
                b["solarMonth"] = r["solar_month"]
                b["solarDay"] = r["solar_day"]
            else:
                b["lunarMonth"] = r["lunar_month"]
                b["lunarDay"] = r["lunar_day"]
            result.append(b)
        return result
    except:
        return []

def get_upcoming_birthdays(owner_id, today, remind_days=BIRTHDAY_REMIND_DAYS):
    """获取即将到来的生日列表"""
    birthdays = fetch_birthdays(owner_id)
    upcoming = []
    for b in birthdays:
        next_date = getNextBirthdayDate(b, today)
        if next_date is None:
            continue
        days = (next_date - today).days
        if 0 <= days <= remind_days:
            # 构造显示名称
            if b.get('type') == 'solar':
                orig = f"{b['solarMonth']}月{b['solarDay']}日"
            else:
                orig = formatLunar(b['lunarMonth'], b['lunarDay'])
            upcoming.append({
                'name': b['name'],
                'original': orig,
                'type': b.get('type', 'solar'),
                'next_date': next_date,
                'days_until': days
            })
    upcoming.sort(key=lambda x: x['days_until'])
    return upcoming

# ========== 构建提醒内容 ==========
def build_wechat_html(owner_name, overdue, upcoming, birthdays, adjustments=None):
    adjustments = adjustments or []
    today = today_str()
    parts = []
    parts.append(f'<div style="font-size:14px;line-height:1.6;">')
    parts.append(f'<h3 style="color:#2c3e50;margin:0 0 10px 0;">每日提醒 - {today}</h3>')
    parts.append(f'<p>房东 <strong>{owner_name}</strong>，您好：</p>')

    # 缴费部分
    if overdue or upcoming:
        parts.append(f'<hr style="border:none;border-top:1px solid #eee;margin:10px 0;">')
        parts.append(f'<h4 style="color:#e74c3c;margin:0 0 8px 0;">缴费提醒</h4>')
        if overdue:
            parts.append(f'<p style="color:#e74c3c;font-weight:bold;margin:5px 0;">已逾期（{len(overdue)}笔）</p>')
            parts.append('<div style="background:#fff5f5;padding:8px;border-radius:4px;">')
            for r in overdue:
                parts.append(f'<p style="margin:3px 0;">{r["tenant_name"]} · {r.get("room_name","-")} · ¥{r["amount"]} · <span style="color:#e74c3c;font-weight:bold;">逾期{r.get("overdue_days",0)}天</span></p>')
            parts.append('</div>')
        if upcoming:
            parts.append(f'<p style="color:#f39c12;font-weight:bold;margin:8px 0 5px 0;">即将到期（{len(upcoming)}笔）</p>')
            parts.append('<div style="background:#fffdf5;padding:8px;border-radius:4px;">')
            for r in upcoming:
                parts.append(f'<p style="margin:3px 0;">{r["tenant_name"]} · {r.get("room_name","-")} · ¥{r["amount"]} · 还有{r["days_until"]}天</p>')
            parts.append('</div>')
    else:
        parts.append(f'<hr style="border:none;border-top:1px solid #eee;margin:10px 0;">')
        parts.append(f'<h4 style="color:#e74c3c;margin:0 0 8px 0;">缴费提醒</h4>')
        parts.append('<p style="color:#27ae60;">所有租户均已按时缴费！</p>')

    # 生日部分
    if birthdays:
        parts.append(f'<hr style="border:none;border-top:1px solid #eee;margin:10px 0;">')
        parts.append(f'<h4 style="color:#e91e63;margin:0 0 8px 0;">生日提醒</h4>')
        parts.append('<div style="background:#fce4ec;padding:8px;border-radius:4px;">')
        for b in birthdays:
            tag = '公历' if b['type'] == 'solar' else '农历'
            date_str = b['next_date'].strftime('%Y年%m月%d日')
            if b['days_until'] == 0:
                parts.append(f'<p style="margin:3px 0;"><strong>🎂 {b["name"]}</strong> · {tag} · <span style="color:#e91e63;font-weight:bold;">今天生日！</span></p>')
            elif b['days_until'] == 1:
                parts.append(f'<p style="margin:3px 0;"><strong>🎂 {b["name"]}</strong> · {tag} · {b["original"]} → {date_str} · <span style="color:#e91e63;font-weight:bold;">明天</span></p>')
            else:
                parts.append(f'<p style="margin:3px 0;"><strong> {b["name"]}</strong> · {tag} · {b["original"]} → {date_str} · 还有{b["days_until"]}天</p>')
        parts.append('</div>')

    # 调租提醒部分
    if adjustments:
        parts.append(f'<hr style="border:none;border-top:1px solid #eee;margin:10px 0;">')
        parts.append(f'<h4 style="color:#8e44ad;margin:0 0 8px 0;">⏰ 调租提醒</h4>')
        parts.append('<div style="background:#f5eefc;padding:8px;border-radius:4px;">')
        for a in adjustments:
            amt = f'+¥{a["amount"]}' if a.get('direction') == 'increase' else f'-¥{a["amount"]}'
            color = '#e74c3c' if a.get('direction') == 'increase' else '#27ae60'
            d = a['days_until']
            if d < 0:
                stat = f'<span style="color:#e74c3c;font-weight:bold;">已到期{abs(d)}天</span>'
            elif d == 0:
                stat = '<span style="color:#e74c3c;font-weight:bold;">今天到期</span>'
            else:
                stat = f'还有{d}天'
            note = f' · {a["note"]}' if a.get('note') else ''
            parts.append(f'<p style="margin:3px 0;">{a["tenant_name"]} · {a.get("room_name","-")} · <span style="color:{color};font-weight:bold;">{amt}</span> · {a["adjust_date"]} · {stat}{note}</p>')
        parts.append('</div>')

    parts.append('<p style="color:#999;font-size:12px;margin-top:15px;">瑞丽租房管理系统</p>')
    parts.append('</div>')
    return ''.join(parts)

def build_email_html(owner_name, overdue, upcoming, birthdays, adjustments=None):
    adjustments = adjustments or []
    today = today_str()
    parts = []
    parts.append(f'<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">')
    parts.append(f'<h2 style="color:#2c3e50;">每日提醒 - {today}</h2>')
    parts.append(f'<p>房东 <strong>{owner_name}</strong>，您好！</p>')

    # 缴费部分
    parts.append('<h3 style="color:#e74c3c;border-bottom:2px solid #e74c3c;padding-bottom:5px;">缴费提醒</h3>')
    if overdue:
        parts.append('<h4 style="color:#e74c3c;">已逾期</h4><table style="width:100%;border-collapse:collapse;">')
        parts.append('<tr style="background:#f8d7da;"><th style="border:1px solid #ddd;padding:8px;">租客</th><th style="border:1px solid #ddd;padding:8px;">房间</th><th style="border:1px solid #ddd;padding:8px;">金额</th><th style="border:1px solid #ddd;padding:8px;">逾期天数</th><th style="border:1px solid #ddd;padding:8px;">缴租日</th></tr>')
        for r in overdue:
            parts.append(f'<tr><td style="border:1px solid #ddd;padding:8px;">{r["tenant_name"]}</td><td style="border:1px solid #ddd;padding:8px;">{r.get("room_name","-")}</td><td style="border:1px solid #ddd;padding:8px;">¥{r["amount"]}</td><td style="border:1px solid #ddd;padding:8px;color:#e74c3c;font-weight:bold;">{r.get("overdue_days",0)}天</td><td style="border:1px solid #ddd;padding:8px;">{r.get("period_start","-")}</td></tr>')
        parts.append('</table><br>')
    if upcoming:
        parts.append('<h4 style="color:#f39c12;">即将到期</h4><table style="width:100%;border-collapse:collapse;">')
        parts.append('<tr style="background:#fff3cd;"><th style="border:1px solid #ddd;padding:8px;">租客</th><th style="border:1px solid #ddd;padding:8px;">房间</th><th style="border:1px solid #ddd;padding:8px;">金额</th><th style="border:1px solid #ddd;padding:8px;">缴租日</th><th style="border:1px solid #ddd;padding:8px;">状态</th></tr>')
        for r in upcoming:
            parts.append(f'<tr><td style="border:1px solid #ddd;padding:8px;">{r["tenant_name"]}</td><td style="border:1px solid #ddd;padding:8px;">{r.get("room_name","-")}</td><td style="border:1px solid #ddd;padding:8px;">¥{r["amount"]}</td><td style="border:1px solid #ddd;padding:8px;">{r.get("period_start","-")}</td><td style="border:1px solid #ddd;padding:8px;"><span style="color:#f39c12;">还有{r["days_until"]}天</span></td></tr>')
        parts.append('</table><br>')
    if not overdue and not upcoming:
        parts.append('<p style="color:#27ae60;">所有租户均已按时缴费！</p><br>')

    # 生日部分
    if birthdays:
        parts.append('<h3 style="color:#e91e63;border-bottom:2px solid #e91e63;padding-bottom:5px;">生日提醒</h3>')
        parts.append('<table style="width:100%;border-collapse:collapse;">')
        parts.append('<tr style="background:#fce4ec;"><th style="border:1px solid #ddd;padding:8px;">姓名</th><th style="border:1px solid #ddd;padding:8px;">类型</th><th style="border:1px solid #ddd;padding:8px;">生日</th><th style="border:1px solid #ddd;padding:8px;">公历日期</th><th style="border:1px solid #ddd;padding:8px;">倒计时</th></tr>')
        for b in birthdays:
            tag = '公历' if b['type'] == 'solar' else '农历'
            date_str = b['next_date'].strftime('%Y-%m-%d')
            if b['days_until'] == 0:
                countdown = '<span style="color:#e91e63;font-weight:bold;">今天！</span>'
            elif b['days_until'] == 1:
                countdown = '<span style="color:#e91e63;font-weight:bold;">明天</span>'
            else:
                countdown = f'还有{b["days_until"]}天'
            parts.append(f'<tr><td style="border:1px solid #ddd;padding:8px;">{b["name"]}</td><td style="border:1px solid #ddd;padding:8px;">{tag}</td><td style="border:1px solid #ddd;padding:8px;">{b["original"]}</td><td style="border:1px solid #ddd;padding:8px;">{date_str}</td><td style="border:1px solid #ddd;padding:8px;">{countdown}</td></tr>')
        parts.append('</table><br>')
    else:
        parts.append('<h3 style="color:#e91e63;border-bottom:2px solid #e91e63;padding-bottom:5px;">生日提醒</h3>')
        parts.append('<p style="color:#999;">近期没有即将到来的生日</p><br>')

    # 调租提醒部分
    if adjustments:
        parts.append('<h3 style="color:#8e44ad;border-bottom:2px solid #8e44ad;padding-bottom:5px;">⏰ 调租提醒</h3>')
        parts.append('<table style="width:100%;border-collapse:collapse;">')
        parts.append('<tr style="background:#f5eefc;"><th style="border:1px solid #ddd;padding:8px;">租客</th><th style="border:1px solid #ddd;padding:8px;">房间</th><th style="border:1px solid #ddd;padding:8px;">调整</th><th style="border:1px solid #ddd;padding:8px;">生效日期</th><th style="border:1px solid #ddd;padding:8px;">状态</th><th style="border:1px solid #ddd;padding:8px;">备注</th></tr>')
        for a in adjustments:
            amt = f'+¥{a["amount"]}' if a.get('direction') == 'increase' else f'-¥{a["amount"]}'
            color = '#e74c3c' if a.get('direction') == 'increase' else '#27ae60'
            d = a['days_until']
            if d < 0:
                stat = f'<span style="color:#e74c3c;font-weight:bold;">已到期{abs(d)}天</span>'
            elif d == 0:
                stat = '<span style="color:#e74c3c;font-weight:bold;">今天到期</span>'
            else:
                stat = f'还有{d}天'
            parts.append(f'<tr><td style="border:1px solid #ddd;padding:8px;">{a["tenant_name"]}</td><td style="border:1px solid #ddd;padding:8px;">{a.get("room_name","-")}</td><td style="border:1px solid #ddd;padding:8px;color:{color};font-weight:bold;">{amt}</td><td style="border:1px solid #ddd;padding:8px;">{a["adjust_date"]}</td><td style="border:1px solid #ddd;padding:8px;">{stat}</td><td style="border:1px solid #ddd;padding:8px;">{a.get("note") or "-"}</td></tr>')
        parts.append('</table><br>')

    parts.append('<p style="color:#666;font-size:12px;">此邮件由瑞丽租房管理系统自动发送</p></div>')
    return ''.join(parts)

def fetch_adjustments(owner_id, room_map):
    """查询待处理的租金调整计划（rent_adjustments表可能尚未建表，失败返回空）"""
    try:
        rows = http_get(f"{SB_URL}/rest/v1/rent_adjustments", {
            "select": "id,tenant_id,adjust_date,direction,amount,note,status",
            "owner_id": f"eq.{owner_id}",
            "status": "eq.pending"
        })
    except Exception as e:
        print(f"WARNING: rent_adjustments query failed: {e}")
        return []
    if not rows:
        return []
    # 关联租客名
    tenant_map = {}
    try:
        tlist = http_get(f"{SB_URL}/rest/v1/tenants", {
            "select": "id,name,status",
            "owner_id": f"eq.{owner_id}"
        })
        for t in (tlist or []):
            tenant_map[t["id"]] = t
    except Exception:
        pass
    result = []
    today_dt = datetime.strptime(today_str(), "%Y-%m-%d").date()
    for a in rows:
        t = tenant_map.get(a.get("tenant_id"))
        if t and t.get("status") == "inactive":
            continue
        try:
            adj_dt = datetime.strptime(a["adjust_date"], "%Y-%m-%d").date()
        except Exception:
            continue
        days_until = (adj_dt - today_dt).days
        if days_until > 7:
            continue
        a["tenant_name"] = t["name"] if t else "未知租客"
        a["room_name"] = room_map.get(t.get("room_id"), "-") if t else "-"
        a["days_until"] = days_until
        result.append(a)
    result.sort(key=lambda x: x["days_until"])
    return result

def check_pushplus_column():
    try:
        http_get(f"{SB_URL}/rest/v1/workspace_settings", {"select": "pushplus_token", "limit": "1"})
        return True
    except:
        return False

# ========== 主流程 ==========
def main():
    today = today_str()
    today_dt = datetime.strptime(today, "%Y-%m-%d").date()
    remind_days = 15

    has_pushplus = check_pushplus_column()
    if not has_pushplus:
        print("WARNING: pushplus_token column not found, WeChat push disabled")

    select_fields = "owner_id,notification_email,rent_remind_days,enable_reminders"
    if has_pushplus:
        select_fields += ",pushplus_token"

    settings = http_get(f"{SB_URL}/rest/v1/workspace_settings", {
        "select": select_fields,
        "notification_email": "not.is.null"
    })

    if not settings:
        print("NO_REMINDERS")
        return

    results = []
    email_results = []
    any_sent = False

    for s in settings:
        if not s.get("notification_email"):
            continue
        if s.get("enable_reminders") is False:
            continue

        owner_id = s["owner_id"]
        email = s["notification_email"]
        rdays = s.get("rent_remind_days") or remind_days

        # 获取房东名字
        owner_profiles = http_get(f"{SB_URL}/rest/v1/profiles", {
            "select": "name", "id": f"eq.{owner_id}"
        })
        owner_name = owner_profiles[0]["name"] if owner_profiles else "房东"
        if not owner_name: owner_name = "房东"

        # === 缴费数据 ===
        tenants = http_get(f"{SB_URL}/rest/v1/tenants", {
            "select": "id,name,room_id,rent_amount,pay_method,contract_end,status",
            "owner_id": f"eq.{owner_id}", "status": "eq.active"
        })

        overdue, upcoming = [], []
        room_map = {}
        if tenants:
            room_ids = set(t.get("room_id") for t in tenants if t.get("room_id"))
            for rid in room_ids:
                rooms = http_get(f"{SB_URL}/rest/v1/rooms", {"select": "id,name", "id": f"eq.{rid}"})
                if rooms: room_map[rid] = rooms[0]["name"]

            pending_rents = []
            for t in tenants:
                rents = http_get(f"{SB_URL}/rest/v1/rents", {
                    "select": "id,tenant_id,amount,period_start,due_date,status,pay_date",
                    "tenant_id": f"eq.{t['id']}", "status": "in.(pending,overdue)"
                })
                for r in rents:
                    r["tenant_name"] = t["name"]
                    r["room_name"] = room_map.get(t.get("room_id"), "未知房间")
                    pending_rents.append(r)

            for r in pending_rents:
                period_start = r.get("period_start", "") or ""
                if period_start and period_start < today:
                    try:
                        ps_dt = datetime.strptime(period_start, "%Y-%m-%d").date()
                        r["overdue_days"] = (today_dt - ps_dt).days
                    except: r["overdue_days"] = 0
                    overdue.append(r)
                elif period_start:
                    try:
                        ps_dt = datetime.strptime(period_start, "%Y-%m-%d").date()
                        days_until = (ps_dt - today_dt).days
                        if days_until <= rdays:
                            r["days_until"] = days_until
                            upcoming.append(r)
                    except: pass

            overdue.sort(key=lambda x: x.get("overdue_days", 0), reverse=True)
            upcoming.sort(key=lambda x: x.get("days_until", 999))

        # === 生日数据 ===
        birthdays = get_upcoming_birthdays(owner_id, today_dt, BIRTHDAY_REMIND_DAYS)

        # === 调租提醒数据 ===
        try:
            adjustments = fetch_adjustments(owner_id, room_map)
        except Exception as e:
            print(f"WARNING: fetch_adjustments failed: {e}")
            adjustments = []

        # 有任何提醒才发送
        if overdue or upcoming or birthdays or adjustments:
            any_sent = True

            # 微信推送标题
            wx_title_parts = []
            if overdue: wx_title_parts.append(f"{len(overdue)}笔逾期")
            if upcoming: wx_title_parts.append(f"{len(upcoming)}笔到期")
            if birthdays: wx_title_parts.append(f"{len(birthdays)}个生日")
            if adjustments: wx_title_parts.append(f"{len(adjustments)}个调租")
            wx_title = f"每日提醒 {today} - " + "，".join(wx_title_parts)

            # 构建内容
            wx_html = build_wechat_html(owner_name, overdue, upcoming, birthdays, adjustments)
            email_html = build_email_html(owner_name, overdue, upcoming, birthdays, adjustments)

            # 发邮件
            email_subject = f"【每日提醒】{today} - " + "，".join(wx_title_parts)
            ok, msg = send_reminder_email(email, email_subject, email_html)
            email_results.append({
                "to": email, "owner_id": owner_id, "owner_name": owner_name,
                "subject": email_subject, "success": ok, "msg": msg,
                "overdue_count": len(overdue), "upcoming_count": len(upcoming),
                "birthday_count": len(birthdays), "adjust_count": len(adjustments)
            })

            # PushPlus微信推送
            pushplus_token = s.get("pushplus_token", "") if has_pushplus else ""
            if pushplus_token:
                wx_ok, wx_msg = send_pushplus(pushplus_token, wx_title, wx_html)
                email_results[-1]["pushplus_success"] = wx_ok
                email_results[-1]["pushplus_msg"] = wx_msg
            else:
                email_results[-1]["pushplus_success"] = None
                email_results[-1]["pushplus_msg"] = "skipped"

            results.append({
                "email": email, "owner_id": owner_id,
                "overdue": overdue, "upcoming": upcoming, "birthdays": birthdays,
                "adjustments": adjustments
            })

    if any_sent:
        output = {"date": today, "reminders": results, "email_results": email_results}
        output_path = os.environ.get("OUTPUT_PATH", "./codeact/output")
        os.makedirs(output_path, exist_ok=True)
        fname = f"daily_reminder_{today}.json"
        with open(os.path.join(output_path, fname), "w") as f:
            json.dump(output, f, ensure_ascii=False, indent=2, default=str)
        print(f"REMINDER_DATA:{fname}")
    else:
        print("NO_REMINDERS")

if __name__ == "__main__":
    main()
