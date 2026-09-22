#!/usr/bin/env bash
# ============================================================
# v97 一键部署：新增「催租助手」
#   纯前端增量，不改后端、不改数据库表结构
#   - 三档分组（已逾期 / 今天到期 / 3天内到期）
#   - 一键生成话术 + 跳转微信
#   - 收款码上传（pay-qrcodes，复用现有文件服务）
#   - 已收款一键销账（复用 doQuickPay）
# 幂等、可重复执行
# 用法：先 sudo -i，再 bash deploy_v97.sh
# ============================================================
set -uo pipefail

GH="https://ghfast.top/https://raw.githubusercontent.com/Python-Dreamer/fangdong/main"
SITE="/www/wwwroot/ruilifangfong.site"
WORK="$(mktemp -d /tmp/v97.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

download(){
  wget -q --timeout=30 --tries=2 "$1" -O "$2" && [ -s "$2" ]
}

echo "【1/3】下载文件 ..."
FILES=(app.html sw.js i18n.js whatsnew.html)
PASS=1
for f in "${FILES[@]}"; do
  if download "$GH/$f" "$WORK/$f"; then echo "   ✅ $f"; else echo "   ❌ $f"; PASS=0; fi
done
[ "$PASS" -eq 1 ] || { echo "❌ 有文件下载失败，请稍后重试（GitHub代理偶发超时）"; exit 1; }

echo "【2/3】更新前端文件 ..."
mkdir -p "$SITE"
for f in "${FILES[@]}"; do cp "$WORK/$f" "$SITE/$f"; done
echo "   ✅ 前端已更新（app/sw/i18n/whatsnew）"

echo "【3/3】自检 ..."
code=$(curl -sS -m 10 -o /dev/null -w "%{http_code}" "https://ruilifangfong.site/app.html")
echo "   app.html HTTP $code"

echo
echo "================ v97 部署完成 ================"
echo "打开 App，侧边栏新增「📣 催租助手」。"
echo "手机请强刷或完全关闭后台重开；若仍显示旧版，退出微信重新进。"
echo "============================================="
