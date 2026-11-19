---
name: incremental-literature-tracker
description: |
  最新文献发现与追踪 Skill。基于组织方增量导入状态的离线快照判定"真新增"：区分首次
  出现/版本演进（预印本→正式版→修订版）/滞后入库旧文献/重复转载/撤稿记录。每次输出
  带增量依据（与上一状态对比），重复与误报不推给用户。不声称全球最新性。
---

# Incremental Literature Tracker — 最新文献发现与追踪 Skill

## 1. 用途与适用范围

把"增量变化"做成可信的发现流：真新论文、版本更新、方向变化——同时过滤四类噪声：滞后入库的旧文献、重复转载、版本演进误报、撤稿记录。**离线约束**：语料带 organizer-local 增量导入状态；**不声称全球最新/实时覆盖**；"新"的判定=与导入状态对比，不是猜。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、主题范围、语料与**增量导入状态**（哪些记录哪些批次已入库）。
2. 盘点：记录清单、版本链线索（预印本 DOI/正式 DOI 关联、勘误标注）、时间字段（发表/入库/更新）。

## 3. 工作流程

### Step 1 基线建立
- 从导入状态建立基线集合：`{record_id, batch, first_seen}`——"新"的定义=不在基线中的记录。

### Step 2 版本链归并（"新"不干净的主因）
- 预印本→正式版→修订/勘误 按标识符与版本关系归并成**一条实体**的版本链。
- 判定类型：`new_work（全新论文）| new_version（已知论文的新版本）| late_indexed（旧文新入库）| duplicate（转载）| retraction（撤稿/更正）`。
- new_version 与 new_work 分开报告——用户要的是"新东西"，不是"旧文的第 2 版冒充新发现"。

### Step 3 新增判定与降噪
- 对每条非基线记录给出判定与依据（标识符关联/日期对比/重复文本）。
- 重复转载：与基线内容一致的记录标 duplicate 并给匹配依据，不进"新发现"列表。
- 撤稿记录：单独列出（不入常规推荐），标注关联的原记录。

### Step 4 方向变化提示（可选增值）
- 从新记录的主题分布看领域动向（新主题词出现频次），作为观察项而非结论。

### Step 5 输出

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "incremental_tracking",
  "status": "success | partial | failed",
  "baseline": {"known_records":18,"batches":["b1","b2"]},
  "findings": [
    {"record_id":"r21","type":"new_work | new_version | late_indexed",
     "evidence":"首次出现于 b3；无基线匹配","version_chain":{"preprint_doi":null,"published_doi":"...","revisions":[]},
     "match_topic":"与主题查询 q1 相关","basis_quote":"..."}
  ],
  "filtered_noise": [
    {"record_id":"r22","type":"duplicate","matched_to":"r5","evidence":"同DOI转载"},
    {"record_id":"r23","type":"retraction","linked_to":"r7","note":"撤稿通知"}
  ],
  "trend_notes": ["新主题词出现：...（观察项）"],
  "gaps": [], "uncertainty_notes": ["仅覆盖导入批次内语料"], "changes": []
}
```

硬性要求：findings 每条有与基线对比的依据；version_chain 归并完整；噪声过滤逐条给依据；无全球最新性声明。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 导入状态缺失 | 无法判增量 → 如实说明，退化为全量主题清单 |
| 版本关系不明 | 标 uncertain，不强行归并 |
| 预算不足 | 版本链归并优先，趋势提示可省 |

## 6. 自查清单

1. [ ] "新"的判定基于导入状态对比？
2. [ ] 五类记录类型分开？new_version 不冒充 new_work？
3. [ ] 噪声（重复/转载/撤稿）逐条有依据？
4. [ ] 无实时/全球声明？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。基线集合与标识符索引脚本化；版本链归并批处理；噪声清单自动比对。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **离线语料约束**：检索/筛选/覆盖率判定仅依据组织方提供的语料快照与导入状态——**不声称实时联网检索、全球覆盖或最新性；不编造文献记录、引用关系、全文内容、法律状态**。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（语料文件/记录ID/字段/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
