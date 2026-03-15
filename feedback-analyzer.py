#!/usr/bin/env python3
"""
开元时代 · CEO 反馈闭环分析引擎
读取 ceo-tasks.html 的 localStorage → 判断完成状态 → 生成行动计划
"""
import json
import subprocess
import sys
import os
from datetime import datetime

# ─────────────────────────────────────────────
# Step 1: 读取 localStorage
# ─────────────────────────────────────────────
def read_feedback():
    result = subprocess.run(
        ['agent-browser', 'eval',
         'JSON.stringify(JSON.parse(localStorage.getItem("kaiyuan_ceo_tasks_v2") || "{}"))'],
        capture_output=True, text=True
    )
    raw = result.stdout.strip()
    try:
        return json.loads(json.loads(raw))
    except:
        try:
            return json.loads(raw.strip('"'))
        except:
            return {}

# ─────────────────────────────────────────────
# Step 2: 任务定义（与 ceo-tasks.html 同步）
# ─────────────────────────────────────────────
TASKS = {
    "T001": {
        "title": "激活居委会人脉 · 探问辖区失能长者家庭需求",
        "priority": "P0", "type": "人脉",
        "check_key": "result",
        "done_values": ["聊了，对方愿意帮忙问", "聊了，有具体线索"],
        "blocked_values": ["对方不感兴趣"],
        "next_action": {
            "未进行":               "【今日P0·今天就做】吃饭时随口聊，话头：「居委会有没有需要照顾老人的家庭？国家有800元补贴……」",
            "聊了，对方愿意帮忙问":  "【C05推进】1周内再跟进进展；同步更新 E06 预登记表",
            "聊了，有具体线索":      "【E06录入·立即执行】将线索格式化录入家庭需求登记表；安排首次上门拜访时间",
            "聊了，无线索":          "【扩大渠道】请家人留意；或换话头「有没有亲戚需要照顾老人」；同时尝试广外业主群",
            "对方不感兴趣":          "【升级预案·绕开居委会】直接通过广外小区楼门长/业主群/物业切入需求端",
        },
        "leads_key": "leads",
    },
    "T002": {
        "title": "社区巡访 · 登记2户有需求的家庭信息（E06首批）",
        "priority": "P0", "type": "人脉",
        "check_key": "count",
        "done_values": ["2户", "3户及以上"],
        "next_action": {
            "0户":      "【今日P0·下午出门】广外街道14:00-17:00老人出门高峰，去转30分钟；看到推轮椅/老人家庭就上前搭话",
            "1户":      "【差1户完成目标】已有1户！可请家人再推荐1户；或今晚再出门巡访",
            "2户":      "【E06达成！】将手机备忘录发给小美，整理成正式家庭需求登记表",
            "3户及以上": "【超额完成！】立即整理进 E06；优先选情况最典型的2户作为首批服务家庭",
        },
        "leads_key": "summary",
    },
    "T003": {
        "title": "致电广外街道政务中心 · 确认补贴申领流程（E05核心）",
        "priority": "P0", "type": "政务",
        "check_key": "q1",
        "done_values": ["已落地，正常受理", "落地但暂未受理"],
        "next_action": {
            "未打":             "【下周一9:00 P0】电话：010-83736036，工作日 09:00-11:30/13:30-17:00；问5个问题（见任务卡片）",
            "已落地，正常受理":  "【E05完成·解锁CFO】将5个问题答案整理成 E05 核查表；CFO启动定价策略制定",
            "落地但暂未受理":    "【E05部分完成】确认受理时间；同时拨备用通道：民政局 010-66133678",
            "说不清楚，需再问":  "【换通道】改拨西城区民政局：010-66133678；重新询问800元补贴受理状态",
        },
        "leads_key": None,
    },
    "T004": {
        "title": "确认个人启动资金100万的到账时间节点",
        "priority": "P1", "type": "决策",
        "check_key": "window",
        "done_values": ["2026年Q4（10-12月）", "2027年Q1（1-3月）", "2027年上半年"],
        "next_action": {
            "未考虑":             "【本月决策·CFO阻塞】CFO无法建模；请评估流动性后告诉小美一个大致时间窗口",
            "2026年Q4（10-12月）": "【CFO解锁·Q4启动】CFO启动三情景现金流模型；COO招募提前到Q2启动",
            "2027年Q1（1-3月）":   "【CFO解锁·Q1启动】现金流模型以2027年1月为起点；2026年底开始接触COO候选人",
            "2027年上半年":        "【资金偏晚·评估融资】考虑天使轮提前补充运营资金；小美帮你起草融资需求说明",
            "需要更多时间评估":    "【班子先按保守模型推进】告小美预计评估完成日期即可",
        },
        "leads_key": "constraint",
    },
    "T005": {
        "title": "确认开元时代的注册主体形式与命名",
        "priority": "P1", "type": "决策",
        "check_key": "preference",
        "done_values": ["个体工商户", "有限责任公司", "社会服务机构/NGO"],
        "next_action": {
            "未考虑":              "【本月决策】推荐「有限责任公司」；下周找会计师朋友咨询30分钟确认",
            "个体工商户":          "【注意融资限制】如需天使融资，后续需升级；小美帮你准备升级流程说明",
            "有限责任公司":        "【最优选择·可启动注册】确认股东名册和注册地址；小美帮你准备工商注册材料清单",
            "社会服务机构/NGO":    "【确认分红限制可接受后启动】对接民政通有优势；小美起草注册申请材料",
            "咨询后再决定":        "【小美提供咨询提纲】发你律师咨询用的5个关键问题清单",
        },
        "leads_key": "name",
    },
    "T006": {
        "title": "识别并接触1位顾问级人物——养老政策或医疗背景",
        "priority": "P1", "type": "人脉",
        "check_key": "exist",
        "done_values": ["有1-2个候选", "已有明确人选"],
        "next_action": {
            "暂无线索":      "【小美启动搜索】领英搜索「西城区民政 退休」；同时小美帮你起草「顾问邀请信」模板",
            "有1-2个候选":   "【小美准备话术】本月内安排1次非正式「咖啡约谈」；小美帮你准备约谈话术和顾问意向书",
            "已有明确人选":  "【快速推进！】起草顾问合作意向书；明确咨询费/股权形式；本月内签约",
            "不清楚，需要想想": "【小美发人脉盘点问卷】系统梳理你的一度二度人脉，识别潜在顾问候选人",
        },
        "leads_key": "profile",
    },
    "T007": {
        "title": "每周五 · P0进度校准（30分钟）",
        "priority": "P1", "type": "校准",
        "check_key": "p0status",
        "done_values": None,  # 有内容即视为完成
        "next_action": {
            "__default__": "【每周五必做】花30分钟填写本任务反馈；小美据此生成下周行动计划",
        },
        "leads_key": "block",
    },
}

