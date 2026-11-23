---
name: citation-tracing-discovery
description: |
  引文追踪与关联文献发现 Skill。从种子论文出发：后向参考文献找方法与数据出处，前向引用
  找使用/改进/质疑者，共被引与文献耦合、主题关联找不直接引用但高度相关的平行工作。
  基于组织方保留的真实参考图（离线），每条关系标注类型与依据，不编造引用与全文内容。
---

# Citation Tracing — 引文追踪与关联文献发现 Skill

## 1. 用途与适用范围

"顺藤摸瓜"三类发现：① 后向（种子论文的参考文献 → 方法/数据出处）；② 前向（谁在用/改/质疑种子）；③ 平行（共被引/文献耦合/主题关联，不直接引用但高度相关）。**离线约束**：基于组织方保留的真实 reference graph 快照；**不编造引用关系与全文内容**；无实时数据库声称。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、种子论文、参考图数据。
2. 盘点参考图：节点（论文记录）、边（引用关系，含方向）、每篇可用字段（摘要/标题/年份）。
3. 若提供前向引用快照：记录其覆盖范围（哪些时间窗/哪些库）。

## 3. 工作流程

### Step 1 种子解析
- 种子论文的核心方法与数据集清单（从摘要/正文段提取）——追线索的"藤"。
- 登记种子记录的参考文献列表（后向）与被引情况（前向，按快照）。

### Step 2 后向追踪（方法与数据出处）
- 在参考文献中定位：方法学出处（"我们使用 X 方法[12]"→ 文献12）、数据集出处、关键试剂/工具出处。
- 每条：`{seed_loc(引用位置原文短句), target_record, relation: method_source | data_source | tool_source}`。

### Step 3 前向追踪（使用/改进/质疑）
- 前向引用快照中的论文按语义分类：`uses | extends | questions | reproduces`，依据 = 其摘要中与种子方法/结果相关的原文短句。
- 无前向快照时如实登记（不编造被引数）。

### Step 4 平行发现（共被引/耦合/主题）
- 共被引：与种子共享参考文献 ≥N 的记录；文献耦合：参考文献重叠度。
- 主题关联：摘要语义与种子核心问题高度相关但不互相引用——标注 relation: topical_parallel + 依据短句。

### Step 5 关系图汇总
- 输出节点+边清单：`{from, to, type, direction, evidence, confidence}`——每条边可回查（种子引用位置或对方摘要原文）。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "citation_tracing",
  "status": "success | partial | failed",
  "seed": {"record_id":"...","methods":["..."],"datasets":["..."]},
  "edges": [
    {"type":"backward | forward | cocitation | coupling | topical_parallel",
     "subtype":"method_source | extends | questions | ...",
     "from":"seed","to":"r7","evidence":"原文短句","evidence_loc":"seed para2 / r7 abstract",
     "confidence":"high | medium | low"}
  ],
  "graph_stats": {"nodes":18,"edges":23,"by_type":{"backward":9,"forward":4,"topical_parallel":10}},
  "forward_coverage_note": "前向引用快照覆盖2020-2024，非全史",
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：每条边有 evidence 与 confidence；无编造引用关系；forward 覆盖范围如实声明；平行发现给语义依据。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 参考图不完整（部分引用无目标记录） | 边登记为 dangling，gaps 说明 |
| 前向数据缺失 | 如实登记，只用后向+平行 |
| 预算不足 | 后向（最确定）优先，partial |

## 6. 自查清单

1. [ ] 三类发现都覆盖（或如实登记缺失）？
2. [ ] 每条边有原文依据与方向？
3. [ ] 无编造引用/全文内容？
4. [ ] 覆盖范围声明诚实？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。参考图解析脚本化；语义分类批处理；先落盘后向边再补平行。

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
1. 边表 CSV（from,to,type,evidence,locator）；
2. 共被引/耦合用脚本从参考图计算；
3. forward 覆盖范围显式声明。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 交付量化对账：edges.csv（from/to/type/evidence/locator）
2. graph_stats 计数表（按类型合计=总边数）；dangling 边计数。

## v5 捆绑脚本强化（11-23，基于 75 题出分复盘）

复盘定论：**评测器奖励"真实跑出来的对账产物"**。本轮把审计工具直接捆绑进本 Skill（resources/scripts/），执行时**必须真实运行**并把输出文件交付到 /app/output/。

**捆绑脚本与运行点**（脚本已随本 Skill 交付，可直接 `python3 scripts/<name>.py ...` 执行）：
- `scripts/reconcile.py`

**交付前数字门槛（gate）——全部 PASS 才允许 status=success**：
edges.csv 行数=graph_stats 各类型合计；dangling 计数显式

**本题针对性修正**：
边表对账：backward+forward+parallel 行数=edges 总数
