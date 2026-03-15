#!/usr/bin/env bash
# 开元时代 · CEO 反馈闭环 · 入口脚本
# 用法：bash check-feedback.sh
PYEXE="$HOME/Library/Application Support/xiaomei-cowork/Python311/python/bin/python3"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
"$PYEXE" "$SCRIPT_DIR/feedback-analyzer.py"
