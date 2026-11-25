---
name: scientific-figure-parsing
description: |
  科研图表解析 Skill：把科研图表（曲线图/统计图/光谱图/显微图/多子图）读成带单位、精度与误差范围的结构化数据。
  方法主线：五步流水线——图表清点→坐标轴判别与像素标定→元素提取（曲线/数据点/误差线/显著性标记/比例尺）→
  科学解释三级标注（图中直接可读/合理推断/无法确定）→结构化落盘 result.json。
  全程离线、如实约束：每个数值可回指原图位置与读取依据；读不出、不确定的如实标 unavailable/uncertain，不编造。
---

# 科研图表解析 Skill（scientific-figure-parsing）

## 1. 用途与适用范围

- 用途：输入一张（或一组）科研图表图片及其图注/正文描述，输出可复核的结构化解析结果：坐标轴类型与刻度、单位、数据系列、关键数值（峰位/峰强/均值±误差/显著性标记）、趋势结论及其证据定位。
- 适用：折线图、散点图、柱状图、误差线图、简单光谱图、带比例尺的显微图、多子图（a/b/c/d 编号）。
- 不适用/降级：无任何坐标刻度且无比例尺的纯示意图（输出 status=partial，只报告可判读元素）；被严重裁剪或过曝无法标定的图（见 §6）。
- 核心原则：**不把 mV 当 V，不把对数轴当线性轴，不把非数据元素当数据，不确定不写成事实。**

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：提取 `case_id`、任务说明、材料清单、output_contract 全字段（逐字段抄录到工作笔记，缺字段就是缺口）。
2. 盘点材料文件（图片/PDF/文本）。执行 `scripts/inventory.py --input-dir <材料目录>`，产出 `work_inventory.json`：
   - 每个文件的 kind（image/pdf/text/unknown）、尺寸/页数、md5。
   - 图片文件给出像素尺寸；PDF 给出页数。
3. 材料缺失或图片为空 → `result.json` 写 `status="failed", reason="material missing"`，**不虚构**。
4. 建立工作目录：`/app/work/`（过程产物）、`/app/output/`（最终 result.json 与预览）。

## 3. 工作流程（5 步流水线）

### Step 1 图表清点与图注关联
- 从 PDF/文本中用 `pdf-text-tool`/文本读取抽取所有 `Figure N`/`Fig. N`/`Table N` 题注段落及正文提及（"Fig. 3a shows..."）。
- 产出 `work_figures_index.json`：`[{figure_id, caption, panel_ids:["a","b",...], mentioned_in:[{locator}], image_file|null}]`。
- 题注与图片对不上的（有图无文/有文无图）记入 `gaps`，不强行配对。
- **题面修订注意**：每例必做对象是该例给出的 1 张原图片及全部原表；未给像素的其他图注明确列缺口，不构造。

### Step 2 坐标轴判别与像素标定
- 人工/视觉读图取得参照信息：每条轴 ≥2 个刻度的像素位置 + 刻度标注值 + 单位字符串。
- 运行 `scripts/calibrate.py --spec work_axis_spec.json`：
  - 轴类型判别：等距刻度值等差 → linear；刻度值等比（比值≈常数）→ log10；左右轴量纲不同 → dual-axis，输出时每系列必须带 `axis_ref`。
  - 输出像素→数据坐标的仿射/对数映射 `axis_map`，含 `r_squared`（拟合质量）与 `unit`。
- 验收断言：`calibrate.py` 退出码 0，`axis_map.r_squared ≥ 0.999`（linear）/残差 ≤ 0.5%（log）；不达标 → 该轴标 `uncertain`，禁止继续读数出硬值。
- **单位量级守卫**：从图注/正文正则抽取单位（`mV|V|µm|mm|...`），若与刻度标注单位前缀冲突（如刻度写 500 mV 而正文说 V），报 `unit_conflict` 到 `uncertainties`，以刻度标注为准并说明依据。

### Step 3 元素提取（提得全）
- 依 `axis_map` 提取：曲线数据点、散点、柱高、误差线（上下须）、峰位峰强、显著性标记（*, **, ***, n.s. 及其归属比较组）、比例尺（长度像素→实际尺寸换算）、子图编号归属。
- 曲线逐像素追踪用 `scripts/extract_curve.py`（输入：色掩码像素坐标 JSON 或手动取点列表；输出：按 series 分组的去重数据点 CSV）。
- 非数据元素（图例框、网格线、坐标框、文字水印）必须在 `excluded_nondata` 中列出，证明"没把它们当数据"。
- 每个提取元素必须带：`evidence`（原图位置描述，如 "Fig.2a, y-axis tick at x_px=63"）、`method`（tick calibration / pixel tracing / caption text）、`confidence`（high/medium/low）。

### Step 4 科学解释三级标注
- 每条结论必须标注来源级别：
  - `direct`：图中直接可读（如"Fig.1b 中 t=10 s 处 y≈3.2±0.1 mV"，可指到像素与刻度）。
  - `inference`：合理推断（如"曲线在 5–15 s 进入平台期"，依据斜率阈值判定，阈值写明）。
  - `undetermined`：无法确定（图中无支撑信息），**不得写成事实**。
- 显著性结论只复述标记本身含义（p<0.05 等），不引入图注外的统计解释。

### Step 5 结构化落盘
- 先写 `/app/output/result.json` 最小版（case_id + status + 主结果骨架），再逐步充实——保证任何中断都有可评分产物。
- 数值数据另导出 `/app/output/extracted_data.csv`（列：series_id,x_value,y_value,y_err,axis_ref,unit,evidence）。
- 若有可编辑产物（如标注版图表），附真实渲染 PNG 预览。

