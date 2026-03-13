#!/bin/bash
# ====================================================
# 开元时代官网 · 一键自动部署脚本
# 用法：bash deploy.sh [提交说明]
# 示例：bash deploy.sh "更新Day4工作日志"
# ====================================================

cd "$(dirname "$0")"

COMMIT_MSG="${1:-自动更新: $(date '+%Y-%m-%d %H:%M')}"

echo "🔄 检查更新..."
CHANGED=$(git status --porcelain)

if [ -z "$CHANGED" ]; then
  echo "✅ 没有新变化，无需部署"
  exit 0
fi

echo "📦 暂存所有变更..."
git add -A

echo "💾 提交: $COMMIT_MSG"
git commit -m "$COMMIT_MSG"

echo "🚀 推送到 GitHub Pages..."
git push origin main

echo ""
echo "✅ 部署完成！"
echo "🌐 访问地址: https://wangxiaohou123.github.io/kaiyuanshidai/"
echo "🔗 短链接:   https://v.gd/OxO7yG"