# ─────────────────────────────────────────────
# Step 3: 判断每个任务的完成状态
# ─────────────────────────────────────────────
def check_task(tid, task_def, feedback):
    s = feedback.get(tid, {})
    is_marked_done = bool(s.get("done", False))
    has_feedback = bool(s.get("savedAt"))

    check_key = task_def["check_key"]
    val = s.get(check_key, "")
    done_values = task_def.get("done_values")

    is_substantively_done = is_marked_done
    if done_values is None:
        # 有内容就算完成（T007）
        is_substantively_done = is_substantively_done or (len(str(val)) > 5)
    elif val in done_values:
        is_substantively_done = True

    # 下一步行动
    next_actions = task_def["next_action"]
    action = next_actions.get(val) or next_actions.get("__default__") or "→ 等待CEO填写反馈"

    # 线索内容
    leads_key = task_def.get("leads_key")
    leads = s.get(leads_key, "") if leads_key else ""

    return {
        "id": tid,
        "title": task_def["title"],
        "priority": task_def["priority"],
        "type": task_def["type"],
        "done": is_substantively_done,
        "has_feedback": has_feedback,
        "feedback_value": val,
        "action": action,
        "leads": leads,
        "note": s.get("note", ""),
        "saved_at": s.get("savedAt", ""),
        "raw": s,
    }

