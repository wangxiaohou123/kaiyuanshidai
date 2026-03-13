#!/bin/bash
# ============================================================
# 开元时代 · 自动产出沉淀 & GitHub 同步脚本
# 用途：每次班子汇报生成后调用此脚本完成归档+推送
# 用法：./auto-sync.sh "提交说明（可选）"
# ============================================================

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
DATE_LABEL=$(date '+%Y-%m-%d')
MSG="${1:-📋 班子产出自动归档 · $TIMESTAMP}"

cd "$REPO_DIR"

# ── 1. 检查是否有需要同步的改动 ──
CHANGED=$(git status --porcelain)
if [ -z "$CHANGED" ]; then
  echo "✅ 无新改动，本地与 GitHub 已同步"
  exit 0
fi

# ── 2. 分类统计变更 ──
NEW_REPORTS=$(git status --porcelain | grep -E "day[0-9]+-briefing|weekly-review|monthly-review" | wc -l | tr -d ' ')
MODIFIED_INDEX=$(git status --porcelain | grep "index.html" | wc -l | tr -d ' ')
echo "📊 检测到变更："
echo "   汇报文件：$NEW_REPORTS 个"
echo "   官网主页：$MODIFIED_INDEX 处"
git status --short

# ── 3. 全量暂存所有 HTML/MD 产出 ──
git add *.html *.md 2>/dev/null
git add knowledge/ 2>/dev/null

# ── 4. 自动生成结构化 commit 消息 ──
REPORT_LIST=$(git diff --cached --name-only | grep -E "briefing|review|report" | sed 's/^/  - /' | tr '\n' '\n')
AUTO_MSG="$MSG

变更文件概览:
$REPORT_LIST
自动归档时间: $TIMESTAMP"

git commit -m "$AUTO_MSG"

# ── 5. 更新知识库索引文件 ──
INDEX_FILE="$REPO_DIR/knowledge/reports-index.md"
mkdir -p "$(dirname "$INDEX_FILE")"
if [ ! -f "$INDEX_FILE" ]; then
  echo "# 开元时代 · 汇报产出索引" > "$INDEX_FILE"
  echo "" >> "$INDEX_FILE"
  echo "每次班子产出自动追加，最新在前。" >> "$INDEX_FILE"
  echo "" >> "$INDEX_FILE"
fi

# 追加新记录到索引（插入到第一条记录前）
ENTRY="- **$DATE_LABEL** | $MSG | [GitHub Pages](https://wangxiaohou123.github.io/kaiyuanshidai/)"
# 在 "最新在前" 那行后插入
sed -i '' "4a\\
$ENTRY
" "$INDEX_FILE" 2>/dev/null || \
  echo "$ENTRY" >> "$INDEX_FILE"

git add "$INDEX_FILE"
git commit -m "📚 更新汇报产出索引 · $DATE_LABEL" --no-verify 2>/dev/null || true

echo ""
echo "✅ 归档完成！"
echo "🌐 GitHub Pages: https://wangxiaohou123.github.io/kaiyuanshidai/"
