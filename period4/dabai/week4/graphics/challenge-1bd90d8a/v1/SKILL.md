---
name: source-value-chart
description: |
  科研数据图表生成与编辑（workorder: source_value_chart）。从源数据表出发生成柱/线/散点图：每个图元带 data-value 与 data-row 双向映射回 CSV 行列，样式按目标规范配置，标注校验（轴/单位/图例/误差线含义/样本量）后交付可编辑 SVG + 300dpi PNG/PDF；数据更新后可一键重绘。
---

# 源数据图表 Skill（source-value-chart）

## 1. 用途与适用范围

- 用途：数据表→图元映射、样式规范、标注校验、源数据关联、可编辑导出。
- 核心判据（题面）：每根柱子的数字能说出来自源数据哪列哪行；图例与系列逐项一致；交付可编辑源文件；导出合规。
- 不做：统计方法选择与显著性计算、实验路线设计。

## 2. 输入识别（Step 0，必做）

1. 读 /input/case.json：case_id 原样保留、output_contract 全字段抄进 /app/work/order.json、材料清单。
2. 先写最小 result.json（status=running）到 /app/output——任何中断都有可评分产物。
3. 盘点数据表：读表头+前 20 行确认字段语义；找到与图相关的列（分组列/数值列/误差列）。材料缺失→status=failed。
4. 从 task.md 提取图型要求、目标规范（字号/线宽/尺寸/分辨率）、导出格式；未指明按默认 SVG+PNG(300dpi)+PDF、单栏 7.5in。

## 3. 工作流程

### Step 1 源数据快照与字段映射

```bash
python3 $SKILL_DIR/scripts/snapshot.py /path/to/data.csv /app/work
```

产出：data.raw.csv 原样副本 + snapshot.json（行数、各列 sha256、缺失/空值计数）。**绘图只读快照，不改原始文件。**
写 /app/work/fieldmap.tsv：`figure_element, column, rows, unit, source`（每行注明"柱 1 ← 列 value 行 2-4，单位来自表头"）。单位不在表头时先查数据字典/材料正文；找不到 → y 轴标 "（单位未标注，源表未提供）" 并记 uncertainty，**不猜单位**。

验收：fieldmap 每行有 column 与 rows；快照行数>0。

### Step 2 数据→图元映射计算

在 spec JSON 里显式给出（chart_spec.json）：

- type: bar/line/scatter；data_csv 指向快照副本
- x_label/y_label（**y 轴必须含单位**）、err_label（SD/SEM/95%CI，误差列存在时必填）
- zero_baseline=true（bar 禁止截断基线；折线图允许非零基线但必须注明）
- title（面板编号如 Fig1b）

执行 `chart_builder.py chart_spec.json --outdir /app/output`：柱高/点位置=值线性映射（映射函数 Y(v) 写在脚本内，SVG 图元带 data-value 与 data-row），图例项数=系列数。

### Step 3 标注校验（六类检查点逐项过）

跑 `export_check.py --svg ... --png ... --pdf ...`，另按 checklist 人工/脚本核对：

| 检查点 | 断言 |
|---|---|
| 科学实体 | 图中分组/系列名与源表逐字符一致（防拼错基因/蛋白/物种名） |
| 数据编码 | 任取 2 个图元，data-value==源表对应行值（脚本 verify_map.py 自动抽验≥2点） |
| 图例标注 | 图例项数=系列数；误差线含义已写进图注 |
| 坐标轴 | x/y 标目齐全，y 含单位；刻度范围覆盖数据±误差 |
| 中文/字体 | 无方框乱码；font_used 记录 |
| 导出格式 | PNG≥300dpi；SVG 文字未转曲；PDF 可打开 |

### Step 4 verify_map.py 数值抽验（防"画得像但不对"）

```bash
python3 $SKILL_DIR/scripts/verify_map.py /app/output/xxx.svg /app/work/data.raw.csv
```

解析 SVG 内 data-value/data-row，与 CSV 对应行列比对，≥2 点不一致即 FAIL（exit 1），必须修图重跑。

### Step 5 result.json

