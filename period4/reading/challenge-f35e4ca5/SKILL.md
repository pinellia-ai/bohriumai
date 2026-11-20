---
name: figure-data-extraction
description: |
  科研图表解析 Skill。输入论文原始图片（1张/例）与全部原表，完成坐标轴/单位/刻度识别、
  曲线与数据点读取、误差线与显著性标记还原，输出带单位、精度与误差范围的结构化数据
  （CSV + result.json），每条数值保留可复核的读取路径。明确区分"图中直接可读 / 合理推断 /
  无法确定"，未提供像素的图注只登记缺口、不构造数据。
---

# Figure Data Extraction — 科研图表解析 Skill

## 1. 用途与适用范围

从真实论文图片中"读得准、提得全、讲得清、交得出"：识别坐标轴类型（线性/对数/双轴）、刻度起点与间隔、单位量级；完整提取曲线、数据点、误差线、峰位峰强、显著性标记、比例尺、子图编号；输出带单位与精度的结构化数据并保留读取路径。

适用：曲线图数据提取、光谱峰识别、统计图表（柱/箱线/误差线）、显微图像比例尺换算、多子图综合理解。不适用：无图像输入的纯文本任务；与图表无关的请求——说明并拒答。

## 2. 输入识别（第一步，必做）

1. `ls /input/`；确认每例的**必做对象：1 张原图片 + 全部原表**（组织方修订 v2）。图片通常为 PNG/JPG，表格随材料给出。
2. 读取 case.json / task.md：记录 case_id、图号与图注文本、领域标签。
3. **按实际材料更正领域/图型标签**：材料是什么就是什么，不依据（可能错误的）标签臆测图型。
4. **缺口登记**：图注提到但未提供像素的其它图，在 `gaps` 中列出"未提供像素，无法解析，非本任务隐藏要求"，**禁止构造数据**。
5. 图片文件缺失或损坏：status=failed，写明原因，不得编造数值。

## 3. 工作流程

### Step 1 坐标轴识别（读得准）
- 用图像工具查看原图。逐轴记录：轴名、类型（线性/对数/双轴）、刻度起点、间隔、单位及量级前缀。
- 对数轴必须显式标注 `log-scale: true`，并按对数规则读取——**不把对数轴当线性轴**。
- 单位核对：mV/V、ms/s、nm/µm 等量级逐一确认；有双轴时明确每个数据系列挂在哪根轴。

### Step 2 数据提取（提得全）
- 曲线/散点：按像素-坐标映射（两端刻度锚点标定）读取数据点，输出 CSV：`series,x,y[,y_err]`。
- 误差线：区分 ±SD / ±SEM / CI（依图注），换算成数值列。
- 显著性标记：*、**、*** 与 ns 逐个登记（对应关系以图注为准）。
- 比例尺（显微图）：读比例尺长度，换算系数写入输出，测量值按比例尺换算并注明精度。
- 峰位/峰强（光谱）：峰位（x 单位）、峰强（y 单位）、半高宽如可读。
- 非数据元素（网格线、图例框、水印）**不得**混入数据。

### Step 3 趋势与结论（讲得清）
每条趋势结论标注来源等级：`direct`（图中直接可读）/ `inference`（合理推断，写出推断链）/ `undetermined`（无法确定）。
- 区分"图中直接可读"与"正文/图注转述"；统计结论必须指向具体的显著性标记与比较对。
- 不跨子图错配编号；多子图先建立 `子图编号↔图注↔正文` 对应表再总结。

### Step 4 结构化输出（交得出）
- `data.csv`：每个数据系列一段，带表头注释（单位、轴类型、误差含义）。
- `result.json`：见 §4。

## 4. 输出契约

