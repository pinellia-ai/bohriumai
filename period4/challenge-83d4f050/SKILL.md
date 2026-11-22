---
name: pathway-map-builder
description: |
  生物机制图与通路图 Skill（biological_mechanism_pathway）。把机制陈述画成可逐条质疑的图：
  生物实体命名规范（基因/蛋白书写区分、物种前缀、复合物）、相互作用语义映射（激活/抑制/
  磷酸化/结合/转运 → 可区分箭头）、通路方向与拓扑正确（受体—胞内—核层级、跨膜位置、
  反馈环走向）、图例/颜色/线宽编码与数据一致。硬约束：每个实体与边可回溯输入材料或权威
  命名；交付分层可编辑 SVG + 渲染件；改一个标签可重新导出。
---

# Pathway Map Builder — 生物机制图与通路图 Skill

## 1. 用途与适用范围

机制图是**可以被逐条质疑的机制陈述**：每个箭头、每处定位都带语义，画错一处=给出错误论断。聚焦：实体命名、相互作用语义、通路方向拓扑、图例与数据编码、可编辑源文件与导出。

不负责：统计分析、实验方案设计、论文写作、版式美化。

## 2. 输入识别（必做第一步）

1. `ls /input/`；读 case.json / task.md 与 workorder，记录 case_id。
2. 盘点：机制描述文字、数据表（表达量/显著性）、原图片、权威命名参考（若提供）。
3. 逐条登记材料中的机制陈述句（作为绘制依据清单），每句带定位。
4. 材料未给的实体/数值不构造；登记 gaps。

## 3. 工作流程

### Step 1 实体与命名规范
- 区分基因与蛋白书写（基因斜体/蛋白正体约定，按材料学科惯例），物种前缀（h/m），同义名与旧名统一为材料所用主名。
- 复合物与家族成员显式标注（"复合物A（含X、Y）"）。
- 每个实体：`{entity_id, display_name, type(protein/gene/complex/cell/compartment), source(材料位置)}`。
- 无法从材料确认的命名 → 中性名 + needs_human_review，不用疑似错误名称。

### Step 2 相互作用语义映射
文字关系 → 可区分视觉语法（图例逐一说明）：
| 原文表述 | 视觉 |
|---|---|
| 促进/激活 | 实线箭头 → |
| 抑制 | T 型端 ┤ |
| 磷酸化/泛素化 | 圆点修饰符 + 标签 |
| 结合 | 双向短线 |
| 转运 | 空心箭头 + 区室穿越 |
| 募集 | 虚线箭头 |
证据强度/不确定性：实线=材料明确、虚线=材料含糊，逐条登记 evidence。

### Step 3 通路方向与拓扑（画错最致命处）
- 明确上下游顺序与方向：受体→胞内→核内的空间层级；**跨膜受体画在膜上**（双层之间）、胞内蛋白在胞浆、核蛋白在核内——区室位置即语义。
- 分支与反馈环走向与材料陈述一致；方向颠倒/包含画并列=0容忍错误，绘制后按陈述句逐条核对。

### Step 4 图例与数据编码
- 颜色/线宽/节点大小→表达量/显著性/置信度的映射与数据表逐项一致；图例、图面、数据三者自洽。
- 数值标签标注数据来源位置。

### Step 5 可编辑源文件与导出
- SVG 分层：compartment 层（膜/核/胞浆）→ entity 层 → edge 层 → label 层 → legend 层；节点命名 `ent-<id>`，文字 `<text>` 可编辑。
- 渲染 PNG/PDF 预览；导出检查（矢量、字体、分辨率、图层保留）逐项记录。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "biological_mechanism_pathway",
  "status": "success | partial | failed",
  "statement_checklist": [{"statement":"材料陈述句","loc":"para 3","drawn":true,"edge_ids":["edge1"]}],
  "entities": [{"entity_id":"e1","display_name":"EGFR","type":"protein","compartment":"membrane","source":"para2"}],
  "edges": [{"edge_id":"edge1","from":"e1","to":"e2","semantic":"phosphorylation","visual":"dot+label","evidence":"EGFR phosphorylates AKT","strength":"explicit"}],
  "legend_consistency": {"legend_items":6,"mapped":6,"mismatches":[]},
  "compartment_check": {"membrane_proteins_on_membrane":true,"direction_reversed":0},
  "source_files": {"svg":"pathway.svg","render_script":"render.py"},
  "renders": {"png":"preview.png","pdf":"preview.pdf"},
  "export_check": {"vector":true,"fonts_embedded":[],"layer_preserved":true,"issues":[]},
  "needs_human_review": [], "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：statement_checklist 每句机制陈述有对应边或登记未画原因；compartment_check 全过；图例无 mismatch；SVG 可编辑可重导出。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 陈述句关系含糊 | 虚线+note，不猜方向 |
| 数据表与描述冲突 | 并列登记，以数据表为准绘制数值，冲突上报 |
| 区室信息缺失 | 用默认区室布局 + needs_human_review |
| 预算不足 | 先实体/边清单（科学正确性核心），渲染 partial |

## 6. 自查清单

1. [ ] 每个实体/边可回溯材料？命名规范无同名异义？
2. [ ] 激活/抑制/修饰语法可区分且与图例一致？
3. [ ] 上下游方向、跨膜位置、区室无误？
4. [ ] 数值编码与数据表一致？图例自洽？
5. [ ] SVG 分层可编辑？改标签可重导出？
6. [ ] result.json 可解析、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。陈述句清单与实体边抽取一次完成；SVG 由脚本从 JSON 生成；渲染导出单次执行。中断时清单完整即 partial。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"success",
 "statement_checklist":[{"statement":"配体结合激活受体","loc":"para1","drawn":true,"edge_ids":["edge1"]}],
 "entities":[{"entity_id":"e1","display_name":"R","type":"protein","compartment":"membrane","source":"para1"}],
 "edges":[{"edge_id":"edge1","from":"e1","to":"e2","semantic":"activation","visual":"solid arrow","evidence":"binding activates R","strength":"explicit"}],
 "legend_consistency":{"legend_items":3,"mapped":3,"mismatches":[]},
 "compartment_check":{"membrane_proteins_on_membrane":true,"direction_reversed":0},
 "export_check":{"vector":true,"fonts_embedded":[],"layer_preserved":true,"issues":[]},
 "gaps":[],"uncertainty_notes":[],"changes":[]}
```

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段（如存在）。它定义本案例 `result.json` 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实内容**；contract 里有而本文件 §4 未描述的字段，按 contract 字段语义填实际结果，绝不遗漏；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：一律从 `/input/case.json` 原样读取，禁止自造。
3. **路径**：工作过程写 `/app/work/`；最终产物写 `/app/output/`，主输出为 /app/output/result.json（含 case.json 的 output_contract 全部字段）。
4. **尽早落盘**：先用最小可用结果写一次 /app/output/result.json（含 case.json 的 output_contract 全部字段），再增量增强——任何时刻中断都保证已落盘内容诚实、结构合法（status 如实标 partial）。
5. **不虚构**：无数据、无文件、无软件状态一律不编造；材料缺失写 gaps，无法判断写 uncertainty，禁止把推断写成事实。
6. **可核验**：每个关键结论保留来源定位（页/段/句/表号/图号或文件位置），他人可独立复核。
7. **交付物自检**：本 Skill 的提交材料为 SKILL.md + README.md（使用与方法说明）；运行时按上述契约执行案例。二者不一致处以本节契约为准。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 交付量化对账：statement_checklist.csv（机制陈述/边ID/位置）逐句
2. compartment_check 断言
3. legend mismatches=0 计数。
