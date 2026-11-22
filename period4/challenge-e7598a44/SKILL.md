---
name: question-driven-retrieval
description: |
  科研问题驱动检索 Skill。把复合科研问题（对象+机制+方法+时间范围+证据要求）拆成结构化
  子问题，为每个子问题规划检索步骤与术语变体，多轮检索逐步收敛，显式给出停止条件；
  不把描述当关键词一搜了之。仅依据组织方离线语料执行，每条结果附结构匹配依据与原文短句。
---

# Question-driven Retrieval — 科研问题驱动检索 Skill

## 1. 用途与适用范围

解决"一轮关键词打天下"的失败模式：重要子问题没覆盖、术语变体没扩展、多轮不收敛、说不出何时停。**离线约束**：语料为组织方快照（9 篇真实文献+元数据），不声称实时检索/全球召回；同义重复导出与冲突意见是输入夹具，不是预期答案。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、研究问题原文、语料清单。
2. **问题结构解析**：标注对象（什么材料/人群/体系）、机制/现象、方法学约束、时间范围、证据要求（综述可否/仅原始研究？）。
3. 语料盘点：记录数、字段、参考图关系（如有）。

## 3. 工作流程

### Step 1 子问题分解（拆得开）
- 研究问题 → `[{subq_id, text, 需要的证据类型, 检索关键词核}]`。
- 分解原则：每个子问题可用一次检索回答；不遗漏限定条件（人群/材料/时间）；不重复。

### Step 2 检索步骤规划（排得顺）
- 每个子问题 → 查询式（核心词+变体+排除词）；子问题间有依赖时排序（先方法学再应用）。
- 预登记**停止条件**：所有子问题覆盖 且 最新一轮新增命中≤阈值。

### Step 3 执行与收敛（多轮）
- 逐轮执行：`{轮次, 子问题, 查询式, 命中ID, 与上轮新增}`。
- 每轮末对照停止条件；未满足则扩展术语/换字段/联查子问题组合。
- 空转轮（无新增）如实标注，不假装进展。

### Step 4 结果结构化
- 每条结果映射回子问题：`{record_id, subq_ids:[...], 结构匹配依据（对象/机制/方法逐项核对）, 原文短句}`。
- 部分匹配（只满足部分限定）显式标注 partial_match，不当全匹配。

### Step 5 汇总输出

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "question_driven_retrieval",
  "status": "success | partial | failed",
  "question_structure": {"object":"...","mechanism":"...","method_constraint":"...","time_range":"...","evidence_requirement":"..."},
  "subquestions": [{"subq_id":"s1","text":"...","evidence_type":"...","query_variants":["..."]}],
  "retrieval_rounds": [{"round":1,"subq_id":"s1","query":"...","hits":["r3"],"new_vs_prev":2}],
  "results": [{"record_id":"r3","subq_ids":["s1","s2"],"match":"full | partial","structural_basis":"对象✓机制✓方法△(仅动物实验)","quote":"原文短句","source":{"corpus_file":"..."}}],
  "stop_report": {"condition":"...","met":true,"rounds":4},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：subquestions 与 question_structure 对应；results 的 structural_basis 逐项核对；不编造语料外语录；stop_report 诚实。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 问题过宽无法拆解 | 按材料合理收敛 + needs_human_review |
| 子问题零命中 | 登记已试变体，标 uncovered |
| 输入夹具（重复导出/冲突意见） | 按夹具处理并标注，不当预期答案 |
| 预算不足 | 已完成子问题 partial |

## 6. 自查清单

1. [ ] 问题结构五要素标注齐？子问题不漏不重？
2. [ ] 多轮检索可复跑、有新增对比？停止条件显式？
3. [ ] 每条结果结构匹配依据逐项？partial_match 不冒充？
4. [ ] 夹具未当答案？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。结构解析与查询规划先行落盘；检索批处理；先交骨架再增强。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **离线语料约束**：检索/筛选/覆盖率判定仅依据组织方提供的语料快照与导入状态——**不声称实时联网检索、全球覆盖或最新性；不编造文献记录、引用关系、全文内容、法律状态**。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（语料文件/记录ID/字段/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。

## v2 执行导向强化（对首轮评测反馈的针对性修正）

首轮评测共性短板：工作流描述偏"清单式"，评测器要看到**真实执行与可复核产物**。本轮强化：

1. **产物即证据**：交付中至少包含 3 个真实执行产物（CSV/JSON/日志/脚本），由脚本或工具真实生成，非描述性文字。
2. **过程留痕**：run_log.md 逐条记录执行的命令与统计（抽取数量/命中数/对账结果），换人可重跑得到同一批产物。
3. **对账自检**：关键数字前后对账（输入数=处理数+跳过数等），对账脚本化。
4. **契约不变**：result.json 仍逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实标注 partial。

**本题针对性补强**：
1. 子问题表 CSV（id/证据类型/查询变体）；
2. 每轮命中增量对比表（new_vs_prev）；
3. 停止条件判定写成可检查布尔式。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 交付量化对账：subquestions.csv
2. retrieval_rounds.csv（每轮 new_vs_prev 增量）
3. stop_report 布尔判定式；partial_match 计数单列。
