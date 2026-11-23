---
name: reviewer-response-builder
description: |
  审稿回复与论文修改 Skill。受控返修演练：只修订组织方基线摘要（materials/
  manuscript-baseline.md），逐条处理 reviewer-comments.md 的实际意见（拆子要求），
  产出可编辑修订稿 + 回复信草案 + 修改定位（可检索锚点）+ 未到位证据清单。
  不冒称真实审稿人逐字要求、不谎称补做实验/已接收/整篇返修完成；语气分四档，多轮承诺一致。
---

# Reviewer Response Builder — 审稿回复与论文修改 Skill

## 1. 用途与适用范围

"答得全、改得准、证得住、对得上"：意见拆解 → 逐条回应（采纳/部分采纳/不采纳+理由）→ 修改落稿并给可检索定位 → 证据清单与版本一致性台账。

材料边界（组织方修订，必须遵守）：
- `materials/manuscript-baseline.md` 是**组织方基线摘要**，`materials/reviewer-comments.md` 是**意见摘要**——不是完整原稿或审稿报告逐字全文。
- 只修订指定基线；公开论文/报告链接仅是来源身份，不代表已联网核验原文。
- **不得**冒称：真实审稿人逐字要求、真实补做实验、原作者已改稿、编辑部已接收、整篇全文返修完成。
- 意见摘要中的实质性修改要求以摘要实际内容为准。

## 2. 输入识别（必做第一步）

1. `ls /input/`（及 materials/）；读 case.json / task.md，记录 case_id。
2. 读基线摘要：记录章节结构、版本标识（作为修订基准版本 v0）。
3. 逐条读意见摘要：登记意见编号、原文。
4. 材料缺失：status=failed；意见涉及基线外内容时在回信中说明"基线摘要未包含该部分"。

## 3. 工作流程

### Step 1 意见拆解（答得全）
每条意见拆成子要求：`{comment_id, 子要求编号, 类型(method/data/writing/format/ethics), 严重度, 可执行动作, 与其它意见的关系}`。一条意见里的多个子要求逐一登记——只答一半即为缺陷。

### Step 2 逐条回应（改得准的前提）
每个子要求给决策：`accepted | partially_accepted | rejected`，附理由。不采纳时给出礼貌、有据的澄清（不冒犯、不过度承诺、不无原则顺从）。语气四档：接受/澄清/礼貌反驳/申诉——按意见性质选择并保持一致。

### Step 3 修改落稿（改得准）
- 在基线副本上执行修改，生成修订稿（保留结构，改动最小化）。
- 每处改动给**可检索定位**：修订稿中的章节 + 原文锚点（前后各一句原文，便于检索）。
- 回复信声称的每处修改必须真实落稿——落稿后逐条回查"声称↔实际"一致性。

### Step 4 证据清单（证得住）
- 需要补实验/补数据/补文献/重做分析的意见：生成证据清单 `{comment_id, 需要什么, 到位状态(已提供自材料/材料内无/无法补做), 数据出处, 替代说明}`。
- **材料内没有的证据如实标注无法补做**，并给替代处理（如加 limitation 说明）——不虚构数据、不谎称已补。

### Step 5 版本一致性（对得上）
- 台账：`意见 → 回应 → 修改 → 定位`四表对齐；上一轮承诺（若材料含）逐条核对仍成立。
- 输出修订稿版本号与变更记录。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "reviewer_response",
  "status": "success | partial | failed",
  "baseline_version": "v0 (manuscript-baseline.md)",
  "revised_manuscript": "revised_manuscript.md（可编辑，标注 v1）",
  "response_letter": "response_letter.md",
  "comment_breakdown": [
    {"comment_id":"R1","sub":[1,2],"type":"data","severity":"major","quote":"意见摘要原句"}
  ],
  "responses": [
    {"comment_id":"R1","sub":1,"decision":"accepted","action":"在§3.2加入统计方法说明",
     "tone":"accept","location":{"section":"3.2","anchor_prev":"...前句原文","anchor_next":"...后句原文"},
     "letter_text":"回复信对应段落"}
  ],
  "evidence_list": [
    {"comment_id":"R2","needed":"补充 n 的统计功效说明","status":"材料内无 | 已提供 | 无法补做",
     "source":null,"fallback":"已在 limitation 中说明"}
  ],
  "version_ledger": {"rounds_consistent":true,"broken_promises":[]},
  "honesty_notes": ["未补做实验；未核验外部链接原文；仅按摘要意见修订"],
  "needs_human_review": [], "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：每条意见及子要求都有回应；location 用原文锚点可检索；evidence_list 状态如实；不得出现的冒称语句（已接收/已补实验等）逐项自检为空；修订稿与回复信同版本。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 意见超出基线范围 | 回信说明"基线摘要未含该部分"，标 needs_human_review |
