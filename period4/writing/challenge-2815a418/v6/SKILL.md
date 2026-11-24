---
name: review-response-revision-run
description: |
  审稿回复与论文修改：意见逐条拆解落实，回复-修改-位置三方对齐，未落实项诚实说明。真实执行流水线：逐步产出可复核的 CSV/JSON 对账产物，每条结论指到输入材料
  的具体位置，计数断言全部脚本验收；材料不足诚实标注，绝不虚构。
---

# 审稿回复与论文修改 — 真实执行版 Skill（v6）

## 0. 运行契约（最高优先）

1. **Step 0 必做**：读 `/input/case.json` 的 `output_contract`——result.json 的字段名与嵌套结构**逐字段原样落实**，一个不缺；`case_id` 从 case.json 原样读取，禁止自造。
2. 过程文件写 `/app/work/`；最终产物写 `/app/output/`（含 result.json 与全部对账产物）。
3. 只依据 `/input/` 实际文件执行；先 `ls /input/` 再读真实内容，不依据标签猜测材料。
4. 预算 64 请求 / 900 秒 / 单响应 16384 token：**先落盘最小可用 result.json（status=partial），再逐步增强**；中断也有诚实部分产物。
5. 不虚构数据、文献、实验状态；材料外内容标 `unverifiable/gap`；可编辑 Office/图形产物附真实渲染预览。

## 1. 输入识别

1. `ls /input/`：case.json、task.md 与本题材料（PDF/docx/CSV/文本等）。
2. 读 task.md 的任务动作与交付要求；记录材料形态（文本层/扫描件/表格），决定抽取路径。
3. 本题核心质量四问：**立得住=落实真实可查；连得上=意见-回复-修改对齐；改得动=按 comment_id 单条重改；查得清=差异可回退**。全流程围绕这四问设计验收。

## 2. 执行流水线（真实执行，逐步留痕）

### Step 1 意见拆解（comments.csv）
审稿意见逐条拆成可执行项 {comment_id, 原始意见逐字, 子项, 类型(实验/表述/格式/质疑)}。验收：覆盖全部审稿意见无遗漏。

### Step 2 逐项落实方案（actions.csv）
每子项 {comment_id, 处置(修改/补实验/辩驳), 方案, 涉及位置}；无法落实的显式标 limited 并给理由与替代回应。

### Step 3 修改执行与差异（changes.csv）
真实修改稿件，逐处 {comment_id, 位置, 原文, 新文, 理由}；数字改动用 numeric_audit 审计；不改与意见无关内容。

### Step 4 回复信与对齐检查
逐条回复 {comment_id, 回复文本, 对应 changes 引用, 修改位置}；脚本对账：每意见有回复+处置；回复声称的修改在 changes 中真实存在。

### Step 5 四件套交付
findings.json、comments/actions/changes CSV + 回复信 + 修改稿、run_log.md、scoring_sheet.csv。

每步执行后把 命令/输入/输出摘要/计数 追加到 `/app/work/run_log.md`，最终随产物交付。

## 3. 输出契约

result.json 顶层必须包含 case.json `output_contract` 的**全部字段**（原样字段名），并包含：

```json
{
  "case_id": "<从 /input/case.json 原样读取>",
  "status": "success | partial | failed",
  "deliverables": {"comments": "comments.csv", "actions": "actions.csv", "changes": "changes.csv", "findings": "findings.json", "run_log": "run_log.md", "scoring_sheet": "scoring_sheet.csv", "reconciliation": "reconciliation.csv"},
  "reconciliation": {"checks": "<reconciliation.csv 检查项数>", "all_pass": true},
  "gaps": [], "needs_review": [], "uncertainty_notes": []
}
```

（示意结构；正式字段以 case.json 的 output_contract 为准，上述为追加的对账与诚实性字段。）

## 4. 数字门槛（交付前必须全部通过）

1. 意见全覆盖；每子项有处置；limited 显式说明
2. 回复-修改-位置三方对齐；虚报修改数 = 0
3. 无关内容零改动检查；数字审计通过
4. 辩驳类回复有证据支撑

任一门槛未过：能修则修；不能修则在 result.json 的 gaps/needs_review 显式登记并把 status 降为 partial，**不得带病宣称 success**。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 材料缺失/无文本层 | 换抽取路径（OCR 标置信度）；仍缺则 gap 登记 + partial |
| 计数对账 FAIL | 定位差异来源，修复或显式登记；reconciliation.csv 保留 FAIL 行不掩盖 |
| 脚本依赖不可用 | 降级为逐条人工清点并在 run_log 说明口径；不虚构脚本输出 |
| 预算不足 | 按流水线顺序优先落盘已完成步骤产物，result.json 标 partial 并列明未完成步骤 |
| 材料冲突 | 冲突双方逐字登记，标 needs_review，不擅自取舍 |

## 6. 自查清单

1. [ ] output_contract 全部字段逐字段落实？case_id 原样？
2. [ ] 数字门槛逐条跑过？reconciliation.csv 全 PASS（或 FAIL 已显式登记）？
3. [ ] 每张 CSV 行数与来源计数对账？无虚构行？
4. [ ] 每条结论有输入材料内的逐字证据或显式 unverifiable？
5. [ ] run_log.md 记录真实命令与输出？四件套齐全？
6. [ ] status 诚实（partial 不冒充 success）？

## 7. 效率约束

- 计数/比对/统计一律脚本执行（scripts/ 已捆绑），不手算大表。
- 单步产物落盘后再进下一步；重复读取同一文件用缓存摘要。
- 模型请求优先用于判定与写作，机械抽取交给脚本。

## 8. 最小调用示例（示意，非正式结果）

输入：`/input/case.json`（含 output_contract）+ 本题材料。
调用：按 §2 流水线执行 → `/app/output/result.json` + 对账 CSV + run_log.md。
示意输出片段：`{"case_id":"demo","status":"partial","reconciliation":{"checks":3,"all_pass":true},"gaps":["示例缺口"]}`（仅示意接口，不是任何真实案例答案）。

## 附：捆绑脚本（scripts/，真实可运行）

- `scripts/reconcile.py`
- `scripts/numeric_audit.py`
- `scripts/term_check.py`

脚本均为 UTF-8 Python3，标准库为主（个别需 PyMuPDF/python-docx，缺失时按 §5 降级）。
用法与输出以脚本头部 docstring 为准；所有脚本产物写入当前工作目录后移入 /app/output/。
