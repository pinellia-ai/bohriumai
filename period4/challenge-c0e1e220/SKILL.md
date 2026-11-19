---
name: stats-analysis-interpreter
description: |
  统计分析与结果解读 Skill。回答三问：差异有没有、有多大、多确定。前提检查（数据假设：
  正态/方差齐/独立）、检验选择与数据类型匹配、效应量与置信区间并报（不止 p 值）、
  解读与证据强度匹配（显著≠重要，相关≠因果）。原始值/代码/假设检查留痕可复跑。
---

# Stats Analysis & Interpretation — 统计分析与结果解读 Skill

## 1. 用途与适用范围

从脏表到"能写进报告"的统计结论：前提检查→检验→效应量→克制解读。每个结论三层：统计结果（是什么）、实际意义（多大）、确定性（多稳）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、数据（清洗后）、研究问题、比较要求。
2. 读取数据字典与字段语义；确认各组样本量、数据类型（连续/分类/配对）。

## 3. 工作流程

### Step 1 前提检查（假设先于检验）
- 正态性（检验+图）、方差齐性、独立性、配对结构——检查结果留档，**不满足时选替代检验并说明**。

### Step 2 检验执行
- 检验选择依据表：`{比较, 数据类型, 用的检验, 为什么}`；检验名+统计量+自由度+精确 p 报告。
- 多重比较：校正方法与校正后 p 同报。

### Step 3 效应量与区间
- 效应量（差值/比值/η² 等）+95%CI——**只有 p 不够**：显著但效应小要明说。
- 图：带误差线/区间可视化（含义注明 SD/SEM/CI）。

### Step 4 克制解读
- 三问作答：有没有（统计显著+方向）、有多大（效应量实际含义）、多确定（CI 宽度/样本限制）。
- 相关不写因果；亚组探索性发现标 exploratory；不把边界 p（p=0.05 附近）写成明确结论。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "statistical_analysis",
  "status": "success | partial | failed",
  "assumption_checks": [{"check":"normality (Shapiro-Wilk)","result":"p=0.32 通过","evidence_ref":"fig_qq.png"}],
  "tests": [{"comparison":"A vs B","test":"Welch t-test","stat":{"t":2.41,"df":31,"p":0.022},
             "effect":{"type":"mean diff","value":1.8,"ci":[0.3,3.3]},
             "selection_reason":"两组连续数据、方差不齐","multiple_correction":"Holm，校正后p=0.041"}],
  "figures": [{"file":"fig1.png","type":"箱线+散点","error_bar_meaning":"95%CI"}],
  "interpretation": [
    {"question":"A与B有无差异","answer":"有（校正后p=0.041）","magnitude":"差1.8单位（CI 0.3-3.3），实际意义为约15%改善",
     "certainty":"样本量n=16/组，CI较宽，结论中等确定","boundary":"相关设计，不推因果","written_for_report":"建议表述"}
  ],
  "code": "analysis.py（可复跑）",
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：assumption_checks 先于检验；效应量+CI 必报；解读三层齐；代码可复跑；边界声明（因果/探索性）不越界。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 数据不满足任何检验假设 | 非参替代 + 限制声明 |
| 结果无法解释（统计显著但无实际意义） | 如实说明两面 |
| 预算不足 | 核心比较优先（partial） |

## 6. 自查清单

1. [ ] 假设检查先于检验？
2. [ ] 效应量+CI 并报？校正做了？
3. [ ] 解读三层（有无/多大/多确定）齐？
4. [ ] 因果/探索性边界未越？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。分析脚本一次成型可复跑；假设检查与检验合并执行；解读基于脚本输出。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：数据/配置/日志/文献是事实依据；不编造数据、运行结果、软件状态。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/`（数据/图/代码文件 + result.json）。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：保留原始值、规则、结果、图表/代码和质量检查；每条结论带来源定位。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