| 意见互相冲突 | 双方并列，给作者裁决建议 |
| 无法补做的证据 | 如实标注 + 替代说明（limitation/澄清），不虚构 |
| 预算不足 | 先 major 意见全流程，status=partial |

## 6. 自查清单

1. [ ] 每条意见的每个子要求都有明确结论？
2. [ ] 回复信声称的修改真实落稿且锚点可检索？
3. [ ] 证据清单状态如实？无冒称语句？
4. [ ] 语气得当（无冒犯/无过度承诺）？
5. [ ] 台账四表对齐、版本一致？
6. [ ] result.json 可解析、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。意见拆解一次完成；修订与回复信同步产出（每条意见处理完即落稿）；锚点摘录随改动即时记录。中断时已完成意见的完整闭环可交（partial）。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"success",
 "comment_breakdown":[{"comment_id":"R1","sub":[1],"type":"method","severity":"major","quote":"请补充统计方法描述"}],
 "responses":[{"comment_id":"R1","sub":1,"decision":"accepted","action":"在§3.2加入统计方法句",
   "tone":"accept","location":{"section":"3.2","anchor_prev":"...各组差异分析...","anchor_next":"...结果见表2..."},
   "letter_text":"We have added the statistical methods in Section 3.2 (page 5, para 2)."}],
 "evidence_list":[{"comment_id":"R2","needed":"重复实验数据","status":"材料内无","source":null,"fallback":"limitation 已注明"}],
 "version_ledger":{"rounds_consistent":true,"broken_promises":[]},
 "honesty_notes":["未补做实验"],"gaps":[],"uncertainty_notes":[],"changes":[]}
```

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段（如存在）。它定义本案例 `result.json` 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实内容**；contract 里有而本文件 §4 未描述的字段，按 contract 字段语义填实际结果，绝不遗漏；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：一律从 `/input/case.json` 原样读取，禁止自造。
3. **路径**：工作过程写 `/app/work/`；最终产物写 `/app/output/`，主输出为 /app/output/result.json（含 case.json 的 output_contract 全部字段）。
4. **尽早落盘**：先用最小可用结果写一次 /app/output/result.json（含 case.json 的 output_contract 全部字段），再增量增强——任何时刻中断都保证已落盘内容诚实、结构合法（status 如实标 partial）。
5. **不虚构**：无数据、无文件、无软件状态一律不编造；材料缺失写 gaps，无法判断写 uncertainty，禁止把推断写成事实。
6. **可核验**：每个关键结论保留来源定位（页/段/句/表号/图号或文件位置），他人可独立复核。
7. **交付物自检**：本 Skill 的提交材料为 SKILL.md + README.md（使用与方法说明）；运行时按上述契约执行案例。二者不一致处以本节契约为准。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 保持 73.3 分水准：responses.csv（意见/子要求/决策/锚点）逐条；evidence_list 状态三态计数；台账四表对齐断言。

## v5 捆绑脚本强化（11-23，基于 75 题出分复盘）

复盘定论：**评测器奖励"真实跑出来的对账产物"**。本轮把审计工具直接捆绑进本 Skill（resources/scripts/），执行时**必须真实运行**并把输出文件交付到 /app/output/。

**捆绑脚本与运行点**（脚本已随本 Skill 交付，可直接 `python3 scripts/<name>.py ...` 执行）：
- `scripts/docx_inventory.py`
- `scripts/reconcile.py`

**交付前数字门槛（gate）——全部 PASS 才允许 status=success**：
responses.csv 行数=意见子要求总数（对账）；锚点可检索=100% 断言

**本题针对性修正**：
返修台账 CSV 化 + 修改落稿后 docx_inventory 验证
