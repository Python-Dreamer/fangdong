#!/bin/bash
# v81 部署脚本：登记只列空置房 + 员工子账号
# 重要：本版需要【数据库建表】+【更新后端 file_server.py】，必须用 root 运行！
#   步骤：先 sudo -i 切到 root，再 bash deploy_v81.sh
# 前端静态文件：app.html / i18n.js / sw.js / whatsnew.html
# 数据库：staff_accounts 表（员工登录账号关联 + 员工只读RLS）
# 后端：file_server.py 新增 /staff/create-account 接口（开通/启停员工账号）
#
# 设计：不 set -e，任何一步失败都打印并继续，最后汇总；下载/校验不过绝不碰站点和数据库。

SITE=/www/wwwroot/ruilifangfong.site
BAK=/tmp/fangdong_v81_bak_$(date +%Y%m%d_%H%M%S)
BASE="https://raw.githubusercontent.com/Python-Dreamer/fangdong/main"
MIRROR="https://ghfast.top/https://raw.githubusercontent.com/Python-Dreamer/fangdong/main"

echo "================================================"
echo "  v81 部署：空置房过滤 + 员工子账号"
echo "  站点目录: $SITE"
echo "  备份目录: $BAK"
echo "================================================"

if [ "$(id -u)" != "0" ]; then
  echo "❌ 请先用 root 运行：执行 sudo -i 切换到 root 后，再 bash 本脚本"
  exit 1
fi

mkdir -p "$BAK"
WORK=/tmp/fangdong_v81_dl
rm -rf "$WORK"; mkdir -p "$WORK"

# ---------- 1. 下载文件（官方源失败自动转镜像） ----------
download() {
  local rel="$1" out="$2"
  wget -q --timeout=20 --tries=2 "$BASE/$rel" -O "$out" && [ -s "$out" ] && return 0
  echo "   官方源失败，尝试镜像: $rel"
  wget -q --timeout=30 --tries=2 "$MIRROR/$rel" -O "$out" && [ -s "$out" ] && return 0
  return 1
}

echo ""
echo "【1/5】下载文件..."
OK=1
for f in app.html i18n.js sw.js whatsnew.html; do
  if download "$f" "$WORK/$f"; then echo "   ✅ $f"; else echo "   ❌ $f 下载失败"; OK=0; fi
done
# 后端与SQL
if download "file_server.py" "$WORK/file_server.py"; then echo "   ✅ file_server.py"; else echo "   ❌ file_server.py 下载失败"; OK=0; fi
if download "supabase/migrations/20260912000000_staff_accounts.sql" "$WORK/staff_accounts.sql"; then echo "   ✅ staff_accounts.sql"; else echo "   ❌ staff_accounts.sql 下载失败"; OK=0; fi

if [ "$OK" != "1" ]; then
  echo ""
  echo "❌ 有文件下载失败，已中止，站点和数据库均未改动。"
  echo "   可检查网络后重试，或改用宝塔面板手动上传。"
  exit 1
fi

# ---------- 2. 校验前端文件（关键特征必须存在） ----------
echo ""
echo "【2/5】校验文件内容..."
PASS=1
grep -q "fangdong-v81" "$WORK/sw.js" || { echo "   ❌ sw.js 版本不是 v81"; PASS=0; }
grep -q "i18n.js?v=81" "$WORK/app.html" || { echo "   ❌ app.html i18n引用不是 v81"; PASS=0; }
grep -q "roomOccToggleHtml" "$WORK/app.html" || { echo "   ❌ app.html 缺少空置房开关函数"; PASS=0; }
grep -q "renderStaffApp" "$WORK/app.html" || { echo "   ❌ app.html 缺少员工界面"; PASS=0; }
grep -q "staff_accounts" "$WORK/staff_accounts.sql" || { echo "   ❌ SQL 缺少 staff_accounts 表"; PASS=0; }
grep -q "staff/create-account" "$WORK/file_server.py" || { echo "   ❌ file_server.py 缺少员工开通接口"; PASS=0; }
grep -q "staff.openAccount" "$WORK/i18n.js" || { echo "   ❌ i18n.js 缺少员工文案"; PASS=0; }

if [ "$PASS" != "1" ]; then
  echo ""
  echo "❌ 文件校验未通过，已中止，站点和数据库均未改动。"
  exit 1
fi
echo "   ✅ 全部校验通过"

# ---------- 3. 备份并更新前端静态文件 ----------
echo ""
echo "【3/5】备份并更新前端文件..."
for f in app.html i18n.js sw.js whatsnew.html; do
  if [ -f "$SITE/$f" ]; then cp "$SITE/$f" "$BAK/$f"; fi
  cp "$WORK/$f" "$SITE/$f" && echo "   ✅ $f 已更新"
done

# ---------- 4. 更新后端 file_server.py 并重启服务 ----------
echo ""
echo "【4/5】更新后端 file_server.py..."
FS_OLD=""
if [ -f /opt/fangdong/bin/file_server.py ]; then
  FS_OLD=/opt/fangdong/bin/file_server.py
  cp "$FS_OLD" "$BAK/file_server.py.bak"
  cp "$WORK/file_server.py" "$FS_OLD" && echo "   ✅ file_server.py 已更新"
  # 语法检查
  if python3 -m py_compile "$FS_OLD"; then
    systemctl restart fangdong-files && echo "   ✅ fangdong-files 服务已重启"
  else
    echo "   ⚠️ file_server.py 语法异常，已回滚后端"
    cp "$BAK/file_server.py.bak" "$FS_OLD"
    systemctl restart fangdong-files
  fi
else
  echo "   ⚠️ 未找到 /opt/fangdong/bin/file_server.py，跳过后端更新（员工开通账号功能将不可用）"
fi

# ---------- 5. 数据库建表 + RLS ----------
echo ""
echo "【5/5】数据库执行 staff_accounts 建表..."
if docker ps --format '{{.Names}}' | grep -q "fd_db"; then
  if docker exec -i fd_db psql -U postgres -d postgres < "$WORK/staff_accounts.sql"; then
    echo "   ✅ staff_accounts 表与RLS策略已创建"
  else
    echo "   ❌ 数据库执行失败（脚本通常可重复执行，可重试；前端不受影响，员工账号功能需此表）"
  fi
else
  echo "   ⚠️ 未找到 fd_db 容器，跳过建表。请手动执行："
  echo "      docker exec -i fd_db psql -U postgres -d postgres < staff_accounts.sql"
fi

# ---------- 复核线上 ----------
echo ""
echo "================================================"
echo "  部署完成，复核线上版本："
curl -s "$SITE/sw.js" 2>/dev/null | grep -o "fangdong-v8[0-9]" | head -1
curl -s "https://ruilifangfong.site/sw.js" 2>/dev/null | grep -o "fangdong-v8[0-9]" | head -1
echo ""
echo "  备份位置: $BAK"
echo "  如发现问题，回滚命令：cp $BAK/<文件> $SITE/ 然后重启 fangdong-files"
echo "  员工请用老板开通的邮箱+密码登录；老板在「员工提成」页点「开通登录账号」。"
echo "================================================"
