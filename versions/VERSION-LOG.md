# 开元时代官网 · 版本历史

> 每次重要迭代后打快照，方便回退。
> 命名规则：`v{大版本}.{小版本}-{关键词}-{日期时间}.html`

---

## 版本记录

### v1.0 · 2026-03-13 15:52
- **文件**：`v1.0-theme-switcher-20260313-1552.html`
- **核心变更**：
  - 新增三套主题切换器（暗黑/珍珠白/暖沙色），导航栏右侧三圆点
  - localStorage 记忆用户主题偏好
  - 修复16处硬编码紫色 #B580E8 → CSS变量 --purple
  - 修复8处 rgba(185,128,232,...) 背景 → var(--purple-bg)
  - 全站0.3s平滑过渡动画
- **基于**：Day3 班子产出 + 工作日志倒序 + 导航修复版

---

## 回退方法

```bash
# 回退到某个版本（会覆盖当前 index.html）
cp ~/.xiaomei-workspace/yanglao-ceo-plan/versions/v1.0-theme-switcher-20260313-1552.html \
   ~/.xiaomei-workspace/yanglao-ceo-plan/index.html
open ~/.xiaomei-workspace/yanglao-ceo-plan/index.html
```

---

## 打快照命令（每次重要迭代后执行）

```bash
VER="v1.1-描述关键词"
DATE=$(date +%Y%m%d-%H%M)
cp ~/.xiaomei-workspace/yanglao-ceo-plan/index.html \
   ~/.xiaomei-workspace/yanglao-ceo-plan/versions/${VER}-${DATE}.html
echo "已保存：${VER}-${DATE}.html"
```
