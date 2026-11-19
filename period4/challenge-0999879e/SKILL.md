---
name: paper-quality-auditor
description: |
  论文质量审查 Skill。把"哪里有问题"变成可执行可核对可交办的条件目：结构完整性、事实
  一致性、论证链断裂、可发表性问题。每个问题给原文位置+判断依据+问题分级（事实错误/
  证据不足/规范问题/建议）+修改建议；无法确认标 needs_review 不凭空补结论。
---

# Paper Quality Auditor — 论文质量审查 Skill

## 1. 用途与适用范围

整体质量/结构完整性/事实一致性/可发表性审查。产出**可交办的问题单**：哪段论断缺证据、哪处引用不支持所引内容、哪实验缺对照或样本量、统计缺哪个量、论证链断在哪、哪些表述触规范。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、稿件、审查重点（如指定检查项）。
2. 建立检查清单（按题目给定的检查项优先）：结构/事实/统计/引用/论证/规范。

## 3. 工作流程

### Step 1 结构完整性
- 章节要素齐备（摘要/方法/结果/讨论/限制/声明）；图表与正文引用互查；承诺-交付对照（引言说要做的在结果出现）。

### Step 2 事实一致性
- 正文数值 ↔ 表格/图；摘要结论 ↔ 结果正文；方法描述 ↔ 材料步骤——不一致逐条定位。

### Step 3 论证与证据
- 论断-证据清单：无证据论断、引用不支持所引句、缺对照/样本量说明、统计量缺失、论证链断裂点。

### Step 4 分级与输出
- 每条问题：`{issue_id, 位置(段/句), 类型: factual_error | insufficient_evidence | normative | suggestion, severity: major | minor, 依据(原文引用), 建议修改}`。
- 无法确认（材料外事实）→ needs_review，不凭空补结论。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "paper_quality_review",
  "status": "success | partial | failed",
  "issues": [
    {"issue_id":"i1","loc":{"section":"3 Results","paragraph":2,"sentence":1},
     "type":"insufficient_evidence","severity":"major",
     "quote":"稿件原句","basis":"无对照设置说明","suggestion":"补充对照描述或降级表述"}
  ],
  "completeness": {"missing_sections":[],"figure_ref_mismatch":[],"promise_delivery_gap":["引言承诺的X分析未在结果出现"]},
  "consistency": [{"loc":"摘要 vs §4","note":"数值不一致","detail":"..."}],
  "needs_review": [{"issue_id":"i5","reason":"涉及材料外事实，无法确认"}],
  "stats": {"by_type":{"factual_error":1,"insufficient_evidence":4,"normative":2,"suggestion":3},"by_severity":{"major":3,"minor":7}},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：issues 每条有位置+依据引用+类型+severity；四类分级准确；needs_review 不补结论；建议具体可执行。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 稿件不完整 | 按 existing 部分审查 + 缺失登记 |
| 领域事实超出材料 | needs_review |
| 预算不足 | major 级优先扫描 |

## 6. 自查清单

1. [ ] 问题单逐条可交办（位置/依据/类型/建议）？
2. [ ] 四类分级准确？
3. [ ] needs_review 未补结论？
4. [ ] 承诺-交付对照做了？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。结构+事实一致性脚本辅助扫描；论证与证据逐段核对；输出按严重度排序。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：输入文件与材料是事实依据；不编造记录/引用/软件状态/数据。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（文件/记录/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