```json
{
  "case_id": "<原样>",
  "status": "complete|partial|failed",
  "figure": {"svg": "...", "png": "...", "pdf": "...", "type": "bar", "n_points": 0},
  "fieldmap": "/app/work/fieldmap.tsv",
  "data_snapshot": {"rows": 0, "sha256": "...", "missing_cells": 0},
  "annotations_check": {"axis_units": true, "err_label": "SD", "legend_consistent": true, "verify_map": "pass 3/3"},
  "export_check": {"pass": true},
  "uncertainty": [],
  "change_log": []
}
```

## 4. 输出契约

- 逐字段对照 output_contract；三大交付=可编辑源文件（SVG 分层可编辑）/导出件（PNG/PDF+检查结果）/来源与修改记录（fieldmap+snapshot+verify_map 结果）。

## 5. 数字门槛

- verify_map 抽验点 100% 一致；export_check 全 PASS；图例-系列 0 错配；y 轴单位必须有（或如实标缺失）。
- 数据更新重绘：改 CSV 后重跑 Step 2-4 即同步，无需手工改图——这是"可编辑+可复现"的证据，写进 result.json change_log。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 缺列/列名不匹配 | 按 fieldmap 报错终止，不静默换列 |
| 空值 | 不当 0 参与；如实剔除并在 uncertainty 记行号 |
| 量级异常（离群>10×中位数） | 保留但标 uncertainty，不擅自删 |
| 标签过长溢出 | 缩字号至最小 8pt，仍溢出改写短标签+图注全名 |
| 字体缺失/乱码 | FIG_CJK_FONT 重渲染；失败→partial |
| 导出失败 | 只交 SVG，exports 标 null |

## 7. 自查清单

- [ ] case_id/contract 全覆盖；快照 sha256 已记
- [ ] fieldmap 每行可回溯；verify_map 全过
- [ ] 轴标目+单位+误差线含义+图例齐；bar 基线未截断
- [ ] export_check 全 PASS；SVG 文字可编辑
- [ ] result.json status 如实

## 8. 效率约束

最小 result 先落盘；一次成型不迭代风格；校验失败最多修 2 轮；文件≤50。

## 9. 最小示例

3 行 CSV→bar 图：chart_builder 产出 Fig1b_demo.svg/png/pdf，export_check pass:true，verify_map 3/3 一致（详见 README 自测记录）。


## 附录 A 全流程命令序列（评测时按序执行）

```bash
# Step 0 识别（手动：读 /input/case.json 抄 output_contract 到 order.json）
mkdir -p /app/work /app/output
# Step 1-N 主链路（$SKILL_DIR 为本 skill 安装目录）
ls $SKILL_DIR/scripts/        # 确认脚本齐备
# 各 Step 的具体命令见 §3；校验脚本 FAIL 时按 §6 异常表处置后重跑（≤2 轮）
python3 $SKILL_DIR/scripts/export_check.py --help   # 查看参数
```

## 附录 B 常见失败 ↔ 处置对照

| 失败现象 | 根因 | 处置 |
|---|---|---|
| 校验脚本 exit 1 有 FAIL 项 | 见其输出 detail 字段 | 按 detail 修 spec/数据后重跑 |
| PNG 打开是白图/方框 | 无 CJK 字体 | FIG_CJK_FONT=/path/to/font.ttf 后重跑渲染 |
| result.json 字段缺失 | 跳过 Step 6 模板 | 按 §3 末模板逐字段补齐 |
| 预算接近上限 | 前面步骤耗时过多 | 立即交 partial（status 如实），已产文件照常评分 |
| 材料与预期类型不符 | 题面材料变化 | 按 Step 0 盘点结果走 §6 对应行 |

## 附录 C 与本赛道的边界对照（不做的事，避免越界扣分）

- workorder 类型: `source_value_chart`；spec 文件命名: `chart_spec.json`。
- 越界内容一律移交相邻课题：统计方法选择、实验方案设计、论文写作、版式美化。
- 科学判断由评测 Judge 做：本 skill 只保证"可编辑源文件+导出合规+来源可核验"三件套的工程质量。
