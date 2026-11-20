---
name: literature-review-generator
description: |
  文献综述生成 Skill。四步闭环：按标准筛选 → 按该领域文献实际分布归并主题（不套
  背景/方法/挑战/展望通用框架）→ 证据结构逐条回链 → 每句可指回具体文献的草稿。
  反面证据与结论分歧保留不抹平；出错可定位（筛选/归纳/引用三层各自留痕）。
---

# Literature Review Generator — 文献综述生成 Skill

## 1. 用途与适用范围

不是摘要连缀。四步：筛选（按标准）→ 主题归并（按实际分布）→ 证据结构（逐条回链）→ 草稿（每句可指回）。三原则：引用与论断不脱节、分歧不抹平、错误可定位。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、文献集合（题录/全文）、综述范围与纳排规则。
2. 按纳排标准筛选并留痕：`{文献, 纳入/排除, 排除理由}`——筛选层留痕，后续错误可定位到这层。

## 3. 工作流程

### Step 1 主题归并（按实际分布）
- 读纳入文献 → 按研究问题/方法/发现聚类主题：`{theme_id, 名称, 成员文献, 归并依据}`。
- 主题数量与边界由**文献实际分布**决定，模板框架（背景/方法/挑战/展望）不硬套。

### Step 2 证据结构（逐条回链）
- 每主题证据表：`{theme_id, 文献, 结论要点, 适用条件, 强度, locator(章节/页)}`。
- 反面证据与分歧专门登记（不混入主线），综述正文必须呈现。

### Step 3 草稿撰写（句句可指回）
- 每个论断句带引用且引用确实支撑该句：写前先定证据，禁止"句子通顺引文随便挂"。
- 层次：主题内综合 → 主题间关系 → 整体图景与分歧。

### Step 4 可定位性自查
- 三层留痕：筛选层（纳排表）、归纳层（主题表）、引用层（句级引用映射）——任何错误可定位到层。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "literature_review",
  "status": "success | partial | failed",
  "screening_log": [{"paper":"...","decision":"included | excluded","reason":"..."}],
  "themes": [{"theme_id":"t1","name":"...","members":["p1","p4"],"basis":"聚类依据"}],
  "evidence_map": [{"theme_id":"t1","paper":"p1","point":"...","conditions":"...","strength":"strong | moderate | weak","locator":{"section":"4","page":8}}],
  "draft": "review.md",
  "claim_citation_map": [{"draft_sentence":"...","citations":["p1 §4","p4 §2"],"supports_check":true}],
  "disagreements": [{"papers":["p1","p4"],"topic":"...","presented_in":"draft §t1"}],
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：claim_citation_map 覆盖草稿全部论断句且 supports_check 通过；disagreements 在正文呈现；三层留痕完整。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 文献不足以支撑某主题 | 主题如实标注覆盖有限 |
| 引用无法核实 | 该句降级或删除 |
| 预算不足 | 筛选+主题表先行，草稿 partial |

## 6. 自查清单

1. [ ] 主题按实际分布归并？未套通用框架？
2. [ ] 证据表逐条回链？
3. [ ] 每论断句引用确实支撑？
4. [ ] 分歧呈现？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。筛选与主题表先行；证据表批处理；草稿按主题分块写即落盘。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：输入文件与材料是事实依据；不编造记录/引用/软件状态/数据。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（文件/记录/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
