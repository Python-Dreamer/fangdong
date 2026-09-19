#!/bin/bash
# v95 部署脚本：房间照片修复 + 留言举报 + 品牌名瑞丽->德宏
# 重要：本版需要【数据库建新表】+【更新后端 file_server.py】，必须用 root 运行！
#   用法：先 sudo -i 切到 root，再 bash deploy_v95.sh
# 前端静态文件：app.html / sw.js / whatsnew.html / match.html / index.html
# 数据库：listing_reports 表（租房页匿名举报，仅后端可读写，前端无权直连）
# 后端：file_server.py 新增 匿名举报提交 / 管理员查看 / 管理员处理 三个接口
#
# 设计：不 set -e，任何一步失败都打印并继续，最后汇总；下载/校验不过绝不碰站点、后端和数据库。

SITE=/www/wwwroot/ruilifangfong.site
BAK=/tmp/fangdong_v95_bak_$(date +%Y%m%d_%H%M%S)
BASE="https://raw.githubusercontent.com/Python-Dreamer/fangdong/main"
MIRROR="https://ghfast.top/https://raw.githubusercontent.com/Python-Dreamer/fangdong/main"
SQL_REL="supabase/migrations/20260920000000_listing_reports.sql"

echo "================================================"
echo "  v95 部署：照片修复 + 留言举报 + 德宏品牌名"
echo "  站点目录: $SITE"
echo "  备份目录: $BAK"
echo "================================================"

if [ "$(id -u)" != "0" ]; then
  echo "❌ 请先用 root 运行：执行 sudo -i 切换到 root 后，再 bash 本脚本"
  exit 1
fi

mkdir -p "$BAK"
WORK=/tmp/fangdong_v95_dl
rm -rf "$WORK"; mkdir -p "$WORK"

download() {
  local rel="$1" out="$2"
  wget -q --timeout=20 --tries=2 "$BASE/$rel" -O "$out" && [ -s "$out" ] && return 0
  echo "   官方源失败，尝试镜像: $rel"
  wget -q --timeout=30 --tries=2 "$MIRROR/$rel" -O "$out" && [ -s "$out" ] && return 0
  return 1
}

echo ""
echo "【1/6】下载文件..."
OK=1
for f in app.html sw.js whatsnew.html match.html index.html; do
  if download "$f" "$WORK/$f"; then echo "   ✅ $f"; else echo "   ❌ $f 下载失败"; OK=0; fi
done
if download "file_server.py" "$WORK/file_server.py"; then echo "   ✅ file_server.py"; else echo "   ❌ file_server.py 下载失败"; OK=0; fi
if download "$SQL_REL" "$WORK/listing_reports.sql"; then echo "   ✅ listing_reports.sql"; else echo "   ❌ listing_reports.sql 下载失败"; OK=0; fi

if [ "$OK" != "1" ]; then
  echo ""
  echo "❌ 有文件下载失败，已中止，站点/后端/数据库均未改动。"
  echo "   可检查网络后重试，或改用宝塔面板手动上传。"
  exit 1
fi

# ---------- 2. 校验文件关键特征 ----------
echo ""
echo "【2/6】校验文件内容..."
PASS=1
grep -q "foldDupBucket" "$WORK/app.html" || { echo "   ❌ app.html 缺少照片双桶名修复"; PASS=0; }
grep -q "fangdong-v95" "$WORK/sw.js" || { echo "   ❌ sw.js 版本不是 v95"; PASS=0; }
grep -q "function rReports" "$WORK/app.html" || { echo "   ❌ app.html 缺少举报管理页"; PASS=0; }
grep -q "upload/report" "$WORK/file_server.py" || { echo "   ❌ file_server.py 缺少举报接口"; PASS=0; }
grep -q "CREATE TABLE IF NOT EXISTS listing_reports" "$WORK/listing_reports.sql" || { echo "   ❌ SQL 缺少 listing_reports 建表"; PASS=0; }
grep -q "德宏" "$WORK/match.html" || { echo "   ❌ match.html 未更新为德宏"; PASS=0; }
python3 -m py_compile "$WORK/file_server.py" 2>/dev/null || { echo "   ❌ file_server.py 语法异常"; PASS=0; }

if [ "$PASS" != "1" ]; then
  echo ""
  echo "❌ 文件校验未通过，已中止，未做任何改动。"
  exit 1
fi
echo "   ✅ 全部关键特征校验通过"

# ---------- 3. 建数据库表 ----------
echo ""
echo "【3/6】创建数据库表 listing_reports ..."
if docker ps --format '{{.Names}}' | grep -q "^fd_db$"; then
  if docker exec -i fd_db psql -U postgres -d postgres < "$WORK/listing_reports.sql"; then
    echo "   ✅ listing_reports 表就绪（幂等，可重复执行）"
  else
    echo "   ❌ 建表失败，已中止前端/后端更新。"
    exit 1
  fi
else
  echo "   ⚠️ 未找到 fd_db 容器，跳过建表。举报功能需先手动执行："
  echo "      docker exec -i fd_db psql -U postgres -d postgres < $WORK/listing_reports.sql"
  echo "   本次先继续更新前端和后端，但举报在表建好前会提示错误（不影响其他功能）。"
fi

# ---------- 4. 更新前端静态文件 ----------
echo ""
echo "【4/6】更新前端静态文件..."
for f in app.html sw.js whatsnew.html match.html index.html; do
  if [ -f "$SITE/$f" ]; then cp "$SITE/$f" "$BAK/$f.bak"; fi
  cp "$WORK/$f" "$SITE/$f" && echo "   ✅ $f"
done

# ---------- 5. 更新后端并重启 ----------
echo ""
echo "【5/6】更新后端 file_server.py ..."
if [ -f /opt/fangdong/bin/file_server.py ]; then
  cp /opt/fangdong/bin/file_server.py "$BAK/file_server.py.bak"
  if cp "$WORK/file_server.py" /opt/fangdong/bin/file_server.py; then
    if python3 -m py_compile /opt/fangdong/bin/file_server.py; then
      systemctl restart fangdong-files && echo "   ✅ fangdong-files 服务已重启"
    else
      echo "   ⚠️ 后端语法异常，已自动回滚后端"
      cp "$BAK/file_server.py.bak" /opt/fangdong/bin/file_server.py
      systemctl restart fangdong-files
    fi
  fi
else
  echo "   ⚠️ 未找到 /opt/fangdong/bin/file_server.py，跳过后端更新（举报接口将不可用）。"
fi

# ---------- 6. 验证 ----------
echo ""
echo "【6/6】验证线上..."
sleep 2
code=$(curl -s -o /dev/null -w "%{http_code}" -m 10 -X POST https://ruilifangfong.site/upload/report -H "Content-Type: application/json" -d '{}')
if [ "$code" = "400" ]; then
  echo "   ✅ 举报接口已在线（空提交返回400参数校验，符合预期）"
else
  echo "   ⚠️ 举报接口自检返回 HTTP $code（预期400）。可稍后手动重试，或检查 fangdong-files 日志。"
fi

echo ""
echo "================================================"
echo "  v95 部署完成"
echo "  备份目录: $BAK"
echo "  回滚: cp $BAK/<文件> 对应目录 后 systemctl restart fangdong-files"
echo "  手机请强刷/清缓存一次（或关闭后台重开），sw 会自动升级到 v95"
echo "================================================"
