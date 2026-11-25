---
name: multidoc-comparison-integration
description: |
  多文档比较与整合 Skill：读 /input/comparison-workorder.json 与全部语料文档，为同一研究
  问题下的多篇论文建立统一字段比较矩阵，逐格绑定 source_document_id + paragraph_id +
  逐字 quote；定量合成前先做可比性判定（task/metric/units/material/pollutant/budget），
  保留全部不可比与未报告条件，不合并不同数据集。方法主线：工单解析 → 字段字典 → 逐篇
  抽取 → 两级对齐（字段落格+条件归一）→ 一致性/冲突判定与归因 → 脚本校验落盘。
  单篇摘要不构成多文档比较；冲突必须归因到样本/方法/条件/指标差异，查得回、说得清。
---

# 多文档比较与整合 Skill（multidoc-comparison-integration）

## 1. 用途与适用范围

- 用途：给定比较工单与一组论文文档，输出统一字段比较矩阵、可比性评估、一致性/冲突结论（带归因）与跨文档证据组织，全部逐格可回溯。
- 适用：5–10 篇带段落定位的文本材料；比较维度为对象/数据/方法/条件/指标/结论/局限。
- 核心原则：**对得齐（同一套字段定义）、填得准（值来自它标注的那篇）、说得清（差异归因可核查）、查得回（逐格定位）。单篇摘要不算多文档比较；不同数据集不合并。**

## 2. 输入识别（Step 0，必做）

1. 读 `/input/comparison-workorder.json`：比较任务、目标论文集合（document_id 清单）、比较维度、要求的字段组、output_contract。工单缺失 → status=failed。
2. 盘点语料文档：逐份登记 document_id、路径、页数/段落数。文档缺失或多版本并存 → 登记实际使用的版本；某篇缺失 → 矩阵中该行标 missing-source，不用其他论文补。
3. 读 `/input/case.json` 取 case_id（原样保留）。
4. 建目录 `/app/work/`、`/app/output/`。

## 3. 工作流程（6 步流水线）

### Step 1 字段字典（产出 work/field-dictionary.json）
- 为字段组定义统一字段：object/data_source/method/conditions/metric/conclusion/limitation 等，每个字段含：名称、定义、允许取值类型、取值规则（逐字取/归一规则/允许的归一动作）。
- 验收断言：覆盖工单要求的全部字段组；每个字段定义唯一，各论文共用同一套。

### Step 2 逐篇抽取（产出 work/per-doc-extracts.json）
- 按字段字典逐篇抽取：每格记录 value、units、数据集/样本标识、指标口径、paragraph_id、quote（逐字、子串可匹配）。
- 值必须来自它标注的那篇论文；单位、数据集版本、指标口径随值记录，不脱钩。
- 原文未报告 → value=null + status=not_reported；不填 0、不从其他论文借值。

### Step 3 两级对齐（产出 work/alignment.json）
- 第一级（落格）：每篇的值落到统一字段列。
- 第二级（条件归一）：归一数据集版本、样本量、划分方式、基线模型、评价口径后，判定哪些论文在同一条件下可比（comparable_subset），哪些只能在子集内比较，哪些完全不可比（noncomparable，登记原因）。
- 验收断言：任何跨论文定量对照都先通过可比性判定（task、metric、units、material、pollutant、budget 六项逐项核对）。

### Step 4 一致性与冲突判定（产出 work/consistency.json）
- 对每个比较维度：一致 / 部分一致 / 冲突。
- 冲突必须归因：差异来自样本、方法、条件还是评价指标；归因要落到双方具体段落，可核查；无法归因 → 如实写"cannot attribute with given sources"，并保留双方原话。
- 不把"指标不同导致的数字差异"误报为结论冲突。

### Step 5 跨文档证据组织（产出 work/evidence-cards.json）
- 证据卡片：每张卡 = 一条跨文档结论 + 支持它的各文档证据（document_id + paragraph_id + quote）。
- 主题整合报告段落化：每段可回指卡片，卡片可回指原文。

### Step 6 校验与落盘（scripts/validate_matrix.py）
```bash
python3 /skills/weekly-skill/scripts/validate_matrix.py --result /app/output/result.json --workorder /input/comparison-workorder.json
```
校验：矩阵覆盖工单全部 document_id × 字段；每格非空时有 quote 且能在对应文档文本匹配；可比性判定先行；冲突格有归因。先落骨架再充实。

## 4. 输出契约（result.json 逐字段）