```json
{
  "case_id": "<原样填写>",
  "task": "figure_data_extraction",
  "status": "success | partial | failed",
  "figure": {
    "file": "<图片文件名>",
    "axes": [{"axis":"x","name":"Time","type":"linear|log","unit":"s","ticks":{"start":0,"step":10}}],
    "series": [{"name":"...","points_extracted":12,"csv_ref":"data.csv#series1",
                "axis_assignment":"left|right","precision_note":"像素分辨率约0.2单位"}],
    "annotations": {"error_bars":"±SD per caption","significance":"* = p<0.05 (a vs b)","scale_bar":"10 µm"}
  },
  "tables": [{"table_id":"Table 1","file":"<原表文件或位置>","summary":"...", "rows_extracted": 8}],
  "trend_conclusions": [{"text":"...","grade":"direct|inference|undetermined","evidence":"图中哪个区域/标记"}],
  "reading_path": [{"item":"series1 第5点","how":"像素(412,208)按轴锚点(0,0)/(50,100)线性映射","result":"x=25.3 s, y=48.7 mV"}],
  "gaps": ["图注提到图2b但未提供像素——未解析，不构造"],
  "uncertainty_notes": ["读取精度受图像分辨率限制，数值保留3位有效数字"],
  "changes": []
}
```

硬性要求：case_id 原样保留；数值必须带单位与精度说明；`direct/inference/undetermined` 三级标注不可缺；CSV 与 result.json 数值一致。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 图片缺失/损坏/为占位图 | status=failed，写明；不编造 |
| 对数轴 + 刻度标签被裁剪 | 标 undetermined，说明无法标定 |
| 图注与图内容冲突 | 两者并列记录，数值以图为准，note 注明冲突 |
| 低分辨率导致点读取不确定 | 给出读取区间而非单值，precision_note 说明 |
| 表格为图片扫描 | 尝试 OCR；失败则登记 gaps |

## 6. 自查清单

1. [ ] 坐标轴类型/单位/量级逐轴核对（mV≠V，log≠linear）？
2. [ ] 数据点、误差线、显著性标记、比例尺提取完整，无非数据元素混入？
3. [ ] 每个数值可沿 reading_path 复核？
4. [ ] 未提供像素的图只登记 gaps，没有构造任何数据？
5. [ ] trend_conclusions 三级标注齐全？
6. [ ] result.json 可被 json.tool 解析，case_id 原样？

## 7. 效率约束

预算 64 次模型请求 / 900 秒 / 单响应 16384 token。图像查看按区域裁剪聚焦；先出全部数据点的最小可用 CSV，再补 annotations 与结论。中断时保证已提取部分完整可交（status=partial）。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","task":"figure_data_extraction","status":"success",
 "figure":{"file":"fig2a.png","axes":[{"axis":"x","name":"Time","type":"linear","unit":"min","ticks":{"start":0,"step":5}}],
   "series":[{"name":"control","points_extracted":6,"csv_ref":"data.csv#s1","axis_assignment":"left","precision_note":"±0.3 OD"}]},
 "trend_conclusions":[{"text":"处理组吸光度随时间线性上升","grade":"direct","evidence":"fig2a 蓝色曲线0-30min"}],
 "gaps":["图注提及fig2b电镜照片未提供像素"],"uncertainty_notes":["y读取精度±0.3"],"changes":[]}
```

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段（如存在）。它定义本案例 `result.json` 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实内容**；contract 里有而本文件 §4 未描述的字段，按 contract 字段语义填实际结果，绝不遗漏；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：一律从 `/input/case.json` 原样读取，禁止自造。
3. **路径**：工作过程写 `/app/work/`；最终产物写 `/app/output/`，主输出为 /app/output/result.json（含 case.json 的 output_contract 全部字段）。
4. **尽早落盘**：先用最小可用结果写一次 /app/output/result.json（含 case.json 的 output_contract 全部字段），再增量增强——任何时刻中断都保证已落盘内容诚实、结构合法（status 如实标 partial）。
5. **不虚构**：无数据、无文件、无软件状态一律不编造；材料缺失写 gaps，无法判断写 uncertainty，禁止把推断写成事实。
6. **可核验**：每个关键结论保留来源定位（页/段/句/表号/图号或文件位置），他人可独立复核。
7. **交付物自检**：本 Skill 的提交材料为 SKILL.md + README.md（使用与方法说明）；运行时按上述契约执行案例。二者不一致处以本节契约为准。
