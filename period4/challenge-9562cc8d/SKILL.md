---
name: publication-figure-builder
description: |
  科研数据可视化 Skill。从数据表到可投稿图件的链条：数据口径确认（缺失/异常/重复处理
  先声明）→ 统计假设 → 图表类型与编码（位置/长度/颜色/形状/分面，不扭曲比例）→ 标注
  （轴/单位/图例/误差线含义/显著性/样本量）→ 按目标要求导出。图与源数据对应关系保留
  （可复现），代码交付。
---

# Publication Figure Builder — 科研数据可视化 Skill

## 1. 用途与适用范围

链条五环：口径确认 → 假设检查 → 类型与编码 → 标注齐全 → 合规导出。铁律：图不错误改变结论（截断轴/双轴混淆/色阶非线性都算）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、数据表、目标期刊/报告要求（尺寸/格式/配色）。
2. 数据口径声明：缺失/异常/重复如何处理（继承清洗结论或本步声明）——画图前定稿。

## 3. 工作流程

### Step 1 假设与类型选择
- 统计假设是否成立（比较类需检验类型匹配）。
- 图表类型按数据关系选：`{比较→柱/箱线, 关系→散点, 趋势→折线, 构成→堆叠（慎用饼图）, 分布→直方/小提琴}`，选择理由登记。

### Step 2 编码正确性
- 位置/长度编码不截断（截断轴必须显式标注）；色阶线性一致；颜色数=分类数；色觉安全（冗余编码：形状/纹理/标签）。
- 误差线含义注明（SD/SEM/CI 按数据）；样本量标注。

### Step 3 标注齐全
- 轴标签+单位+量级、图例、显著性标记（与检验对应）、面板编号（a,b,c）、图注覆盖读图所需全部信息。

### Step 4 导出与复现
- 按目标要求导出（分辨率/矢量/字体嵌入）；绘图代码交付（数据→图可一键重绘）；图-数据对应关系登记（哪列→哪个编码）。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "data_visualization",
  "status": "success | partial | failed",
  "data_scope": {"missing_policy":"NA不进图","outlier_policy":"保留并标注","source":"cleaned.csv"},
  "figure": {"file":"fig1.png/pdf","type":"grouped bar","type_reason":"组间比较",
             "encoding":{"x":"组别","y":"均值(mg/L)","color":"处理(2类)","error_bar":"95%CI"},
             "axes":{"y_start":0,"truncated":false},"colorblind_safe":true},
  "annotations": {"axis_units":"mg/L","legend":"完整","significance":"*p<0.05 (t检验)","n_labels":true,"caption":"图注草稿"},
  "data_link": [{"encoding":"y","column":"conc_mean"},{"encoding":"error_bar","column":"ci95"}],
  "export_check": {"dpi":300,"fonts_embedded":[],"size_compliant":true},
  "code": "plot.py",
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：data_scope 先声明；编码不扭曲（截断/双轴显式处理）；标注五要素齐；data_link 使图可复现；代码交付。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 数据口径未声明 | 先声明再画（不画口径不明的图） |
| 目标要求冲突（如黑白印刷） | 灰度/纹理适配 + 登记 |
| 预算不足 | 核心图先行（partial） |

## 6. 自查清单

1. [ ] 口径先声明？假设检查？
2. [ ] 编码无扭曲？色觉安全？
3. [ ] 标注五要素（轴/图例/误差/显著性/样本量）齐？
4. [ ] 图可由代码+数据复现？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。口径与类型先行；绘图代码一次成型；导出检查合并执行。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：数据/配置/日志/文献是事实依据；不编造数据、运行结果、软件状态。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/`（数据/图/代码文件 + result.json）。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：保留原始值、规则、结果、图表/代码和质量检查；每条结论带来源定位。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
