#!/usr/bin/env bash
# ============================================================
# v96 一键部署：修复 3 个问题
#   1) 举报提交失败 → 修复 service_role 对 listing_reports 的写权限
#   2) 房东端"瑞丽"品牌词 → 德宏（坐标/真实地名保留）
#   3) 后端举报失败改为日志记录，不再返回 {} 给用户
# 幂等、可重复执行；后端会先备份，失败自动回滚
# 用法：先 sudo -i，再 bash deploy_v96.sh
# ============================================================
set -uo pipefail

GH="https://ghfast.top/https://raw.githubusercontent.com/Python-Dreamer/fangdong/main"
SITE="/www/wwwroot/ruilifangfong.site"
BIN="/opt/fangdong/bin"
WORK="$(mktemp -d /tmp/v96.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

PASS=1

download(){ # url dest
  if wget -q --timeout=30 --tries=2 "$1" -O "$2" && [ -s "$2" ]; then return 0; fi
  return 1
}

echo "【1/5】下载文件 ..."
FILES=(
  "app.html|app.html"
  "sw.js|sw.js"
  "i18n.js|i18n.js"
  "file_server.py|file_server.py"
  "image_compress.html|image_compress.html"
  "image_converter.html|image_converter.html"
  "services.html|services.html"
  "tools.html|tools.html"
  "supabase/fix_report_privileges.sql|fix_priv.sql"
)
for it in "${FILES[@]}"; do
  src="${it%%|*}"; dst="${it##*|}"
  if download "$GH/$src" "$WORK/$dst"; then echo "   ✅ $dst"; else echo "   ❌ $dst"; PASS=0; fi
done
[ "$PASS" -eq 1 ] || { echo "❌ 有文件下载失败，请稍后重试（GitHub代理偶发超时）"; exit 1; }

echo "【2/5】校验 ..."
python3 -m py_compile "$WORK/file_server.py" || { echo "❌ file_server.py 语法错误"; exit 1; }
echo "   ✅ file_server.py 语法 OK"

echo "【3/5】修复举报写权限（自适应，幂等）..."
if docker ps --format '{{.Names}}' | grep -q "^fd_db$"; then
  if docker exec -i fd_db psql -U postgres -d postgres < "$WORK/fix_priv.sql"; then
    echo "   ✅ listing_reports 写权限已修复"
  else
    echo "   ❌ 授权SQL执行失败"; exit 1
  fi
else
  echo "   ⚠️ 未找到 fd_db 容器，跳过授权（举报可能仍无法提交）"
fi

echo "【4/5】更新后端 file_server.py（先备份，失败回滚）..."
mkdir -p "$BIN"
[ -f "$BIN/file_server.py" ] && cp -a "$BIN/file_server.py" "$BIN/file_server.py.bak.$(date +%s)"
cp "$WORK/file_server.py" "$BIN/file_server.py"
if systemctl restart fangdong-files && sleep 1 && systemctl is-active --quiet fangdong-files; then
  echo "   ✅ fangdong-files 已重启并运行"
else
  echo "   ⚠️ 重启失败，尝试回滚后端 ..."
  BAK="$(ls -t $BIN/file_server.py.bak.* 2>/dev/null | head -1)"
  [ -n "$BAK" ] && cp "$BAK" "$BIN/file_server.py" && systemctl restart fangdong-files
  echo "   已回滚，请把 journalctl -u fangdong-files -n 30 发我"; exit 1
fi

echo "【5/5】更新前端文件 ..."
mkdir -p "$SITE"
for f in app.html sw.js i18n.js image_compress.html image_converter.html services.html tools.html; do
  cp "$WORK/$f" "$SITE/$f"
done
echo "   ✅ 前端已更新（app/sw/i18n/3个工具页/找服务）"

echo
echo "================ v96 部署完成 ================"
echo "手机请强刷或关闭后台重开。"
echo "自检举报接口（应返回 400 缺少房源信息，说明服务在线）："
curl -sS -m 10 -X POST "https://ruilifangfong.site/upload/report" \
  -H "Content-Type: application/json" -d '{}' -w "\nHTTP %{http_code}\n"
echo "============================================="
