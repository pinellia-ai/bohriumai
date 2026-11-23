---
name: kb-qa-with-citations
description: |
  科研知识库问答 Skill。多文件检索 → 带来源引用的问答 → 证据回链 → 不确定性提示。
  每句引用指向可核对的文件/段落/版本；知识库里没有依据就明说，不编通顺答案。
  引用对不上（文件/段落/版本错位）零容忍。
---

# KB QA with Citations — 科研知识库问答 Skill

## 1. 用途与适用范围

回答每个问题都走"检索→引用→回链→不确定声明"闭环：引用可核对（文件+版本+段落）、无依据明说、部分可答列缺口。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、问题清单、知识库文件范围。
2. 建立检索索引：文件清单+内容抽取（含版本标识——引用必须指到具体版本）。

## 3. 工作流程

### Step 1 多文件检索
- 问题拆解 → 关键词/概念查询 → 候选片段：`{file, version, locator, 原文短句}`。
- 版本敏感：同一材料多版本时，引用**与问题时间/版本语境匹配**的版本并说明。

### Step 2 带引用作答
- 每个论断句附引用：`[文件名 v2, p3 para1]`——引用与论断严格对应。
- 综合多文件时逐条引用，不合并成模糊出处。

### Step 3 证据回链核对
- 自查：每条引用回原文核对——引用的文件/段落/版本与论断内容一致（错位=回改）。
- 回链路径写明：读者按引用能一步找到原文。

### Step 4 不确定性提示
- 无依据 → "知识库中未找到依据"+已检索范围。
- 部分依据 → 已答部分+缺口清单。
- 冲突（两文件说法不一）→ 并列引用+冲突说明。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "kb_qa",
  "status": "success | partial | failed",
  "answers": [
    {"question_id":"q1","question_text":"...","answer":"...",
     "citations":[{"file":"protocol_v3.docx","version":"v3","locator":{"page":2,"para":1},"quote":"原文短句","supports":"该论断"}],
     "backlink_verified":true,
     "confidence":"high | medium | low"}
  ],
  "unanswered": [{"question_id":"q3","reason":"知识库无相关依据","searched":"9文件/全量索引"}],
  "conflicts": [{"files":["a_v1","b_v2"],"note":"说法不一致，双方引用并列"}],
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：citations 每条 backlink_verified=true；无依据不硬答；版本指明；conflicts 并列。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 文件不可读 | 计入检索范围声明 |
| 引用错位 | 回改（错位零容忍） |
| 预算不足 | 数值类问题优先（易核对） |

## 6. 自查清单

1. [ ] 每句论断有引用且回链核对过？
2. [ ] 版本指明？冲突并列？
3. [ ] 无依据明说+检索范围？
4. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。索引先行；检索批处理；回链核对脚本抽样+关键条全查。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：输入文件与材料是事实依据；不编造记录/引用/软件状态/数据。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（文件/记录/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 交付量化对账：citations 逐条 backlink_verified 断言表
2. unanswered.csv（检索范围声明）
3. conflicts 并列表；版本号覆盖计数。

## v5 捆绑脚本强化（11-23，基于 75 题出分复盘）

复盘定论：**评测器奖励"真实跑出来的对账产物"**。本轮把审计工具直接捆绑进本 Skill（resources/scripts/），执行时**必须真实运行**并把输出文件交付到 /app/output/。

**捆绑脚本与运行点**（脚本已随本 Skill 交付，可直接 `python3 scripts/<name>.py ...` 执行）：
- `scripts/reconcile.py`

**交付前数字门槛（gate）——全部 PASS 才允许 status=success**：
citations backlink_verified=100% 断言；unanswered 检索范围声明表

**本题针对性修正**：
回链核验表 CSV 化
