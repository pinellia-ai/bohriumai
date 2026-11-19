---
name: study-quality-appraiser
description: |
  文献研究质量评价 Skill。按固定维度评价研究质量：研究设计是否支持其结论、样本与统计
  是否站得住、偏倚风险落在哪些具体环节、报告缺项。每个判断锚定原文位置（哪一段/哪张表），
  分级标准统一可复核，不凭个人经验。输出结构化评价卡 + 证据定位。
---

# Study Quality Appraiser — 文献研究质量评价 Skill

## 1. 用途与适用范围

让"同一篇文献不同人评出同一结果"：固定维度 + 统一分级规则 + 每个判断锚定原文位置。评价的是**研究设计对结论的支撑度**，不是论文写作好坏。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、待评文献（含摘要/正文摘录/表格）、评价维度要求。
2. 建立分级标准：每维度定义 `low / medium / high` 三档的**可观察判据**（如样本量阈值、对照设置、盲法声明、统计方法适用性）。
3. 材料只有摘要时声明"仅摘要可评"，正文级判断标 insufficient。

## 3. 工作流程（五维度评价）

### D1 设计-结论匹配
- 研究设计（横断面/队列/RCT/案例报告）能否支持其结论强度？相关被说成因果 → 降档，引原文结论句。

### D2 样本与统计
- 样本量/代表性（有无说明）、对照组设置、统计方法适用性（检验选择、多重比较校正）、效应量与显著性报告完整性——逐项对照表格数据。

### D3 偏倚风险（落到环节）
- 选择偏倚（入组方式）、测量偏倚（指标定义）、混杂控制（校正与否）、失访（随访率）——每项判断引用原文位置，risk: low/moderate/high。

### D4 报告完整性
- 必要要素核查：方法细节、样本描述、统计声明、局限声明——缺项逐条列出。

### D5 结论边界
- 结论是否超出数据与条件范围（外推、绝对化表述），引原文对照。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "quality_appraisal",
  "status": "success | partial | failed",
  "study_snapshot": {"design":"retrospective cohort","n":30,"outcome_measures":["..."]},
  "dimensions": [
    {"dim":"design_conclusion_fit","grade":"medium","rule_applied":"相关表述支持但因果越界",
     "evidence":[{"quote":"原文短句","loc":{"section":"Discussion","paragraph":2}}]}
  ],
  "bias_risks": [{"stage":"selection","risk":"high","evidence":"入组方式未说明","loc":{"section":"Methods para1"}}],
  "reporting_gaps": ["未报告失访率","统计方法未指明校正"],
  "overall": {"grade":"medium","justification":"D1-D5 加权综合，规则见分级标准"},
  "rubric": [{"grade":"low","criterion":"..."}],
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：每维度有 rule_applied + 原文证据定位；bias_risks 落到环节；rubric 前置可复核；overall 与维度一致（不自相矛盾）。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 仅摘要可评 | 正文级维度标 insufficient，overall 注明受限 |
| 原文与评价要求冲突 | 以原文为准，冲突登记 |
| 预算不足 | D1/D3（设计匹配+偏倚）优先 |

## 6. 自查清单

1. [ ] 五维度全覆盖？每项有原文定位？
2. [ ] 分级按 rubric 判，非经验印象？
3. [ ] 报告缺项逐条列出？
4. [ ] 仅摘要限制如实声明？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。rubric 先行；五维评价批量推进；证据定位随判随记。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **离线语料约束**：检索/筛选/覆盖率判定仅依据组织方提供的语料快照与导入状态——**不声称实时联网检索、全球覆盖或最新性；不编造文献记录、引用关系、全文内容、法律状态**。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（语料文件/记录ID/字段/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
