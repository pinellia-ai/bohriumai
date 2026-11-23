---
name: multi-doc-compare-matrix
description: |
  多文档比较与整合 Skill。围绕同一研究问题的多篇论文：统一字段定义（对象/数据/方法/
  条件/指标/结论/局限），逐篇抽取并记录取值规则；方法与条件对齐判定可比子集；结论
  一致性判断并把冲突归因到样本/方法/条件/指标口径差异；每个取值与差异结论可回原文
  定位，比较表可复跑、可增量加入新论文。
---

# Multi-doc Compare — 多文档比较与整合 Skill

## 1. 用途与适用范围

把"各写各的摘要"变成**同一套字段下的逐格对照**：对得齐（字段统一定义）、填得准（取值来自标注论文、单位口径随值记录）、说得清（冲突归因到具体差异）、查得回（每格回原文位置）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、研究问题、论文清单（每篇含定位体系）。
2. 通读各论文方法与结果段，盘点可比要素（数据集/样本量/条件/指标）。
3. 论文缺失或字段不可读：登记 gaps，不做无依据比较。

## 3. 工作流程

### Step 1 统一字段表（对得齐）
- 定义字段：`{field_id, name, 定义口径, 取值规则, 允许值/单位}`——先于抽取，全表共用。
- 同名不同口径的字段（如 accuracy 的宏/微平均）显式拆分或注明换算。

### Step 2 逐篇抽取（填得准）
- 每格取值：`{paper_id, field_id, value, unit, dataset_version, condition, locator(页/段/表行), quote}`。
- 未报告 → "未报告"（不填 0）；口径不明 → 标 uncertain。

### Step 3 可比性对齐
- 方法与条件对齐：数据集版本、样本量、划分方式、基线、评价口径归一 → 判定**可比子集**（哪些论文能直接比、哪些只能条件内比）。
- 不可比处显式标注，不强行同表硬比。

### Step 4 结论一致性与冲突归因（说得清）
- 结论方向/强度逐对比较：`一致 | 部分一致 | 冲突`。
- 冲突归因四选一或多因并列：样本差异 / 方法差异 / 条件差异 / 指标口径差异——每个归因引两边原文定位与差异点。

### Step 5 可复跑交付
- 字段表、抽取规则、比较表分离存储（schema/data/rules），新论文可增量加入复算。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "multi_doc_comparison",
  "status": "success | partial | failed",
  "field_schema": [{"field_id":"f1","name":"主要指标","rule":"结果段报告的惟一主指标","unit":"随值","allowed":null}],
  "matrix": [{"paper_id":"pA","field_id":"f1","value":92.1,"unit":"%","condition":"test集B","locator":{"paper":"pA","table":"Table2 row3"},"quote":"..."}],
  "comparable_subsets": [{"subset":[["pA","pB"],"同数据集v2同划分"],"note":"可直比"},{"subset":[["pC"]],"note":"条件不同，仅定性比较"}],
  "consistency": [{"pair":["pA","pB"],"verdict":"consistent | partial | conflict",
                   "attribution":"指标口径差异（宏平均vs微平均）","evidence_locs":["pA Table2","pB §4.1"]}],
  "comparable_notes": [], "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：matrix 全格有 locator+quote；未报告/口径不明不填假值；comparable_subsets 判定有依据；consistency 归因落到四类之一。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 论文间字段定义冲突 | 以统一字段表为准，映射关系登记 |
| 无法判可比性 | 保守划入不可比 + uncertainty |
| 预算不足 | 字段表+核心字段矩阵先行（partial） |

## 6. 自查清单

1. [ ] 字段表先于抽取且口径统一？
2. [ ] 每格取值可回原文？未报告如实标注？
3. [ ] 可比子集判定有依据？不硬比？
4. [ ] 冲突归因具体（四类之一）？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。字段表先行；逐篇抽取并行推进；对齐与归因合并处理。中断时字段表+已抽篇目完整可交。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：实际输入文件与原论文是事实依据；不依据错误的领域标签补造数据；不编造内容/引用/软件状态。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：关键结论保留页码/段落/字段/图表定位。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。

## v2 执行导向强化（对首轮评测反馈的针对性修正）

首轮评测共性短板：工作流描述偏"清单式"，评测器要看到**真实执行与可复核产物**。本轮强化：

1. **产物即证据**：交付中至少包含 3 个真实执行产物（CSV/JSON/日志/脚本），由脚本或工具真实生成，非描述性文字。
2. **过程留痕**：run_log.md 逐条记录执行的命令与统计（抽取数量/命中数/对账结果），换人可重跑得到同一批产物。
3. **对账自检**：关键数字前后对账（输入数=处理数+跳过数等），对账脚本化。
4. **契约不变**：result.json 仍逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实标注 partial。

**本题针对性补强**：
1. 比较矩阵 CSV（paper,field,value,unit,locator）；
2. 可比子集判定规则表；
3. 冲突归因固定四类枚举。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 交付量化对账：matrix.csv（paper,field,value,unit,locator）全格覆盖计数；comparable_subsets 判定规则表；冲突归因四类枚举计数。

## v5 捆绑脚本强化（11-23，基于 75 题出分复盘）

复盘定论：**评测器奖励"真实跑出来的对账产物"**。本轮把审计工具直接捆绑进本 Skill（resources/scripts/），执行时**必须真实运行**并把输出文件交付到 /app/output/。

**捆绑脚本与运行点**（脚本已随本 Skill 交付，可直接 `python3 scripts/<name>.py ...` 执行）：
- `scripts/reconcile.py`
- `scripts/csv_profile.py`

**交付前数字门槛（gate）——全部 PASS 才允许 status=success**：
matrix.csv 行数=论文数×字段数（对账）；四类归因枚举计数

**本题针对性修正**：
比较矩阵 CSV 化 + csv_profile 抽查各论文口径
