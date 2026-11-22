---
name: schematic-builder-editable
description: |
  科研示意图生成与编辑 Skill（可编辑关系示意图 editable_relationship_schematic）。
  从来源材料抽取实体—关系清单（可核对）→ 分层 SVG 绘制（关系类型用可区分箭头，层级/
  分组/上下游方向正确）→ 图例与数据映射逐项一致 → 渲染 PNG/PDF 预览 → 合规导出。
  硬约束：图中每个实体、关系、数值可追溯到来源材料；不发明来源中不存在的实体/数值/单位；
  交付可编辑源文件 + 导出件，改一个标签无需重画。
---

# Schematic Builder — 科研示意图 Skill（来源可追溯 + 可编辑）

## 1. 用途与适用范围

把实验流程、结构关系、机制链条画成"读者一眼读懂、审稿人挑不出错"的示意图。三条可检验标准：
1. 图中每个科学实体、关系、数值与单位**可追溯到来源材料**；
2. 图例、颜色映射与所依据的数据**逐项一致**，数据改动后图可同步更新；
3. 交付**可编辑源文件 + 合规导出件**双形态。

不负责：统计图表数值计算、海报版式美化、正文写作。边界外请求说明并拒答。

## 2. 输入识别（必做第一步）

1. `ls /input/`；读 case.json / task.md 与 workorder，记录 case_id。
2. 盘点来源材料：文字描述、数据表、原图片（如 figure03 等组织方指定对象）。
3. 建立**来源清单**：每个文件的角色（实体来源/关系来源/数值来源/样式参考）。
4. 材料中未提供的像素/数值**不构造**——登记 gaps（如"图注提及但未给像素的图"）。

## 3. 工作流程

### Step 1 实体—关系抽取（图对不对的基础）
从来源材料抽取**实体—关系清单**，逐条可核对：
- 实体：`{entity_id, name(原文原词), attributes(浓度/时间点/状态——仅限材料实际给出), source(文件+位置)}`。
- 关系：`{from, to, type(激活/抑制/包含/上下游/因果/时序), direction, evidence(原文短句)}`。
- **不发明**：来源材料中不存在的基因名、浓度、时间点、单位一律不出现。
- 清单先交付自查：每条关系能在原文找到依据句。

### Step 2 分层 SVG 绘制（结构正确）
- 关系类型用**可区分的视觉语法**：激活=实线箭头、抑制=T型端、包含=嵌套边界、时序=编号节点——图例逐一说明。
- 层级/方向正确：上下游顺序、包含嵌套、分组边界不画错；箭头方向与清单一致。
- 布局规范：分区、留白、对齐、字号层级、元素避让（无重叠/溢出/引导线交叉），小尺寸印刷可读。
- SVG 分层：`<g id="layer-entities"> / layer-relations / layer-labels / layer-legend`，节点命名 `ent-<entity_id>`，文字全部 `<text>` 可编辑。

### Step 3 图例与数据映射（逐项一致）
- 图例项、颜色、形状与数据表分类/数值**严格对应**：颜色数=分类数，逐项对照。
- 数值标签标注来源（`[Source: Table 2]`）。
- 数据更新同步：实体/关系来自结构化清单（entities.json），改清单重跑脚本即重绘——支持"改动数据后图同步更新"。

### Step 4 渲染与导出（交得出）
- 渲染 PNG/PDF 预览（供检查科学内容与布局）。
- 导出适配：分辨率（≥300 dpi 或矢量）、字体嵌入、线宽、色彩空间按目标模板/期刊要求逐项检查并记录。
- 导出失败项（如字体缺失）如实登记，不冒充已嵌入。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "editable_relationship_schematic",
  "status": "success | partial | failed",
  "entity_relation_list": {"entities":[...],"relations":[...],"unmatched_inputs":["来源提及但无法绘制项"]},
  "source_files": {"svg":"schematic.svg（分层可编辑）","entities":"entities.json","render_script":"render.py"},
  "renders": {"png":"preview.png","pdf":"preview.pdf"},
  "legend_consistency": {"legend_items":5,"mapped_categories":5,"mismatches":[]},
  "traceability": [{"element":"ent-TNF-alpha","source":"描述段 para2 / data.csv row3"}],
  "export_check": {"dpi":"vector","fonts_embedded":["..."],"stroke_width_ok":true,"colorspace":"RGB/sRGB","issues":[]},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：无来源依据的实体/关系不得上图；SVG 可编辑（分层+命名+文字可选）；traceability 覆盖全部实体与关系；legend_consistency 无 mismatch 才允许 success。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 材料实体过多画不下 | 分主图+附录图，或分组折叠，登记取舍 |
| 关系类型原文含糊 | 用中性箭头 + note 标注不确定，不猜方向 |
| 字体不可用 | 用通用字体族声明，登记导出风险 |
| 渲染工具缺失 | 保留 SVG 源文件 + 手工核对清单，status=partial |
| 预算不足 | 先 entity_relation_list + 最小 SVG，渲染 partial |

## 6. 自查清单

1. [ ] 每个实体/关系/数值有来源？无发明内容？
2. [ ] 箭头类型、方向、层级与清单一致？抑制≠激活？
3. [ ] 图例与数据逐项一致？
4. [ ] SVG 分层命名、文字可编辑？改标签无需重画？
5. [ ] PNG/PDF 预览已渲染？导出参数逐项检查？
6. [ ] result.json 可解析、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。清单先行（一次抽取）；SVG 由脚本从 entities.json 生成（保证数据更新可重绘）；渲染与导出检查合并单次执行。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"success",
 "entity_relation_list":{"entities":[{"entity_id":"e1","name":"Receptor X","source":"para2"}],
   "relations":[{"from":"e1","to":"e2","type":"activation","evidence":"X promotes Y expression"}],"unmatched_inputs":[]},
 "legend_consistency":{"legend_items":2,"mapped_categories":2,"mismatches":[]},
 "traceability":[{"element":"ent-e1","source":"para2"}],
 "export_check":{"dpi":"vector","fonts_embedded":["DejaVuSans"],"stroke_width_ok":true,"colorspace":"sRGB","issues":[]},
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
1. 交付量化对账：traceability.csv（实体/关系/来源定位）逐条
2. legend_consistency 计数（mismatch=0）
3. statement_checklist 逐句核对表。
