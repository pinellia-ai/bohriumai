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
