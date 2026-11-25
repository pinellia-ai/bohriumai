---
name: research-data-visualization
description: |
  科研数据可视化。图表选择规则库（数据类型×分析目的→图型，含不推荐理由）+ 同源双渲染（可编辑 SVG 与 300dpi PNG 由同一映射函数生成）+ 标注/图注自动生成（轴标目、单位、误差线含义、n、面板编号）+ 图注独立可读 + 发表级导出（色盲安全/灰度可辨、栏宽匹配、字体检查）。数据源 UCI 快照或 SQLite；每个视觉元素可回溯源数据。
---

# 科研数据可视化 Skill（research-data-visualization）

## 1. 用途与适用范围

- 用途：从原始数据表到可投稿图件的完整链条：口径确认→假设检查→图型选择→编码→标注→导出。
- 不做：统计方法创新、实验设计、图像美化。
- 判据：每个视觉元素与源数据一一对应；不经二次修补直接可用；过程可按记录重跑。

## 2. 输入识别（Step 0，必做）

1. 读 /input/case.json（case_id 原样、output_contract 抄 order.json）；最小 result.json 先落盘。
2. 数据源：CSV（快照+sha256）或 SQLite（db_probe.py 发现 schema+行数）。**先读数据字典/表头确认字段语义与单位。**
3. 数据体检（复用清洗链）：缺失/异常/重复的处理口径必须在画图前定，并记进 plot_spec 的 data_policy 字段——口径未记录的图不交付。

## 3. 工作流程

### Step 1 图型选择（规则库，带理由）

`chart_rules.json`（scripts 内置）核心规则：
- 分类比较（组数≤5）→ 柱状图（y 从 0 起）；组数>5 → 点图+误差线（避免柱林）。
- 趋势/时间序列 → 折线图（时间在 x，等间隔检查）；**禁止把时间序列画成并列柱**。
- 两连续变量关系 → 散点图；>100 点 → 二维密度/六边形。
- 构成占比 → 堆叠条形图；**禁止饼图（角度编码难辨，>3 类禁用）**。
- 分布 → 箱线/小提琴（n≥20 箱线才可信，小样本直接点图）。
- 每次选择输出：chosen/rejected（含不推荐理由）/reason。

### Step 2 绘图（同源双渲染）

```bash
python3 $SKILL_DIR/scripts/chart_builder.py /app/work/chart_spec.json --outdir /app/output
```

- chart_spec：type/data_csv/x_label（含单位）/y_label（含单位）/err_label(SD|SEM|95%CI 必填若有误差线)/title(面板编号)/zero_baseline=true(bar 禁止截断)/log_y(对数轴显式声明)。
- 同源保证：SVG 与 PNG 用同一映射函数 X()/Y() 生成；SVG 图元带 data-value/data-row 可回溯 CSV 行。
- 色板默认 Okabe-Ito（色盲安全+灰度可辨，亮度差>0.3）。

### Step 3 标注与图注（十项检查）

```bash
python3 $SKILL_DIR/scripts/annotate_check.py /app/output/<fig>.svg /app/work/chart_spec.json
```
断言：①x/y 标目存在且 y 含单位 ②误差线含义已声明 ③图注 note 含数据源与 n ④面板编号存在 ⑤bar 基线未截断 ⑥刻度范围覆盖数据±误差 ⑦系列名与源表一致 ⑧对数轴显式 ⑨无空图例 ⑩SVG 文字可编辑。

图注模板（annotate_check 生成 note.txt）：
> Fig X. <一句话主结论，与统计结果一致>. <图型与编码说明>. 误差线=<含义>, n=<组n>. 数据：<文件>（sha256 前8位）. <统计方法与 p 值，若有>.

### Step 4 发表级导出

export_check.py（SVG 可编辑/文字未转曲/图元带 data-source/图例数/PNG≥300dpi/PDF）。尺寸：单栏 3.5in/双栏 7.2in，字号缩放后≥6pt；导出参数写进 result.json。

### Step 5 result.json

```json
{
  "case_id": "<原样>", "status": "...",
  "figures": [{"svg": "...", "png": "...", "pdf": "...", "type": "bar", "panel": "a",
                "data_policy": {"missing": "keep_missing", "n_shown": 0}, "note": "/app/output/fig_note.txt"}],
  "chart_choice": {"chosen": "bar", "rejected": [{"type": "pie", "reason": "角度编码难辨"}], "reason": "..."},
  "annotations_check": {"pass": true, "items": 10},
  "export_check": {"pass": true},
  "data_snapshot": {"sha256": "...", "rows": 0},
  "uncertainty": [], "change_log": []
}
```

## 4. 输出契约

题面三大交付：分析结果（图表文件）/质量与复现证据（快照+spec+规则+脚本）/异常说明。图表必须连同绘图代码与图注交付（题面要求"而不是给一段建议"）。

## 5. 数字门槛

- annotate_check 10 项全 PASS；export_check 全 PASS；data-value 抽验与源数据一致（verify_map）。
- 图型选择带 rejected 理由；灰度打印可辨（色板亮度差断言）。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 缺失列/类型混杂 | 数值化失败行标 missing 不画点，uncertainty 记行号 |
| 类别过多（>12） | 按均值排序取前 N+"other"，或分面；不硬塞一张图 |
| 量纲差异大 | 分面或双轴（双轴必须两个 y 标目都含单位） |
| 全缺失列 | 不画该系列，anomalies 记录 |
| 标签过长 | 缩写+图注全名 |
| 字体缺失/乱码 | FIG_CJK_FONT 重试；失败 partial |
| SQLite 结果集为空 | failed |

## 7. 自查清单

- [ ] 数据口径已记录（data_policy）
- [ ] 图型选择含理由与 rejected
- [ ] annotate_check 10 项过；图注独立可读
- [ ] 色盲安全/灰度可辨；bar 未截断基线
- [ ] export_check 过；SVG data-value 可回溯

## 8. 效率约束

先最小 result；一次成型；≤50 文件。

## 9. 最小示例

3 组柱图（含单位/SD 误差线/n）→ annotate_check+export_check 全过，data-value 抽验 3/3（见 README 自测记录）。


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

- workorder 类型: `visualization_task`；spec 文件命名: `chart_spec.json`。
- 越界内容一律移交相邻课题：统计方法选择、实验方案设计、论文写作、版式美化。
- 科学判断由评测 Judge 做：本 skill 只保证"可编辑源文件+导出合规+来源可核验"三件套的工程质量。
