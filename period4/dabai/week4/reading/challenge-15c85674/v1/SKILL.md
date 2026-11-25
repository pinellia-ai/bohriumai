---
name: literature-qa-with-evidence
description: |
  文献智能问答 Skill：读取带段落编号的论文文本与中文问题清单，逐题回答并让每条论断
  可回核到 paper_id + paragraph_id + 逐字短引文。方法主线：通读建立段落索引 → 逐题
  检索证据 → 跨章节（方法/结果/讨论/表格）整合 → 区分论文实测(reported)与自己推断(inferred)
  → 保留数值单位条件与结论范围 → 四态回答状态 + 未回答部分 + 阅读范围。
  全程离线、仅依据给定材料：材料未报告时如实说明，冲突指出出处，不编造答案或引用。
---

# 文献智能问答 Skill（literature-qa-with-evidence）

## 1. 用途与适用范围

- 用途：输入一篇带段落编号的英文论文文本（含摘要、正文、表格文字、图注、参考文献著录）+ 一组中文问题，输出逐题结构化回答，每条论断附 paragraph_id 与逐字引文。
- 适用：文本层完整的固定材料问答；不涉及 PDF 解析、图像识别、补充附件读取或联网检索。
- 核心原则：**只依据给定材料作答；"材料未报告"也是有依据的有效回答；不编造答案或引用。**

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：提取 `case_id`、`paper_id`、`material_version`（输出必须与本次输入一致）、段落清单（保留原样段落编号，不得改写）、任务说明、问题清单（含子问）。
2. 盘点材料：论文段落总数、表格数、图注数、参考文献数。材料缺失/读取失败 → 对应问题 status=`input_error`，不编造。
3. 建目录：`/app/work/`、`/app/output/`（最终 result.json）。

## 3. 工作流程（5 步流水线）

### Step 1 段落索引（产出 work/paragraph-index.json）
- 为每段登记：paragraph_id、章节归属（Abstract/Methods/Results/Discussion/Tables/Figure captions/References）、关键实体与数值（单位随值记录）。
- 验收断言：索引段落集合 == 输入段落集合（逐段编号一致）。

### Step 2 逐题证据检索（产出 work/question-plan.json）
- 对每个 question_id：拆出主问与子问；为每个子问列出候选证据段落（≥1 个来源章节，必要时跨 Methods/Results/Tables 整合）。
- 验收断言：问题清单 100% 有计划，包括预期无法回答的。

### Step 3 回答撰写与论断绑定（产出 work/draft-answers.json）
- 回答文本 `answer`：直接回应问题与每个子问；数值、单位、比较对象、实验条件、结论范围逐字保留，不改写不换算。
- 论断 `claims[]`：每条可核验论断一项，`kind` 分层：
  - `reported`：论文实测/作者明确陈述 → evidence 必须有 paragraph_id + 逐字 quote（≤2 句，子串可匹配）。
  - `inferred`：自己的推断（如由表格数值间接推得的比较）→ 注明推断依据（指向所依据的 reported 证据），不得写成原文事实。
- 严禁把作者解释、推测性表述（may/suggest/possibly）改写成确定事实。
- 验收断言：每条 answer 至少 1 条 claim；每条 claim 至少 1 条 evidence。

### Step 4 状态与缺口（逐题）
- `answered`：完整回答问题及全部子问。
- `partial`：只能部分回答 → `unanswered_parts[]` 列明未答部分及原因（材料未报告/证据不足）。
- `insufficient_evidence`：材料确实未涉及 → 这也是有效回答，须说明检索过哪些章节。
- `input_error`：输入读取失败。
- 原文冲突：不同段落表述不一致 → 同时保留双方 paragraph_id + 原话，指出冲突，不擅自仲裁。
- 验收断言：四态枚举合法；没有一个问题被静默跳过。

### Step 5 校验与落盘（scripts/validate_answers.py）
```bash
python3 /skills/literature-qa/scripts/validate_answers.py \
  --result /app/output/result.json --case /input/case.json
```
校验：question_id 全覆盖；status 枚举；evidence 的 quote 在对应段落文本中子串匹配；material_version/case_id/paper_id 与输入一致。先写骨架（case_id + 各问题四态占位）再充实。

## 4. 输出契约（result.json 逐字段）

