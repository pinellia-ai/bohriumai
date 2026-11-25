---
name: literature-kg-evidence-graph
description: |
  文献知识图谱构建：从论文抽取实体与关系，schema 先行，每条三元组必须绑定
  evidence_span（原文片段+位置）与证据强度；别名归一给合并依据，不得把共现/
  转述当直接证据；至少 3 个真实执行的查询，节点与边可回溯原文。找不到支撑
  的关系不建边，信息缺失标 not_found，绝不编造。
---

# 文献知识图谱构建 Skill — schema 先行 + 证据绑定（v1）

## 1. 用途与适用范围

- 适用：从 1-2 篇论文（或多篇主题文献集）抽取实体（研究者/材料/方法/任务/指标/结论）与关系，构建带证据的可查询图谱，导出 nodes.jsonl + edges.jsonl 并支持查询。
- 不适用（不做也不报）：跨领域通用本体构建、无文献输入的常识图谱、图谱可视化美化。
- 四个验收问题（主线）：
  1. **抽得准**：实体对应论文中真实出现的对象，保留原文表述，区分作者自述与他人转述。
  2. **连得对**：关系类型/方向/条件与原文一致，共现与推测不算直接证据。
  3. **对得齐**：别名/缩写/大小写归一有依据，不重复也不错并。
  4. **查得到、回得去**：≥3 个真实查询，节点与边回到论文具体位置与原文片段。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：提取 `case_id`（**原样保留**）与 `output_contract` 全字段——result.json 逐字段落实；case.json 优先于本文。
2. 读 `/input/task.md`：确认实体类型/关系类型要求与查询问题清单。
3. 盘点材料。**特别注意多文档输入**：若提供 corpus-manifest.json / primary / secondary 材料划分，每篇论文独立登记 DOI/title/authors——根元数据只属于第一篇，**不得套到第二篇**；两篇的相同通用方法/材料术语不代表同一物理样品或模型实例。
4. 材料缺失 → status=failed + failure_reason，不虚构。

## 3. 工作流程（六步流水线）

### Step 1 Schema 先行（→ /app/work/schema.json）

先定 schema 再抽取，schema 随产物交付：

```json
{
  "entity_types": ["Researcher", "Material", "Method", "Task", "Metric", "Finding"],
  "relation_types": ["uses", "compares", "outperforms", "supports", "contradicts", "evaluated_on", "authored_by"],
  "relation_directions": {"outperforms": "A(方法) -> B(被比较方法)"},
  "evidence_fields": ["evidence_span", "source_ref", "strength", "quote_verbatim"]
}
```

- 每个关系类型给方向约束与禁用条件（如 outperforms 必须来自原文直接比较句）。
- 验收断言：schema.json 覆盖题面要求的实体/关系类型，缺失类型登记 gap。

### Step 2 实体抽取（→ /app/work/entities_raw.jsonl）

- 每条：`{entity_id, mention_verbatim, entity_type, source_ref: {doc_id, section_id, para_id, page_no}, self_reported: true|false}`。
- `self_reported=false` 标注转述/综述来源；mention_verbatim 必须逐字来自原文。
- 验收断言：脚本检查每个 mention 在原文中出现（子串匹配），不匹配即拒绝——防模型常识补全。

### Step 3 实体对齐（→ /app/work/alias_map.json）

- 归组依据逐条记录：全称-缩写映射（原文定义句）、大小写/连字符差异、明确同义表述。
- **同名不同对象不合并**：给出区分依据（不同 doc_id/不同上下文条件）。
- 输出：`{canonical_id, canonical_name, aliases:[{mention, basis}], merged_from:[entity_id], conflicts:[{name, docs, reason_not_merged}]}`。
- 验收断言：每个合并有 basis；冲突清单非空时逐条写不合并原因。**不强迫每个别名都合并**。

### Step 4 关系抽取与证据绑定（→ /app/work/triples.jsonl）

- 每条三元组：
```json
{"triple_id": "T001", "subject": "E01", "predicate": "outperforms", "object": "E02",
 "condition": "on benchmark X, when Y",
 "evidence_span": "<原文逐字片段>",
 "source_ref": {"doc_id": "primary", "section_id": "S3", "para_id": "P12", "page_no": 4},
 "strength": "direct | indirect | inferred",
 "self_reported": true}
```
- 判据：直接比较句 → direct；综述转述 → indirect + self_reported=false；仅共现 → **不建边**；无原文片段支撑 → 不建边。
- 验收断言：脚本核对 evidence_span 在原文中存在；strength=direct 的边必须含比较/因果动词。