# ─────────────────────────────────────────────
# Step 4: 生成报告
# ─────────────────────────────────────────────
def generate_report(results):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    done_count = sum(1 for r in results if r["done"])
    total = len(results)

    lines = [
        f"# 开元时代 · CEO 反馈闭环报告",
        f"> 生成时间：{now}",
        "",
        f"## 📊 总体进度：{done_count}/{total} 任务完成（{round(done_count/total*100)}%）",
        "",
        "| 类型 | 完成 | 待处理 |",
        "|------|------|--------|",
    ]

    p0 = [r for r in results if r["priority"] == "P0"]
    p1 = [r for r in results if r["priority"] == "P1"]
    lines.append(f"| 🚨 P0 紧急 | {sum(1 for r in p0 if r['done'])} | {sum(1 for r in p0 if not r['done'])} |")
    lines.append(f"| 📋 P1 重要 | {sum(1 for r in p1 if r['done'])} | {sum(1 for r in p1 if not r['done'])} |")
    lines.append("")

    # ── P0 详情 ──
    lines.append("## 🚨 P0 紧急任务")
    lines.append("")
    for r in p0:
        icon = "✅" if r["done"] else "🔴"
        status = "完成" if r["done"] else ("有反馈" if r["has_feedback"] else "待填写")
        lines.append(f"### {icon} {r['id']} · {r['title']}")
        lines.append(f"- **状态**：{status}{(' · ' + r['saved_at']) if r['saved_at'] else ''}")
        if r["feedback_value"]:
            lines.append(f"- **CEO反馈**：{r['feedback_value']}")
        lines.append(f"- **班子行动**：{r['action']}")
        if r["leads"]:
            lines.append(f"- **获得线索**：{r['leads'][:300]}")
        if r["note"]:
            lines.append(f"- **备注**：{r['note'][:200]}")
        lines.append("")

    # ── P1 详情 ──
    lines.append("## 📋 P1 重要任务")
    lines.append("")
    for r in p1:
        icon = "✅" if r["done"] else "🟡"
        status = "完成" if r["done"] else ("有反馈" if r["has_feedback"] else "待填写")
        lines.append(f"### {icon} {r['id']} · {r['title']}")
        lines.append(f"- **状态**：{status}")
        if r["feedback_value"]:
            lines.append(f"- **CEO反馈**：{r['feedback_value']}")
        lines.append(f"- **班子行动**：{r['action']}")
        if r["leads"]:
            lines.append(f"- **附加信息**：{r['leads'][:200]}")
        lines.append("")

    # ── 今日优先行动计划 ──
    pending = [r for r in results if not r["done"]]
    if pending:
        lines.append("## 🎯 今日/本周优先行动清单（班子自动生成）")
        lines.append("")
        lines.append("基于CEO反馈，以下是班子今日需推进的工作：")
        lines.append("")

        # 有线索需要立即整理的排最前
        for i, r in enumerate(pending):
            if r["leads"]:
                lines.append(f"**[紧急·线索整理]** {r['id']} 已获线索，立即录入：")
                lines.append(f"> {r['leads'][:200]}")
                lines.append("")

        # P0待完成
        p0_pending = [r for r in pending if r["priority"] == "P0"]
        if p0_pending:
            lines.append("### 🚨 P0 本周必完成")
            for r in p0_pending:
                lines.append(f"- **{r['id']}** · {r['action']}")
            lines.append("")

        # P1待完成
        p1_pending = [r for r in pending if r["priority"] == "P1"]
        if p1_pending:
            lines.append("### 📋 P1 本月内推进")
            for r in p1_pending:
                lines.append(f"- **{r['id']}** · {r['action']}")
            lines.append("")

    else:
        lines.append("## 🎉 所有任务已完成！")
        lines.append("")
        lines.append("班子将基于完整反馈自动生成下阶段作战计划。")
        lines.append("")

    lines.append("---")
    lines.append("*本报告由小美反馈闭环引擎自动生成 · 基于 CEO 任务区 localStorage*")

    return "\n".join(lines)

# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("📋 开元时代 · CEO 反馈闭环引擎")
    print("=" * 40)

    # 读取反馈
    feedback = read_feedback()

    if not feedback:
        print("\n⚠️  暂无反馈数据（CEO 尚未在任务区填写）")
        print("\n📌 操作指引：")
        print("   1. 打开 ceo-tasks.html")
        print("   2. 点击任意任务卡片展开")
        print("   3. 填写表单后点「保存反馈」")
        print("   4. 告诉小美「有新反馈」即可触发分析")
        sys.exit(0)

    print(f"\n✅ 读取到 {len(feedback)} 条反馈记录\n")

    # 分析每个任务
    results = []
    for tid, task_def in TASKS.items():
        result = check_task(tid, task_def, feedback)
        results.append(result)
        status_icon = "✅" if result["done"] else ("📝" if result["has_feedback"] else "⏳")
        print(f"{status_icon} {tid} · {result['title'][:40]}")

    print("\n" + "=" * 40)

    # 生成报告
    report = generate_report(results)
    print(report)

    # 保存报告
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge", "daily-intel")
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    output_path = os.path.join(output_dir, f"feedback-report-{ts}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n✅ 报告已保存：{output_path}")
