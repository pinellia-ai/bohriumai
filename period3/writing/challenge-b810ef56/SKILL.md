---
name: evidence-driven-writer
description: |
  文献证据驱动写作 Skill。核心不是多写，而是"每句有依据的话都能被指认依据在哪、依据有多强"：
  从全文抽取可引用原文片段（含定位）、论断—来源关联（claim-evidence 矩阵）、引用准确性
  核验（真实性/著录/编号一致、识别二手转引）、证据分级（研究设计/样本量/共识度）与
  正文表述强度匹配、不确定性限定语。输出稿件 + 论断-证据表，他人可独立回查与重跑。
---

# Evidence-Driven Writer — 文献证据驱动写作 Skill

## 1. 用途与适用范围

让写出的每一条实质性论断满足"找得到、对得上、说得准、复得现"：
- 论断关联到具体文献的具体段落（不是"有引用"的表面功夫）；
- 引用真实存在、原文真的支持该论断（不是相近但更弱/更强的话）；
- 证据强度如实表达：相关不写成因果、单篇小样本不写成领域共识、冲突证据不隐藏；
- 论断清单、证据表、原文摘录、判定理由可独立回查重跑。

## 2. 输入识别（必做第一步）

1. `ls /input/`；读 case.json / task.md，记录 case_id。
2. 盘点材料：待写主题与要点、参考文献全文或摘录、引用格式要求。
3. 对每篇文献登记：类型（original research / review / guideline / preprint）、可及范围（全文/仅摘要）、版本。
4. 只有摘要时显式标注"仅摘要可核"，不得假装读过全文。

## 3. 工作流程

### Step 1 证据抽取（找得到）
- 从**全文而非仅摘要**抽取可直接引用的原文片段，逐条登记：`{ev_id, 文献, quote(逐字≤60词), locator(章节/页/段), source_type}`。
- 区分：数据性证据（结果段数值）、方法性证据（怎么做）、解释性证据（讨论段的作者解释）。

### Step 2 论断—来源关联（对得上）
- 把写作任务拆成论断单元清单：`{claim_id, text, 可判定性}`。
- 每条论断匹配支撑来源与**支撑范围**：该文献支持的是论断的全部还是一部分？一条论断需多篇文献时逐一登记；一篇文献支撑多条论断时复用登记。
- 匹配判定：`supports | partially_supports | related_only | contradicts`——related_only（只是主题相关）不得充当支撑。

### Step 3 引用准确性核验
- 文献真实性与著录信息（作者/年份/期刊/卷期/DOI）逐条核对。
- 参考文献编号与正文标记一致。
- 识别二手转引（A 引 B，你只有 A）——标注 secondhand，不直接引 B。
- 撤稿/版本差异线索如实登记。

### Step 4 证据强度分级与表述匹配（说得准）
- 每条论断定证据等级：`strong`（多来源一致+设计良好）/ `moderate`（单来源但有重复或大样本）/ `weak`（单篇小样本或间接证据）/ `conflicting`（来源冲突）。
- 正文表述强度必须与等级相称：
  - weak → "有研究报道…（单中心小样本）"，禁用"表明/证明"；
  - 相关 → "与…相关"，禁"导致"；
  - conflicting → 并列双方证据与可能原因；
  - 结论边界、适用人群、机制未明处加恰当限定语（不夸大也不含糊到无法判断）。

### Step 5 成稿与可复现交付（复得现）
- 按材料与格式要求成稿；每个论断句旁保留 claim_id 锚点（或用 source_map 关联）。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "evidence_driven_writing",
  "status": "success | partial | failed",
  "manuscript": "manuscript.md",
  "evidence_table": [
    {"ev_id":"e1","ref_key":"[4]","quote":"逐字原文","locator":{"section":"Results","page":6,"paragraph":2},
     "source_type":"original_research","scope":"仅支持缓解幅度，不含机制"}
  ],
  "claim_map": [
    {"claim_id":"c1","text":"...","evidence":["e1","e3"],"strength":"moderate",
     "match":"supports","text_strength_checked":true,
     "reason":"两来源一致，样本量中等，正文用'显示…相关'与等级相称"}
  ],
  "citation_audit": [{"ref_key":"[4]","real":true,"metadata_ok":true,"numbering_ok":true,"secondhand":false,"issues":[]}],
  "conflicts": [{"claim_id":"c2","sources":["e5","e7"],"note":"两文献结论相反，正文已并列"}],
  "hedges_audit": [{"claim_id":"c3","issue":"初稿写成因果，已改为相关表述"}],
  "needs_human_review": [], "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：quote 逐字真实；claim_map 每条有 match 判定与理由；related_only 不得计入支撑；conflicts 必须反映在正文中；稿件可编辑。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 论断找不到支撑 | 删除该论断或改为明确推断并标 needs_human_review |
| 仅摘要可及 | 证据标注 only_abstract，论断降级 |
| 引用编号与列表不一致 | 以列表为准修正，登记变更 |
| 预算不足 | 先完成 claim_map 与高优先论断（status=partial），再补成稿 |

## 6. 自查清单

1. [ ] 每条实质性论断在 claim_map 有登记与证据？
2. [ ] 每条证据 quote 逐字、定位可查？
3. [ ] 无 related_only 冒充支撑？无二手转引冒充一手？
4. [ ] 表述强度与证据等级匹配？冲突已并列？
5. [ ] 他人能否沿 claim_map→evidence_table→locator 回查？
6. [ ] result.json 可解析、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。先建证据表（一次抽取、复用于多条论断），再写正文；claim_map 与稿件同步产出。中断时优先保证 claim_map 完整（可复现核心）。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"success",
 "evidence_table":[{"ev_id":"e1","ref_key":"[4]","quote":"Treatment reduced pain scores by 30% (n=45).","locator":{"section":"Results","page":6,"paragraph":2},"source_type":"original_research","scope":"仅支持幅度"}],
 "claim_map":[{"claim_id":"c1","text":"该疗法可缓解疼痛","evidence":["e1"],"strength":"moderate","match":"supports","text_strength_checked":true,"reason":"单来源但 n=45，正文用'可缓解约30%'相称"}],
 "citation_audit":[{"ref_key":"[4]","real":true,"metadata_ok":true,"numbering_ok":true,"secondhand":false,"issues":[]}],
 "conflicts":[],"hedges_audit":[],"gaps":[],"uncertainty_notes":[],"changes":[]}
```

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段（如存在）。它定义本案例 `result.json` 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实内容**；contract 里有而本文件 §4 未描述的字段，按 contract 字段语义填实际结果，绝不遗漏；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：一律从 `/input/case.json` 原样读取，禁止自造。
3. **路径**：工作过程写 `/app/work/`；最终产物写 `/app/output/`，主输出为 /app/output/result.json（含 case.json 的 output_contract 全部字段）。
4. **尽早落盘**：先用最小可用结果写一次 /app/output/result.json（含 case.json 的 output_contract 全部字段），再增量增强——任何时刻中断都保证已落盘内容诚实、结构合法（status 如实标 partial）。
5. **不虚构**：无数据、无文件、无软件状态一律不编造；材料缺失写 gaps，无法判断写 uncertainty，禁止把推断写成事实。
6. **可核验**：每个关键结论保留来源定位（页/段/句/表号/图号或文件位置），他人可独立复核。
7. **交付物自检**：本 Skill 的提交材料为 SKILL.md + README.md（使用与方法说明）；运行时按上述契约执行案例。二者不一致处以本节契约为准。
