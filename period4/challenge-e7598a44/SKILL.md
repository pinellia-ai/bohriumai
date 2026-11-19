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
