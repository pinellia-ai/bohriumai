---
name: screening-smart-ranking
description: |
  文献筛选与智能排序 Skill。基于研究问题建立多维相关性判据（对象/设计/证据），对候选
  记录全量筛选：标题词面匹配不算相关；综述与原始研究、预印本与正式版分开标注；每条给出
  筛选结论与依据（引原文），排序带可解释得分。合成重复导出与冲突意见是输入夹具，按夹具
  处理。离线语料、全记录筛选、有限快照口径。
---

# Screening & Smart Ranking — 文献筛选与智能排序 Skill

## 1. 用途与适用范围

解决"标题有词就排前面"的排序失效：研究对象/人群/设计不匹配、综述与原创混杂、预印本与正式版算两篇、关键文献沉底。**离线约束**：固定研究问题 + 9 篇真实署名文献 + 实际查询输入，**全记录筛选**，有限快照口径；合成重复导出/冲突意见是输入夹具（标注 fixture 处理，不当预期答案）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、研究问题、候选记录全量清单。
2. **从研究问题推导筛选判据**（不是从标题词面）：对象是否一致、研究设计是否匹配证据要求、人群/材料限定、证据类型要求。
3. 语料盘点：记录数、字段（标题/摘要/年份/类型/DOI/版本状态）。

## 3. 工作流程

### Step 1 判据建立（判得对的依据）
- 判据表：`{criterion_id, 维度(对象/设计/人群/类型/时间), 判定规则, 权重}`。
- 每条判据可第三方复核（写成"什么样的记录满足"）。

### Step 2 全量筛选（一条不漏）
- 对**全部记录**逐条判定：`relevant | partially_relevant | not_relevant`，每条给依据（引摘要原文短句，不是标题）。
- 类型分离：review vs original research；preprint vs published version——同文多版本归并为一条（按 DOI/标识符），版本状态标注。

### Step 3 合成夹具处理
- 重复导出（同一论文不同格式出现）：按标识符归并 + dup_of 记录。
- 冲突意见（元数据互斥）：并列保留双方，标注 conflict，不擅自择一。

### Step 4 智能排序（可解释）
- 得分 = 判据逐项加权（对象匹配 > 设计匹配 > 证据强度 > 新近度），每条记录的得分构成可见。
- **关键文献前置**：与全部判据高匹配的排前；排序依据一句话可读。
- 排序结果可重算：换权重可重排（判据与得分分离存储）。

### Step 5 汇总输出

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "screening_ranking",
  "status": "success | partial | failed",
  "criteria": [{"criterion_id":"c1","dimension":"subject","rule":"...","weight":0.4}],
  "screening": [{"record_id":"r5","verdict":"relevant","type":"original_research","version":"published",
    "basis":"摘要句：...","score":0.92,"score_breakdown":{"c1":1.0,"c2":0.8},"fixture_note":null}],
  "ranked_list": [{"rank":1,"record_id":"r5","score":0.92,"one_line_reason":"对象与设计全匹配+直接证据"}],
  "dedup_log": [{"kept":"r5","merged":["r9"],"key":"doi"}],
  "conflicts": [{"record_id":"r3","fields":["year"],"values":[2021,2022],"note":"输入夹具冲突"}],
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：screening 覆盖全部记录（count 对账）；basis 引摘要原文；得分构成可重算；夹具标 fixture_note。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 记录字段不足以判定 | 用现有字段+uncertainty，不臆测 |
| 全部不相关 | 如实输出空相关集（不硬凑） |
| 预算不足 | 判据+已完成筛选 partial，排序基于已有 |

## 6. 自查清单

1. [ ] 判据从研究问题推导而非标题词面？
2. [ ] 全记录覆盖，count 对账？
3. [ ] 类型/版本分离？重复归并？夹具标注？
4. [ ] 排序得分可重算、理由一句话可读？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。判据先行；筛选批处理；排序脚本化（判据权重分离可重算）。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **离线语料约束**：检索/筛选/覆盖率判定仅依据组织方提供的语料快照与导入状态——**不声称实时联网检索、全球覆盖或最新性；不编造文献记录、引用关系、全文内容、法律状态**。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（语料文件/记录ID/字段/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