### Step 5 查询执行（→ /app/output/queries_results.json）

- 至少 3 个真实查询（如："方法 M 在哪些任务上被评测？"、"谁 outperforms 谁、条件是什么？"、"实体 A 与 B 是否有直接关系？"）。
- 用 scripts/query_graph.py 实际执行，输出结果子图 + 每条结果的 evidence_span 与 source_ref。
- 无结果的查询如实输出 empty，说明原因，**不造关系填答案**。
- 验收断言：queries_results.json 每条结果可回溯到 triples.jsonl 的 triple_id。

### Step 6 result.json 组装（先最小后充实）

- 进入 Step 2 前先写最小 result.json（status=partial）；走完覆盖完整版。

## 4. 输出契约

result.json（以 case.json output_contract 为最高优先，以下为基准全集）：

```json
{
  "case_id": "<原样>",
  "status": "success | partial | failed",
  "graph": {
    "schema": "schema.json",
    "nodes_count": 0,
    "edges_count": 0,
    "nodes": ["nodes.jsonl 引用"],
    "edges": ["triples.jsonl 引用"],
    "alias_map": {"merged": 0, "conflicts_not_merged": 0}
  },
  "queries": [{"query": "", "results": [{"triple_id": "", "evidence_span": "", "source_ref": {}}], "empty_reason": ""}],
  "evidence_and_boundary": {
    "coverage": {"entity_types_covered": [], "relation_types_covered": [], "gaps": []},
    "not_found": ["<材料中找不到的信息，逐条登记>"],
    "cross_doc_merge_log": {"merged_with_basis": [], "refused_merges": []}
  },
  "run_status": {"state": "", "failure_reason": "", "manual_intervention_point": ""},
  "sources": ["<实际输入文件，含每篇 doc_id>"],
  "uncertainty_notes": ["<indirect 证据、存疑合并项>"],
  "change_log": []
}
```

## 5. 数字门槛（达不到诚实标 partial）

1. 100% 节点带 source_ref + mention_verbatim；100% 边带 evidence_span + source_ref + strength。
2. evidence_span 逐条可在原文中子串匹配（脚本核验通过）。
3. 查询 ≥3 个且真实执行；每个结果回溯 triple_id。
4. 合并/不合并决策 100% 带 basis；跨文档合并不把两篇的条件/样本/数值合成一个结论。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 材料只有摘要无正文 | 实体照抽，strength 全标 indirect + uncertainty_notes 说明，不升级为 direct |
| PDF 无法解析 | 对应 doc 标 unresolved，其余文档继续，整体 partial |
| 同名实体跨篇 | 不合并，进 conflicts 清单并写区分依据 |
| 关系证据冲突（两处说法矛盾） | 建两条边各带各自 evidence_span，矛盾登记 uncertainty_notes，不裁决 |
| 查询无结果 | empty + 原因，不造边 |
| 断言跨图表 | source_ref 指到图表 id + 页码，无位置则 not_found |
| output_contract 与本文冲突 | 以 case.json 为准 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 全字段落实
- [ ] schema 先行且随产物交付
- [ ] 每条三元组带 evidence_span（原文子串可匹配）+ source_ref + strength
- [ ] 实体无常识补全（mention_verbatim 校验通过）
- [ ] 合并/不合并均有依据；跨篇不错并条件与结果
- [ ] ≥3 个查询真实执行且可回溯
- [ ] not_found/冲突如实登记

## 8. 效率约束

预算 64 请求 / 900 秒。策略：子串核验、对齐校验、查询执行全部脚本化（scripts/verify_graph.py + query_graph.py）；模型请求只用于实体/关系抽取与依据撰写；先落盘最小 result.json。限额 ≤50 文件 / 2MB。

## 9. 最小示例（示意输出，非正式案例结果）

```json
{"triple_id":"T001","subject":"E_graphqa","predicate":"outperforms","object":"E_baseline_gnn","condition":"on Cora, 60% training ratio","evidence_span":"GraphQA outperforms the strongest GNN baseline by 3.2% on Cora","source_ref":{"doc_id":"primary","section_id":"S4","para_id":"P21","page_no":5},"strength":"direct","self_reported":true}
{"canonical_id":"E_graphqa","canonical_name":"GraphQA","aliases":[{"mention":"our method","basis":"defined in S3 P15: 'we refer to our approach as GraphQA'"}],"conflicts":[{"name":"GraphQA","docs":["primary","secondary"],"reason_not_merged":"secondary uses the name for a different model instance; no identity evidence"}]}
```

（以上为格式示意，正式结果以实际材料运行为准。）