| 字段 | 要求 |
|---|---|
| `case_id` | 与输入一致 |
| `status` | `success` / `partial`（部分文档缺失或大量字段不可抽取）/ `failed` |
| `field_dictionary` | 字段名 → 定义、取值规则 |
| `comparison_matrix[]` | 每行一个 document_id；每格 {field, value, units, dataset, metric口径, source_document_id, paragraph_id, quote, status(reported/not_reported/noncomparable)} |
| `comparability` | 六项判定 task/metric/units/material/pollutant/budget 逐项结论；comparable_subset 与 noncomparable 清单及原因 |
| `consistency[]` | 每个比较维度：verdict（consistent/partially_consistent/conflict）+ 归因（attribution: sample/method/conditions/metric + 双方 paragraph_id + 原话）|
| `evidence_cards[]` | 结论 + 各文档证据定位 |
| `synthesis` | 主题整合报告（每段回指 evidence_cards） |
| `unreported[]` | 未报告条件清单 |
| `uncertainty[]` / `change_log[]` | 不确定项与修订记录 |

示例（示意，非正式案例结果）：
```json
{"case_id":"demo-cmp","status":"success",
 "comparison_matrix":[
  {"source_document_id":"docA",
   "cells":{"metric_value":{"value":"78.4","units":"%","dataset":"dye RhB","metric":"removal efficiency, 120 min",
     "paragraph_id":"p09","quote":"the removal efficiency of RhB reached 78.4% after 120 min","status":"reported"},
   "catalyst_dose":{"value":"0.5","units":"g/L","paragraph_id":"p08","quote":"0.5 g/L catalyst was added","status":"reported"}}},
  {"source_document_id":"docB",
   "cells":{"metric_value":{"value":"91.0","units":"%","dataset":"dye MB","metric":"removal efficiency, 60 min",
     "paragraph_id":"p04","quote":"91.0% of MB was removed within 60 min","status":"reported"},
   "catalyst_dose":{"value":null,"units":null,"paragraph_id":null,"quote":null,"status":"not_reported"}}}],
 "comparability":{"task":"both photocatalytic dye degradation","metric":"different contact times (120 vs 60 min) → not directly comparable",
   "units":"both %","material":"different dyes (RhB vs MB) → do not pool","pollutant":"RhB vs MB → noncomparable","budget":null,
   "comparable_subset":[],"noncomparable":["docA vs docB quantitative pooling (different dye + contact time)"]},
 "consistency":[{"dimension":"conclusion_direction","verdict":"partially_consistent",
   "attribution":{"cause":"conditions","detail":"不同染料与接触时间，方向一致但数值不可比",
     "docA_loc":{"paragraph_id":"p09","quote":"78.4% after 120 min"},"docB_loc":{"paragraph_id":"p04","quote":"91.0% of MB within 60 min"}}}],
 "evidence_cards":[],"synthesis":"","unreported":["docB catalyst dose"],"uncertainty":[],"change_log":[]}
```

## 5. 数字门槛

- 矩阵覆盖 100%：工单 document_id × 要求字段组逐格有值或显式 status，不允许空格。
- 引文可核验率 100%：非空格 quote 子串匹配通过。
- 可比性先行：任何跨论文数字对照前必须有六项判定记录；缺失判定即不合格。
- 冲突必归因：conflict 无 attribution 不合格；无法归因也要写明。
- 不合并：不同数据集/染料/口径的数值不出现任何 pooled 合成数。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 工单缺失 | status=failed，不虚构 |
| 某篇文档缺失/多版本 | 矩阵行标 missing-source / 登记实际版本；不借值 |
| PDF 解析失败/图表读不出 | 该格 status 登记原因，不猜值 |
| 论文主题与比较问题不相关 | 行标 irrelevant + 依据，不入合成 |
| 同一论文两版本数值不同 | 登记两处定位，标 source_conflict，不仲裁 |
| 指标口径不同（如 120min vs 60min） | comparable_subset 排除；差异标注为 metric 差异非结论冲突 |
| 结论冲突且无法归因 | verdict=conflict + cannot attribute + 双方原话并列 |
| 单位不一致 | 先声明换算规则并记录，或判不可比；不静默换算 |

## 7. 自查清单

- [ ] case_id 原样保留
- [ ] 字段字典唯一且覆盖工单字段组
- [ ] 矩阵 100% 覆盖 document_id × 字段
- [ ] 每格 value 来自其标注文档，units/dataset/口径随值
- [ ] 六项可比性判定先于任何定量合成
- [ ] 冲突有归因且落到双方段落
- [ ] 无 pooled 合成数
- [ ] validate_matrix.py 全项通过

## 8. 效率约束

预算内：逐篇抽取批量进行；先落骨架（矩阵空格+status）再充实；脚本一次跑通，失败格定点修复。

## 9. 最小示例

见 §4 示意 JSON（标明为示例）。流程：工单 → 字段字典 → 逐篇抽取 → 对齐 → 一致性 → 落盘。
