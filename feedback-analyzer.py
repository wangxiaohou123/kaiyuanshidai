#!/usr/bin/env python3
"""
开元时代 · CEO 反馈闭环分析引擎 v2
三大升级：
  1. 分析完自动推送飞书通知
  2. 识别关键反馈后自动写入 E05/E06 下游文档
  3. 任务完成后动态生成下一级任务，注入 ceo-tasks.html
"""
import json, subprocess, sys, os, re
from datetime import datetime

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
PYEXE = os.path.expanduser(
    "~/Library/Application Support/xiaomei-cowork/Python311/python/bin/python3"
)

# ─────────────────────────────────────────────
# 飞书推送
# ─────────────────────────────────────────────
FEISHU_APP_ID     = "cli_a93e48764f38dcb3"
FEISHU_APP_SECRET = "FqgvKteUSDktZF4ByUpVJejJUqIR8QLP"
FEISHU_OPEN_ID    = "ou_48bb69d72d1b8d7beda6c3280210fabd"

def feishu_send(text: str) -> bool:
    try:
        import urllib.request
        # 获取 token
        req = urllib.request.Request(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            data=json.dumps({"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}).encode(),
            headers={"Content-Type": "application/json"}, method="POST"
        )
        token = json.loads(urllib.request.urlopen(req, timeout=8).read()).get("tenant_access_token", "")
        if not token:
            return False
        # 发消息
        req2 = urllib.request.Request(
            "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
            data=json.dumps({
                "receive_id": FEISHU_OPEN_ID,
                "msg_type": "text",
                "content": json.dumps({"text": text})
            }).encode(),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req2, timeout=8)
        return True
    except Exception as e:
        print(f"  飞书推送失败: {e}")
        return False

# ─────────────────────────────────────────────
# 读取 localStorage
# ─────────────────────────────────────────────
def read_feedback() -> dict:
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
# 任务定义
# ─────────────────────────────────────────────
TASKS = {
    "T001": {
        "title": "激活居委会人脉 · 探问辖区失能长者家庭需求",
        "priority": "P0", "type": "人脉",
        "check_key": "result",
        "done_values": ["聊了，对方愿意帮忙问", "聊了，有具体线索"],
        "next_action": {
            "未进行":               "【今日P0】吃饭时随口聊，话头：「居委会有没有需要照顾老人的家庭？国家有800元补贴……」",
            "聊了，对方愿意帮忙问":  "【C05推进】1周内再跟进进展；同步更新 E06 预登记表",
            "聊了，有具体线索":      "【E06录入·立即执行】将线索格式化录入家庭需求登记表；安排首次上门拜访",
            "聊了，无线索":          "【扩大渠道】换话头「有没有亲戚需要照顾老人」；尝试广外业主群",
            "对方不感兴趣":          "【升级预案】绕开居委会，通过广外小区楼门长/物业切入需求端",
        },
        "leads_key": "leads",
        # 关键触发：有具体线索 → 自动写入 E06
        "downstream": {
            "聊了，有具体线索": "write_e06",
            "聊了，对方愿意帮忙问": "write_e06_pending",
        },
        # 完成后自动生成下一任务
        "next_task": {
            "聊了，有具体线索": {
                "id": "T001-A",
                "title": "安排首次上门拜访 · 与赵奶奶家确认服务意向",
                "priority": "p0", "type": "服务",
                "timeline": "本周",
                "timeHint": "本周内（T001线索自动生成）",
                "desc": "T001 已获取家庭线索，下一步是确认服务意向，安排首次上门拜访。",
                "why": "第一个家庭是开元的原点故事，上门见面才能建立真实信任。",
                "howto": [
                    "通过家人（居委会）约定见面时间",
                    "上门时带上：服务介绍单页 + 申领补贴流程说明",
                    "目标：长者家属表示有意向，留下联系方式",
                ],
                "feedbackFields": [
                    {"key": "visit_result", "label": "上门结果", "type": "select",
                     "options": ["未安排", "已约定时间", "已上门·有意向", "已上门·无意向", "已上门·直接签约"]},
                    {"key": "family_info", "label": "家庭详情（补充）", "type": "textarea",
                     "placeholder": "长者情况、主要联系人、联系方式…"},
                    {"key": "note", "label": "备注", "type": "textarea", "placeholder": ""},
                ]
            }
        }
    },
    "T002": {
        "title": "社区巡访 · 登记2户有需求的家庭信息（E06首批）",
        "priority": "P0", "type": "人脉",
        "check_key": "count",
        "done_values": ["2户", "3户及以上"],
        "next_action": {
            "0户":       "【今日P0·下午出门】广外街道14:00-17:00老人出门高峰，去转30分钟",
            "1户":       "【差1户完成目标】已有1户！请家人再推荐1户；或今晚再出门巡访",
            "2户":       "【E06达成！】将手机备忘录发给小美，整理成正式家庭需求登记表",
            "3户及以上":  "【超额完成！】整理进 E06；选最典型的2户作为首批服务家庭",
        },
        "leads_key": "summary",
        "downstream": {
            "2户": "write_e06",
            "3户及以上": "write_e06",
        },
        "next_task": {
            "2户": {
                "id": "T002-A",
                "title": "E06 家庭登记表整理 · 格式化录入2户信息",
                "priority": "p0", "type": "文档",
                "timeline": "本周",
                "timeHint": "T002完成后自动生成",
                "desc": "将手机备忘录记录的2户家庭信息，格式化录入 E06 标准登记表，供COO后续跟进使用。",
                "why": "E06 是开元首批用户数据库，需要标准化才能被班子复用。",
                "howto": [
                    "在备注框粘贴备忘录内容，小美自动格式化",
                    "确认：姓名/年龄/失能程度/主要联系人/联系方式",
                    "完成后小美自动更新 index.html 的 E06 状态",
                ],
                "feedbackFields": [
                    {"key": "raw_notes", "label": "粘贴手机备忘录原始记录", "type": "textarea",
                     "placeholder": "把所有记录粘贴进来，小美帮你整理"},
                    {"key": "note", "label": "其他备注", "type": "textarea", "placeholder": ""},
                ]
            }
        }
    },
    "T003": {
        "title": "致电广外街道政务中心 · 确认补贴申领流程（E05核心）",
        "priority": "P0", "type": "政务",
        "check_key": "q1",
        "done_values": ["已落地，正常受理", "落地但暂未受理"],
        "next_action": {
            "未打":              "【下周一9:00 P0】电话：010-83736036，工作日 09:00-11:30/13:30-17:00",
            "已落地，正常受理":   "【E05完成·解锁CFO】整理成 E05 核查表；CFO启动定价策略",
            "落地但暂未受理":     "【E05部分完成】确认受理时间；拨备用通道：民政局 010-66133678",
            "说不清楚，需再问":   "【换通道】改拨西城区民政局：010-66133678，重新询问",
        },
        "leads_key": None,
        "downstream": {
            "已落地，正常受理": "write_e05",
            "落地但暂未受理": "write_e05_partial",
        },
        "next_task": {
            "已落地，正常受理": {
                "id": "T003-A",
                "title": "E05 政策核查表定稿 · 触发CFO定价建模",
                "priority": "p0", "type": "文档",
                "timeline": "本周",
                "timeHint": "T003完成后自动生成",
                "desc": "将5个电话问题的答案录入 E05 标准核查表，CFO据此启动定价策略与现金流模型。",
                "why": "CFO封驳原则：未经书面确认的政策补贴不得进入财务模型。E05是解锁CFO工作的钥匙。",
                "howto": [
                    "在任务卡片填写5个问题的答案",
                    "小美自动生成 E05 核查表 HTML",
                    "CFO启动三情景财务模型（激进/中性/保守）",
                ],
                "feedbackFields": [
                    {"key": "confirm_q1", "label": "最终确认：800元补贴已落地？", "type": "select",
                     "options": ["未确认", "是，正常受理", "暂未受理，预计XX月"]},
                    {"key": "confirm_q2", "label": "申领条件（失能等级要求）", "type": "input",
                     "placeholder": "例：中度以上，需三级鉴定机构证明"},
                    {"key": "confirm_q3", "label": "到账周期", "type": "input",
                     "placeholder": "例：审核10工作日，通过后5工作日到账"},
                    {"key": "confirm_q4", "label": "代办可行性", "type": "select",
                     "options": ["未确认", "可代办·需委托书", "不可代办·本人到场"]},
                    {"key": "note", "label": "其他发现", "type": "textarea", "placeholder": ""},
                ]
            }
        }
    },
    "T004": {
        "title": "确认个人启动资金100万的到账时间节点",
        "priority": "P1", "type": "决策",
        "check_key": "window",
        "done_values": ["2026年Q4（10-12月）", "2027年Q1（1-3月）", "2027年上半年"],
        "next_action": {
            "未考虑":              "【本月决策·CFO阻塞】请评估流动性后给小美一个大致时间窗口",
            "2026年Q4（10-12月）":  "【CFO解锁·Q4启动】CFO启动三情景现金流模型；COO招募提前到Q2",
            "2027年Q1（1-3月）":    "【CFO解锁·Q1启动】现金流以2027年1月为起点；2026年底接触COO候选人",
            "2027年上半年":         "【资金偏晚】评估天使轮是否提前补充运营资金",
            "需要更多时间评估":     "【班子先按保守模型推进】告知预计评估完成日期即可",
        },
        "leads_key": "constraint",
        "downstream": {},
        "next_task": {
            "2027年Q1（1-3月）": {
                "id": "T004-A",
                "title": "启动COO联创寻访 · 建立候选人名单",
                "priority": "p1", "type": "人脉",
                "timeline": "本月",
                "timeHint": "T004完成后自动生成",
                "desc": "资金节点已确认（2027Q1），COO需在2026年底到位，现在开始建立候选人名单。",
                "why": "COO是开元最急缺的联创。招募周期3-6个月，现在启动不算早。",
                "howto": [
                    "领英搜索「居家养老运营总监」「养老机构护理部主任」",
                    "联系认识的养老行业从业者，问是否认识想创业的中层管理者",
                    "目标：本月建立5人候选名单",
                ],
                "feedbackFields": [
                    {"key": "list_count", "label": "已建立候选人数量", "type": "select",
                     "options": ["0人", "1-2人", "3-5人", "5人以上"]},
                    {"key": "top_candidate", "label": "最有潜力候选人简述", "type": "textarea",
                     "placeholder": "背景、联系状态、初步印象"},
                    {"key": "note", "label": "困难或需要支持", "type": "textarea", "placeholder": ""},
                ]
            }
        }
    },
    "T005": {
        "title": "确认开元时代的注册主体形式与命名",
        "priority": "P1", "type": "决策",
        "check_key": "preference",
        "done_values": ["个体工商户", "有限责任公司", "社会服务机构/NGO"],
        "next_action": {
            "未考虑":              "【本月决策】推荐「有限责任公司」；找会计师朋友咨询30分钟",
            "个体工商户":          "【注意融资限制】如需天使融资，后续需升级为有限公司",
            "有限责任公司":        "【最优选择·启动注册】确认股东名册和注册地址；小美准备材料清单",
            "社会服务机构/NGO":    "【确认分红限制可接受后启动】对接民政通有优势",
            "咨询后再决定":        "【小美提供咨询提纲】5个关键问题清单，律师咨询用",
        },
        "leads_key": "name",
        "downstream": {},
        "next_task": {
            "有限责任公司": {
                "id": "T005-A",
                "title": "工商注册材料准备 · 有限责任公司",
                "priority": "p1", "type": "文档",
                "timeline": "本月",
                "timeHint": "T005完成后自动生成",
                "desc": "已决定注册有限责任公司，小美帮你准备完整的注册材料清单和流程。",
                "why": "注册主体是签合同、开发票、接受融资的前提，尽早完成。",
                "howto": [
                    "确认注册地址（可用居住地或商业地址）",
                    "确认股东名册和出资比例",
                    "小美生成完整注册材料清单（营业执照申请所需文件）",
                ],
                "feedbackFields": [
                    {"key": "company_name", "label": "确认公司名称（1-3个选项）", "type": "input",
                     "placeholder": "例：开元时代（北京）养老服务有限公司"},
                    {"key": "address", "label": "注册地址", "type": "input",
                     "placeholder": "例：北京市西城区XXX街道XX号"},
                    {"key": "note", "label": "其他信息", "type": "textarea", "placeholder": ""},
                ]
            }
        }
    },
    "T006": {
        "title": "识别并接触1位顾问级人物——养老政策或医疗背景",
        "priority": "P1", "type": "人脉",
        "check_key": "exist",
        "done_values": ["有1-2个候选", "已有明确人选"],
        "next_action": {
            "暂无线索":          "【小美启动搜索】领英搜索「西城区民政 退休」；小美起草「顾问邀请信」",
            "有1-2个候选":       "【准备约谈】本月内安排1次非正式「咖啡约谈」；小美准备话术",
            "已有明确人选":      "【快速推进！】起草顾问合作意向书；本月内签约",
            "不清楚，需要想想":   "【小美发人脉盘点问卷】系统梳理一度二度人脉",
        },
        "leads_key": "profile",
        "downstream": {},
        "next_task": {
            "已有明确人选": {
                "id": "T006-A",
                "title": "顾问合作意向书起草 · 明确合作形式",
                "priority": "p1", "type": "文档",
                "timeline": "本月",
                "timeHint": "T006完成后自动生成",
                "desc": "已有明确顾问候选人，小美帮你起草合作意向书，确认咨询费/股权/期限等核心条款。",
                "why": "顾问关系需要书面确认才能在路演中作为「外部专家支持」展示给投资人。",
                "howto": [
                    "填写顾问姓名和背景",
                    "小美自动生成意向书模板（含核心条款）",
                    "本月内完成签署",
                ],
                "feedbackFields": [
                    {"key": "advisor_name", "label": "顾问姓名和背景", "type": "input",
                     "placeholder": "例：李XX，前西城区民政局养老服务科科长，现退休"},
                    {"key": "form", "label": "合作形式", "type": "select",
                     "options": ["未确定", "纯咨询·按小时收费", "月度顾问费", "股权顾问（期权形式）", "公益义务顾问"]},
                    {"key": "note", "label": "其他信息", "type": "textarea", "placeholder": ""},
                ]
            }
        }
    },
    "T007": {
        "title": "每周五 · P0进度校准（30分钟）",
        "priority": "P1", "type": "校准",
        "check_key": "p0status",
        "done_values": None,
        "next_action": {
            "__default__": "【每周五必做】花30分钟填写本任务；小美自动生成下周行动计划",
        },
        "leads_key": "block",
        "downstream": {},
        "next_task": {}
    },
}

# ─────────────────────────────────────────────
# Step 2: 判断任务状态
# ─────────────────────────────────────────────
def check_task(tid, task_def, feedback):
    s = feedback.get(tid, {})
    is_marked_done = bool(s.get("done", False))
    has_feedback = bool(s.get("savedAt"))
    check_key = task_def["check_key"]
    val = s.get(check_key, "")
    done_values = task_def.get("done_values")
    is_done = is_marked_done
    if done_values is None:
        is_done = is_done or len(str(val)) > 5
    elif val in done_values:
        is_done = True
    next_actions = task_def["next_action"]
    action = next_actions.get(val) or next_actions.get("__default__") or "→ 等待CEO填写反馈"
    leads_key = task_def.get("leads_key")
    leads = s.get(leads_key, "") if leads_key else ""
    return {
        "id": tid, "title": task_def["title"],
        "priority": task_def["priority"], "type": task_def["type"],
        "done": is_done, "has_feedback": has_feedback,
        "feedback_value": val, "action": action,
        "leads": leads, "note": s.get("note", ""),
        "saved_at": s.get("savedAt", ""), "raw": s,
    }

# ─────────────────────────────────────────────
# 优化2：自动写入下游文档
# ─────────────────────────────────────────────
def execute_downstream(results, feedback):
    actions_taken = []
    for r in results:
        if not r["done"]:
            continue
        task_def = TASKS.get(r["id"], {})
        downstream = task_def.get("downstream", {})
        val = r["feedback_value"]
        action_key = downstream.get(val)
        if not action_key:
            continue

        s = r["raw"]

        if action_key in ("write_e06", "write_e06_pending"):
            leads = r["leads"] or s.get("summary", "") or ""
            if leads:
                e06_path = os.path.join(WORKSPACE, "knowledge", "E06-family-registry.md")
                os.makedirs(os.path.dirname(e06_path), exist_ok=True)
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                status = "✅ 有意向" if action_key == "write_e06" else "📝 待跟进"
                entry = f"""
## 家庭登记 · {now} （来源：{r['id']}）
- **状态**：{status}
- **原始线索**：{leads}
- **来源任务**：{r['id']} · {r['title']}
- **备注**：{r['note']}
- **待办**：安排首次上门拜访，确认服务意向
"""
                with open(e06_path, "a", encoding="utf-8") as f:
                    if os.path.getsize(e06_path) == 0 if os.path.exists(e06_path) else False:
                        f.write("# E06 · 家庭需求登记表\n> 开元时代 · 首批潜在服务家庭记录\n")
                    f.write(entry)
                actions_taken.append(f"✅ 线索已写入 E06 家庭登记表：{leads[:50]}…")

        elif action_key in ("write_e05", "write_e05_partial"):
            e05_path = os.path.join(WORKSPACE, "knowledge", "E05-policy-checklist.md")
            os.makedirs(os.path.dirname(e05_path), exist_ok=True)
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            status = "✅ 完整确认" if action_key == "write_e05" else "⚠️ 部分确认"
            q1 = s.get("q1", "—"); q2 = s.get("q2", "—"); q3 = s.get("q3", "—")
            q4 = s.get("q4", "—"); q5 = s.get("q5", "—")
            content = f"""# E05 · 政策核查表
> 更新时间：{now} · 状态：{status}

| 核查项 | 结果 |
|--------|------|
| ①800元补贴是否落地 | {q1} |
| ②申领条件（失能鉴定） | {q2} |
| ③到账周期 | {q3} |
| ④代办可行性 | {q4} |
| ⑤消费券使用范围 | {q5} |

> 下一步：CFO 据此启动三情景定价模型
"""
            with open(e05_path, "w", encoding="utf-8") as f:
                f.write(content)
            actions_taken.append(f"✅ E05 政策核查表已更新（{status}）")

    return actions_taken

# ─────────────────────────────────────────────
# 优化3：动态任务注入 ceo-tasks.html
# ─────────────────────────────────────────────
def inject_next_tasks(results, feedback):
    """将已完成任务对应的下一级任务注入 ceo-tasks.html"""
    tasks_html_path = os.path.join(WORKSPACE, "ceo-tasks.html")
    with open(tasks_html_path, encoding="utf-8") as f:
        html = f.read()

    new_tasks_js = []
    injected_ids = []

    for r in results:
        if not r["done"]:
            continue
        task_def = TASKS.get(r["id"], {})
        val = r["feedback_value"]
        next_task_map = task_def.get("next_task", {})
        next_task = next_task_map.get(val)
        if not next_task:
            continue

        # 检查是否已注入
        tid = next_task["id"]
        if f'id: "{tid}"' in html:
            continue  # 已存在，跳过

        # 构建 JS 对象字符串
        howto_js = ",\n      ".join(f'"{h}"' for h in next_task["howto"])
        fields_js = ""
        for ff in next_task["feedbackFields"]:
            opts = ""
            if ff.get("options"):
                opts_str = ", ".join(f'"{o}"' for o in ff["options"])
                opts = f', options:[{opts_str}]'
            ph = ff.get("placeholder", "")
            fkey = ff["key"]; flabel = ff["label"]; ftype = ff["type"]
            fields_js += f'      {{ key:"{fkey}", label:"{flabel}", type:"{ftype}", placeholder:"{ph}"{opts} }},\n'

        task_js = f"""
  {{
    id: "{tid}",
    priority: "{next_task['priority']}",
    type: "{next_task['type']}",
    timeline: "{next_task['timeline']}",
    timeHint: "{next_task['timeHint']}",
    title: "{next_task['title']}",
    desc: "{next_task['desc']}",
    why: "{next_task['why']}",
    howto: [
      {howto_js},
    ],
    feedbackFields: [
{fields_js}    ]
  }},"""

        new_tasks_js.append(task_js)
        injected_ids.append(tid)

    if not new_tasks_js:
        return []

    # 插入到 TASKS 数组末尾（在最后一个 }; 之前）
    tasks_end_marker = "\n];\n"
    if tasks_end_marker in html:
        insert_pos = html.rindex(tasks_end_marker)
        new_html = html[:insert_pos] + "\n".join(new_tasks_js) + "\n" + html[insert_pos:]
        with open(tasks_html_path, "w", encoding="utf-8") as f:
            f.write(new_html)

    return injected_ids

# ─────────────────────────────────────────────
# 生成报告文本
# ─────────────────────────────────────────────
def generate_report(results, downstream_actions, new_task_ids):
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
    lines += [
        f"| 🚨 P0 紧急 | {sum(1 for r in p0 if r['done'])} | {sum(1 for r in p0 if not r['done'])} |",
        f"| 📋 P1 重要 | {sum(1 for r in p1 if r['done'])} | {sum(1 for r in p1 if not r['done'])} |",
        "",
    ]

    # P0 详情
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

    # P1 详情
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

    # 自动执行结果
    if downstream_actions:
        lines.append("## 🤖 班子自动执行")
        lines.append("")
        for a in downstream_actions:
            lines.append(f"- {a}")
        lines.append("")

    # 动态新增任务
    if new_task_ids:
        lines.append("## 🆕 自动生成下一级任务")
        lines.append("")
        for tid in new_task_ids:
            lines.append(f"- **{tid}** 已注入任务区，刷新 ceo-tasks.html 即可看到")
        lines.append("")

    # 今日优先行动
    pending = [r for r in results if not r["done"]]
    if pending:
        lines.append("## 🎯 今日优先行动（班子自动生成）")
        lines.append("")
        for r in pending:
            if r["leads"] and r["priority"] == "P0":
                lines.append(f"**[紧急线索·{r['id']}]** {r['leads'][:100]}")
                lines.append(f"   → {r['action']}")
                lines.append("")
        p0_p = [r for r in pending if r["priority"] == "P0"]
        if p0_p:
            lines.append("### 🚨 P0 本周必完成")
            for r in p0_p:
                lines.append(f"- **{r['id']}** · {r['action']}")
            lines.append("")
        p1_p = [r for r in pending if r["priority"] == "P1"]
        if p1_p:
            lines.append("### 📋 P1 本月推进")
            for r in p1_p:
                lines.append(f"- **{r['id']}** · {r['action']}")
            lines.append("")

    lines += ["---", "*开元时代 · 反馈闭环引擎 v2 · 自动生成*"]
    return "\n".join(lines)

# ─────────────────────────────────────────────
# 飞书通知文本
# ─────────────────────────────────────────────
def build_feishu_msg(results, downstream_actions, new_task_ids):
    now = datetime.now().strftime("%m/%d %H:%M")
    done_count = sum(1 for r in results if r["done"])
    total = len(results)
    pct = round(done_count / total * 100)

    lines = [f"🔄 开元时代 · CEO反馈分析报告\n{now} · 进度 {done_count}/{total}（{pct}%）\n"]

    # P0 关键状态
    p0_done = [r for r in results if r["priority"] == "P0" and r["done"]]
    p0_pending = [r for r in results if r["priority"] == "P0" and not r["done"]]

    if p0_done:
        lines.append("✅ P0已完成：")
        for r in p0_done:
            lines.append(f"  · {r['id']} {r['title'][:20]}…")

    if p0_pending:
        lines.append("\n🔴 P0待处理：")
        for r in p0_pending:
            lines.append(f"  · {r['id']} {r['title'][:20]}… → {r['action'][:40]}…")

    if downstream_actions:
        lines.append("\n🤖 班子已自动执行：")
        for a in downstream_actions:
            lines.append(f"  {a[:60]}")

    if new_task_ids:
        lines.append(f"\n🆕 新增任务：{', '.join(new_task_ids)}")
        lines.append("  刷新任务区即可看到")

    lines.append(f"\n👉 https://wangxiaohou123.github.io/kaiyuanshidai/ceo-tasks.html")
    return "\n".join(lines)

# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("📋 开元时代 · CEO 反馈闭环引擎 v2")
    print("=" * 40)

    feedback = read_feedback()

    if not feedback:
        print("\n⚠️  暂无反馈数据")
        print("   打开 ceo-tasks.html → 展开任务卡片 → 填写表单 → 点「保存反馈」")
        sys.exit(0)

    print(f"\n✅ 读取到 {len(feedback)} 条反馈记录\n")

    # 分析任务
    results = []
    for tid, task_def in TASKS.items():
        result = check_task(tid, task_def, feedback)
        results.append(result)
        icon = "✅" if result["done"] else ("📝" if result["has_feedback"] else "⏳")
        print(f"{icon} {tid} · {result['title'][:40]}")

    print("\n" + "=" * 40)

    # 优化2：自动执行下游文档
    print("\n🤖 优化2：自动推进下游文档…")
    downstream_actions = execute_downstream(results, feedback)
    for a in downstream_actions:
        print(f"  {a}")

    # 优化3：动态注入新任务
    print("\n🆕 优化3：检查是否需要生成下一级任务…")
    new_task_ids = inject_next_tasks(results, feedback)
    if new_task_ids:
        print(f"  ✅ 新注入任务：{', '.join(new_task_ids)}")
    else:
        print("  暂无新任务需要生成")

    # 生成并保存报告
    report = generate_report(results, downstream_actions, new_task_ids)

    output_dir = os.path.join(WORKSPACE, "knowledge", "daily-intel")
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    output_path = os.path.join(output_dir, f"feedback-report-{ts}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n✅ 报告已保存：{output_path}")

    # 优化1：自动推送飞书
    print("\n📲 优化1：推送飞书通知…")
    msg = build_feishu_msg(results, downstream_actions, new_task_ids)
    ok = feishu_send(msg)
    print(f"  {'✅ 飞书推送成功' if ok else '⚠️ 飞书推送失败（离线环境？）'}")

    print("\n" + "=" * 40)
    print(report)
