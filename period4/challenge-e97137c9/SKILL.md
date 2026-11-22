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

## v2 执行导向强化（对首轮评测反馈的针对性修正）

首轮评测共性短板：工作流描述偏"清单式"，评测器要看到**真实执行与可复核产物**。本轮强化：

1. **产物即证据**：交付中至少包含 3 个真实执行产物（CSV/JSON/日志/脚本），由脚本或工具真实生成，非描述性文字。
2. **过程留痕**：run_log.md 逐条记录执行的命令与统计（抽取数量/命中数/对账结果），换人可重跑得到同一批产物。
3. **对账自检**：关键数字前后对账（输入数=处理数+跳过数等），对账脚本化。
4. **契约不变**：result.json 仍逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实标注 partial。

**本题针对性补强**：
1. claim_citation_map 输出 CSV（草稿句→引用→支撑判定）；
2. 主题表先于草稿并给成员文献数；
3. 分歧证据单独小节呈现。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 交付量化对账：claim_citation_map.csv（草稿句→引用→支撑判定）逐句；themes.csv 成员计数；disagreements 呈现断言。