| 字段 | 要求 |
|---|---|
| `case_id` / `paper_id` / `material_version` | 与 /input/case.json 一致 |
| `answers[]` | 每个问题一项，不省略任何问题 |
| `answers[].question_id` | 与输入一致 |
| `answers[].answer` | 回答文本，覆盖子问，保留数值/单位/条件/范围 |
| `answers[].conditions[]` | 成立条件列表（实验条件、适用范围） |
| `answers[].status` | `answered` / `partial` / `insufficient_evidence` / `input_error` |
| `answers[].claims[]` | 论断列表 |
| `answers[].claims[].claim_id` | 如 a1-c1 |
| `answers[].claims[].text` | 论断文本 |
| `answers[].claims[].kind` | `reported`（原文报告）/ `inferred`（推断） |
| `answers[].claims[].evidence[]` | 每条含 `paragraph_id` + 逐字短引文 `quote` |
| `answers[].unanswered_parts[]` | 未回答部分及原因；无则空列表 |
| `coverage` | 已读章节、未读章节及原因（结合实际读取，供平台核验） |

示例（示意，非正式案例结果）：
```json
{
  "case_id": "demo-qa-001", "paper_id": "paperX", "material_version": "v3",
  "answers": [
    {"question_id": "Q1",
     "answer": "在 500 °C 煅烧 2 h 条件下，样品 A 的比表面积为 128 m2/g，高于样品 B 的 95 m2/g。",
     "conditions": ["煅烧 500 °C / 2 h", "BET 法测定"],
     "status": "answered",
     "claims": [
       {"claim_id": "Q1-c1", "text": "样品 A 比表面积 128 m2/g", "kind": "reported",
        "evidence": [{"paragraph_id": "p07", "quote": "sample A exhibited a BET surface area of 128 m2/g"}]},
       {"claim_id": "Q1-c2", "text": "样品 A 高于样品 B（95 m2/g）", "kind": "inferred",
        "evidence": [{"paragraph_id": "p07", "quote": "sample A exhibited a BET surface area of 128 m2/g"},
                     {"paragraph_id": "p08", "quote": "the surface area of sample B was 95 m2/g"}]}],
     "unanswered_parts": []}
  ],
  "coverage": {"read_sections": ["Abstract", "Methods", "Results", "Tables", "Figure captions"],
               "unread_sections": [], "notes": "全部段落已读取"}
}
```

## 5. 数字门槛

- 问题覆盖率 100%（含无法回答的，以 insufficient_evidence 呈现）。
- 引文可核验率 100%：reported 证据的 quote 必须在对应段落子串匹配。
- 子问覆盖：多子问问题若缺任何一个子问 → status 降为 partial 并登记 unanswered_parts。
- 定位粒度：paragraph_id 到段落级；表格证据给 表号+行。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 材料读取失败 | 对应问题 input_error，原因登记，不编造 |
| 问题涉及的量材料未报告 | insufficient_evidence，说明检索过哪些章节 |
| 只能答部分子问 | partial + unanswered_parts 逐条列原因 |
| 摘要与正文表述不一致 | 双方原话+定位并列，指出冲突，不仲裁 |
| 作者推测性表述 | 保留 may/suggest 原语气，不写成确定事实 |
| 表格数值被问及 | 引 表号+行，单位随值记录 |
| 段落编号与输入不一致 | 以输入为准回核，不一致即失败修正 |

## 7. 自查清单

- [ ] case_id/paper_id/material_version 与输入一致
- [ ] 问题 100% 覆盖，无静默跳过
- [ ] 每条 reported 证据 quote 子串匹配通过
- [ ] reported/inferred 分层清楚，推断未冒充原文
- [ ] 数值/单位/条件/范围逐字保留
- [ ] partial/insufficient_evidence 的原因与缺口列明
- [ ] coverage 如实反映实际读取
- [ ] validate_answers.py 全项通过

## 8. 效率约束

预算内完成：段落索引一次成型；证据检索按问题批量进行；先落骨架再充实；校验脚本一次跑通，失败项定点修复。

## 9. 最小示例

见 §4 示意 JSON（标明为示例）。调用流程：给论文段落 + 问题清单 → 按 Step 0-5 依次执行 → /app/output/result.json。