## 4. 输出契约（result.json）

```json
{
  "case_id": "<原样保留>",
  "status": "success | partial | failed",
  "task": "figure-parsing",
  "figures": [
    {
      "figure_id": "Fig.2",
      "panels": ["a","b"],
      "axes": [
        {"axis": "x", "type": "linear|log10|dual", "unit": "s", "tick_pixel_refs": [[63,"0"],[412,"10"]],
         "axis_map": {"pixel_range": [63,412], "data_range": [0,10], "r_squared": 0.99999}}
      ],
      "series": [
        {"series_id": "s1", "legend_label": "WT", "color_or_marker": "black circles",
         "n_points": 12, "key_values": [{"name":"peak","x":4.8,"y":3.2,"unit_y":"mV","evidence":"Fig.2a peak at (347px, 88px)"}],
         "axis_ref": "y-left"}
      ],
      "statistical_markers": [{"marker":"**","compares":["WT","KO"],"evidence":"Fig.2b above bar 2-3"}],
      "scale_bar": {"pixel_length": 120, "stated_length": "10 µm", "unit_conv": "1px = 0.083 µm"},
      "excluded_nondata": ["legend box","gridlines"],
      "figure_caption_locator": "page 3, caption of Fig.2"
    }
  ],
  "findings": [
    {"claim": "WT 在 5–15 s 达到平台期", "level": "inference", "evidence": "Fig.2a curve s1 slope <0.01 after t=5", "confidence": "medium"}
  ],
  "uncertainties": [
    {"item": "y 轴刻度 500 mV 与正文 'voltage (V)' 表述不一致", "code": "unit_conflict", "resolution": "以刻度标注 mV 为准，依据：刻度文字直接可读"}
  ],
  "gaps": ["Fig.3 未提供像素，仅列题注，不做解析（按组织方修订为明确缺口）"],
  "not_reported": ["误差线具体数值：图中以误差棒表示，未标数值"],
  "sources": [{"type":"image","file":"fig2.png","locator":"whole image"},{"type":"text","locator":"page 3 caption"}],
  "change_log": [{"ts":"ISO时间","change":"初版落盘"}]
}
```

字段必须逐项落实题面 output_contract 的全部要求；若题面案例有额外字段，全部补齐，一个都不能少。

## 5. 数字门槛（达不到诚实标 partial）

- `axis_map.r_squared ≥ 0.999`（线性）或 log 残差 ≤0.5%：达标才允许输出硬数值。
- 曲线点提取：连续曲线 ≥8 个采样点/系列；散点 100% 记录可辨点数并与图注声明的 n 对照，不符进 uncertainties。
- 每条 finding 必须有 evidence；无 evidence 的 finding 数 = 0。
- 三级标注覆盖：findings 中 level∈{direct,inference} 的比例 ≥60%，其余必须为 undetermined 且不计入结论性表述。
- 门槛不达 → status=partial，写明缺口与可人工接管位置。

## 6. 异常处理表

| 异常 | 判定 | 处置 |
|---|---|---|
| 无坐标刻度 | 标定脚本无法取得 ≥2 刻度 | 只报告图注可读信息与元素清点，status=partial |
| 图被裁剪/轴断裂符号(∥) | 断轴两侧标定不一致 | 分段标定，各自带 map，标 uncertain |
| 图例缺失 | series 无法命名 | 用 series_id + 颜色/标记描述，标 legend_missing |
| 单位不明 | 图注/正文均无单位 | 数值保留 raw，unit=null，标 unreported，不猜 |
| 曲线重叠 | 像素追踪混色 | 按可分离段提取，注明 overlap，漏段列 gaps |
| 图像过曝/低分辨率 | 视觉判读不可靠 | 标 image_quality_low，只输出 low confidence 结果 |
| 材料缺失/空图 | inventory 无效文件 | status=failed + reason，不虚构 |

## 7. 自查清单

- [ ] case_id 原样保留；output_contract 字段 100% 覆盖。
- [ ] 所有数值经 calibrate.py 标定（r_squared 达标）且有 evidence。
- [ ] excluded_nondata 非空（证明排除过非数据元素）。
- [ ] 每条 finding 有 level 三级标注；undetermined 未被写成事实。
- [ ] result.json 可被 `python3 -m json.tool` 解析；CSV 与 JSON 数值一致。
- [ ] 未报告项、不确定项、材料冲突分别落位 not_reported/uncertainties/gaps。

## 8. 效率约束

- 预算 64 请求/900 秒：Step 0-1 ≤10 请求；标定与提取以脚本执行为主，模型只做判读与复核。
- 优先落盘最小 result.json；单图解析超过 120 秒仍未收敛 → 落 partial 并停止继续打磨。

## 9. 最小示例（示意输出，非正式案例结果）

输入：`work_axis_spec.json` = `{"axis":"x","unit":"min","ticks":[[10,"0"],[110,"5"],[210,"10"]],"type":"linear"}`
运行：`python3 scripts/calibrate.py --spec work_axis_spec.json`
示意输出：`{"axis":"x","type":"linear","unit":"min","slope":0.05,"intercept":-0.5,"r_squared":1.0,"map":"data = 0.05*(px-10)"}`
由此：像素 x=210 处读取曲线 y=2.4 → 输出 `{"x":10.0,"y":2.4,"evidence":"tick at px=210"}`。
