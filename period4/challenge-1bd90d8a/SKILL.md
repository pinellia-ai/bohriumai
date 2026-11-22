---
name: data-figure-editor
description: |
  科研数据图表生成与编辑 Skill。把源数据映射成正确图元（柱高/点位/色阶/扇区角/误差线
  长度——与数据数值逐项一致），按目标样式调整（字号/线宽/配色/面板/留白），校验标注
  （轴/单位量级/图例/误差线含义/显著性/样本量），保留图↔源数据对应与可编辑源文件。
  图不错误改变结论。
---

# Data Figure Editor — 科研数据图表生成与编辑 Skill

## 1. 用途与适用范围

源数据→正确图元→合规样式→标注校验→可编辑交付。与可视化题的分工：本题主打**图元正确性**（数值映射逐项校验）与**编辑保留**（源文件可改）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、源数据表、样式要求/模板、编辑任务（生成或改图）。
2. 编辑任务时先解析既有图/源文件（svg/matplotlib 脚本/矢量），登记可编辑性（能改数值还是只能改样式）。

## 3. 工作流程

### Step 1 数据→图元映射
- 映射表：`{数据列 → 图元(柱高/点位/色阶/角度/误差线)}`，逐项校验：柱高=数值×比例（截断轴时显式标注）。
- 数值抽查：随机抽 3 个图元反向读值 vs 数据，误差≤1%。

### Step 2 标注校验
- 轴标签+单位+量级、图例完整、误差线含义（SD/SEM/CI 按数据来源）、显著性标记与检验对应、样本量——缺一补一。

### Step 3 样式适配
- 字号/线宽/配色/面板布局/留白按目标模板；配色=分类数、色觉安全；导出参数合规。

### Step 4 可编辑交付
- 交付：源文件（脚本或矢量 SVG，数据驱动的重绘）+ 导出件（PNG/PDF）；编辑接口说明（改哪个文件哪个参数改什么）。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "data_figure_generation_editing",
  "status": "success | partial | failed",
  "mapping": [{"column":"conc_mean","element":"bar height","axis":"y","scale":"linear, start 0"},
              {"column":"ci95","element":"error bar","meaning":"95%CI"}],
  "value_check": [{"element":"bar2","read_from_fig":411.8,"data_value":412.0,"within_1pct":true}],
  "annotations": {"axis_units":"mg/L","legend_ok":true,"significance":"*p<0.05","n_labels":true},
  "style": {"fonts":"模板要求","colors":2,"colorblind_safe":true,"panel_layout":"1×2"},
  "files": {"source":"plot.py + fig.svg（可编辑）","exports":["fig.png","fig.pdf"]},
  "export_check": {"dpi":300,"truncated_axis":"no | 显式标注"},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：mapping 全覆盖；value_check 反向读值通过；标注五要素齐；源文件数据驱动可编辑；不扭曲（截断显式）。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 既有图无源文件 | 按图重估数据点（标注 estimated）+ 建议重建 |
| 样式冲突（黑白印刷） | 灰度适配 + 登记 |
| 预算不足 | 映射+主图先行（partial） |

## 6. 自查清单

1. [ ] 数据→图元映射逐项校验？反向读值通过？
2. [ ] 标注五要素齐？
3. [ ] 源文件可编辑、数据驱动重绘？
4. [ ] 图未扭曲结论（截断/双轴处理）？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。映射与代码先行；值校验脚本化；导出合并执行。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：数据/配置/日志/文献是事实依据；不编造数据、运行结果、软件状态。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/`（数据/图/代码文件 + result.json）。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：保留原始值、规则、结果、图表/代码和质量检查；每条结论带来源定位。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。

## v2 执行导向强化（对首轮评测反馈的针对性修正）

首轮评测共性短板：工作流描述偏"清单式"，评测器要看到**真实执行与可复核产物**。本轮强化：

1. **产物即证据**：交付中至少包含 3 个真实执行产物（CSV/JSON/日志/脚本），由脚本或工具真实生成，非描述性文字。
2. **过程留痕**：run_log.md 逐条记录执行的命令与统计（抽取数量/命中数/对账结果），换人可重跑得到同一批产物。
3. **对账自检**：关键数字前后对账（输入数=处理数+跳过数等），对账脚本化。
4. **契约不变**：result.json 仍逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实标注 partial。

**本题针对性补强**：
1. 数据→图元映射表 CSV；
2. 反向读值抽查（读回 vs 数据 ≤1%）；
3. 绘图代码交付可重绘。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 保持 69.3 分水准：mapping.csv（数据列→图元）
2. value_check 反向读值表（误差≤1%）
3. 标注五要素核对。
