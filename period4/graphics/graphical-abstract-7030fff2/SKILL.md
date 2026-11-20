---
name: graphical-abstract-builder
description: |
  Graphical Abstract（图形摘要）Skill。单页内把"研究问题→方法→核心结果→结论"组织成
  自洽视觉语言：面板—要点映射（哪些上图、哪些进图注）、实体与空间关系正确、数据编码与
  图例一一对应（色觉差异与灰度打印兼容）、阅读顺序清晰、分层可编辑 SVG 源文件 + 合规
  导出。硬约束：每个实体/关系/数值可追到来源材料；同输入可稳定复现结构一致图稿；交付
  可编辑源文件而非位图。
---

# Graphical Abstract Builder — 图形摘要 Skill

## 1. 用途与适用范围

单页图形摘要三标准：① 实体/关系/数值可追溯到来源材料；② 同样输入稳定复现结构一致的图稿；③ 交付可编辑源文件。聚焦科学内容表达、版式、可编辑性与导出质量。

不负责：正文写作、统计分析、实验方案设计。

## 2. 输入识别（必做第一步）

1. `ls /input/`；读 case.json / task.md 与 workorder，记录 case_id。
2. 盘点：研究描述/实验记录、数据表、目标模板的尺寸与格式要求。
3. 建立"面板—要点"映射前的**事实清单**：研究问题、方法路线、核心结果（数值）、结论——逐条带材料定位。
4. 材料没有的数字/实体不上图；登记 gaps。

## 3. 工作流程

### Step 1 面板—要点映射（画什么）
- 单页分区：`问题 → 方法 → 结果 → 结论` 四区（或按材料实际结构），明确各区上图的要点。
- **哪些信息必须上图、哪些只能进图注**——判断写进 mapping 表，避免信息图式堆砌。
- 同输入两次运行产出同一结构（模板化布局：分区位置/阅读顺序固定，只有内容变）。

### Step 2 实体与空间关系（画得对）
- 研究对象（分子/细胞/材料/器件/样本）的层级、位置、相互作用方向、尺度关系正确。
- 通路方向与因果不颠倒；实体张冠李戴零容忍——每个实体带来源登记。

### Step 3 数据编码与图例（编码一致）
- 核心结果 → 颜色/长度/面积编码，与原始数据一一对应；色阶、单位、条件标签齐全。
- 色觉差异与灰度打印兼容：颜色之外冗余编码（形状/纹理/标签）。
- 图中数字全部能在来源材料找到对应记录（无来源即移除）。

### Step 4 版式与视觉层级（读得顺）
- 阅读顺序显式：编号面板 + 视线动线（问题→方法→结果→结论不迷路）。
- 留白、字号层级、视觉焦点控制；单页内无溢出、无重叠、小图可读。

### Step 5 可编辑源文件与导出
- SVG 分层命名（panel-question / panel-method / …），文字 `<text>` 可编辑。
- 渲染 PNG/PDF 预览；导出按目标格式检查：尺寸、分辨率（或矢量）、字体嵌入、画布无溢出；失败项如实登记。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "graphical_abstract",
  "status": "success | partial | failed",
  "panel_mapping": [{"panel":"question","points":["..."],"captions_only":["不上图要点"],"sources":["para1"]}],
  "entities": [{"entity_id":"e1","name":"...","source":"..."}],
  "data_encoding": [{"visual":"color ramp","data":"Table1 col2","legend_ref":"legend-1","colorblind_safe":true,"grayscale_ok":true}],
  "number_trace": [{"label":"42%","source":"Table 1"}],
  "layout": {"reading_order":["question","method","results","conclusion"],"overflow":false,"min_font_pt":8},
  "source_files": {"svg":"ga.svg","data":"ga_content.json","render_script":"render.py"},
  "renders": {"png":"preview.png","pdf":"preview.pdf"},
  "export_check": {"size_ok":true,"vector_or_dpi":true,"fonts_embedded":[],"issues":[]},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：number_trace 覆盖图中全部数字（无来源即删）；data_encoding 色觉/灰度自检；layout.overflow=false；SVG 可编辑；同输入重跑结构一致（模板驱动）。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 信息过多塞不下 | 上核心主线，其余进图注，取舍登记 |
| 数值无来源 | 移除该数字，gaps 登记 |
| 数据分类数与颜色不符 | 补色阶或改编码，不允许不一致 |
| 字体被替换 | 声明 + 登记，源文件指定字体族 |
| 预算不足 | 先 panel_mapping + 事实清单，渲染 partial |

## 6. 自查清单

1. [ ] 四区阅读顺序清晰？要点上图/图注分流明确？
2. [ ] 实体/方向/层级与材料一致？无张冠李戴？
3. [ ] 每个数字可溯源？图例与编码一一对应？
4. [ ] 色盲/灰度兼容？
5. [ ] SVG 可编辑、可复现？导出合规？
6. [ ] result.json 可解析、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。事实清单与面板映射先行；SVG 由 ga_content.json 模板化生成（保证可复现）；渲染导出单次执行。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"success",
 "panel_mapping":[{"panel":"results","points":["效率42%"],"captions_only":["机理细节"],"sources":["Table1"]}],
 "data_encoding":[{"visual":"bar length","data":"Table1 col2","legend_ref":"legend-1","colorblind_safe":true,"grayscale_ok":true}],
 "number_trace":[{"label":"42%","source":"Table 1"}],
 "layout":{"reading_order":["question","method","results","conclusion"],"overflow":false,"min_font_pt":9},
 "export_check":{"size_ok":true,"vector_or_dpi":true,"fonts_embedded":[],"issues":[]},
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
