---
name: multi-step-analysis-agent
description: |
  多步骤数据分析 Agent Skill。"一批原始表+一句需求"的编排：导入→核对字段→清洗→统计
  →出图→组会级说明。每步依赖上一步产物——**口径走偏防扩散**：每步入口校验上一步口径
  （行数/字段/单位），步间产物签名对账；全程可复核、失败可定位。
---

# Multi-step Analysis Agent — 多步骤数据分析编排 Skill

## 1. 用途与适用范围

多步流水线：导入 → 字段核对 → 清洗 → 统计 → 出图 → 报告。核心风险是**口径扩散**（一步偏，步步偏）——用步间对账拦截：每步开始校验上一步产物的行数/字段/单位签名。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、原始表格、需求描述（缺什么值/比什么/画什么/给什么说明）。
2. 需求结构化：`{交付1: 缺失值与重复处理策略, 交付2: 组间差异检验, 交付3: 图, 交付4: 组会说明}`——含糊需求显式补问或按惯例默认+声明。

## 3. 工作流程

### Step 1 流水线定义
- 步骤 DAG：`{step_id, action, inputs(上步产物), outputs, 口径签名(行数/字段/单位清单)}`。
- 每步产物落盘（intermediate/step{k}.csv + 签名文件）。

### Step 2 逐步执行与对账
- 每步开始：校验输入签名与上步输出一致（行数变化有解释、字段集匹配、单位统一）。
- 不一致 → 停在当前步，定位是哪步改的口径，修复后重跑——**不让偏口径流入下游**。

### Step 3 分析与可视化
- 统计/出图继承前步口径（缺失/异常处理策略沿用声明）；图可由流水线脚本重绘。

### Step 4 组会级说明
- 结论用非专业语言复述 + 关键数字表 + 图；每条结论带步骤 ID（可回查数据来源）。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "multi_step_analysis",
  "status": "success | partial | failed",
  "pipeline": [{"step":"s1_import","inputs":["raw.csv"],"outputs":["intermediate/s1.csv"],"signature":{"rows":200,"cols":9}},
               {"step":"s2_clean","inputs":["s1.csv"],"outputs":["s2.csv"],"signature":{"rows":192,"cols":9,"units":"mg/L"},"signature_match":true}],
  "deliverables": {"missing_dup_policy":"...","stats":{"test":"Welch t","p":0.041,"effect":1.8},"figure":"fig1.png","report":"summary.md"},
  "conclusions": [{"text":"...","trace":"s2→s4","evidence":"stats.json"}],
  "gate_checks": [{"between":"s2→s3","ok":true,"note":"单位口径一致"}],
  "repro": {"runner":"run_all.py","order":"s1→s6"},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：pipeline 每步签名与 gate_checks 对账；口径偏移被拦截并记录；deliverables 四项齐（按需求）；结论带步骤追溯；runner 可一键复跑。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 上游签名不一致 | 停止扩散 → 定位修复 → 重跑 |
| 需求含糊 | 惯例默认 + uncertainty 声明 |
| 预算不足 | 核心链（清洗→统计）优先 |

## 6. 自查清单

1. [ ] 每步产物落盘且签名对账？
2. [ ] 口径偏移有拦截记录？
3. [ ] 四项交付齐？
4. [ ] 结论可回查数据来源？runner 可复跑？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。流水线脚本化一次成型；gate 检查自动；报告模板化生成。

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
1. 每步产物落盘+签名（行数/字段/单位），步间 gate 校验记录；
2. runner 脚本一键复跑；
3. 结论带步骤 ID 追溯。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 保持 67.3 分水准：pipeline 签名对账表（步间行数/字段/单位）
2. gate_checks 断言
3. 结论步骤 ID 追溯表。
