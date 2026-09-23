#!/usr/bin/env bash
set -e
cd /tmp
echo "【1/6】下载文件 ..."
BASE="https://ghfast.top/https://raw.githubusercontent.com/Python-Dreamer/fangdong/main"
W="/www/wwwroot/ruilifangfong.site"
mkdir -p "$W/vendor"
wget -q "$BASE/app.html"        -O app.html        && echo "✅ app.html"
wget -q "$BASE/sw.js"           -O sw.js           && echo "✅ sw.js"
wget -q "$BASE/i18n.js"         -O i18n.js         && echo "✅ i18n.js"
wget -q "$BASE/whatsnew.html"   -O whatsnew.html   && echo "✅ whatsnew.html"
wget -q "$BASE/vendor/zxing.min.js" -O zxing.min.js && echo "✅ vendor/zxing.min.js"
wget -q "$BASE/supabase/migrations/20260924000000_pay_qr_path.sql" -O pay_qr.sql && echo "✅ pay_qr.sql"

echo "【2/6】数据库补 pay_qr_path 列 ..."
docker exec -i fd_db psql -U postgres -d postgres < pay_qr.sql
docker exec -i fd_db psql -U postgres -d postgres -c "NOTIFY pgrst, 'reload schema';" >/dev/null
echo "✅ 列已就绪并已通知 PostgREST 重载"

echo "【3/6】更新前端 ..."
cp app.html "$W/app.html"
cp sw.js "$W/sw.js"
cp i18n.js "$W/i18n.js"
cp whatsnew.html "$W/whatsnew.html"
cp zxing.min.js "$W/vendor/zxing.min.js"
chmod 644 "$W/app.html" "$W/sw.js" "$W/i18n.js" "$W/whatsnew.html" "$W/vendor/zxing.min.js"
echo "✅ 前端已更新"

echo "【4/6】自检 ..."
sleep 1
curl -sS "https://ruilifangfong.site/vendor/zxing.min.js" -o /dev/null -w "zxing HTTP %{http_code}\n"
curl -sS "https://ruilifangfong.site/app.html" -o /dev/null -w "app HTTP %{http_code}\n"

echo "【5/6】清理 ..."
rm -f app.html sw.js i18n.js whatsnew.html zxing.min.js pay_qr.sql

echo "【6/6】完成"
echo "================ v98 部署完成 ================"
echo "手机请强刷或关闭后台重开。"
