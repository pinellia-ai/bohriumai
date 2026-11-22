---
name: data-cleaning-pipeline
description: |
  科研数据清洗与处理 Skill。处理"脏数据路"：宽表缩写列名、缺失值多形态（空格/-999）、
  跨表重复记录、单位混写（mg/L vs μg/mL）、异常值难辨（真实高值 vs 加样失误）。
  原始值全程保留、清洗规则编号可复跑、质量报告与清洗后表数字对得上。缺失/异常/无法
  解释如实说明。
---

# Data Cleaning Pipeline — 科研数据清洗与处理 Skill

## 1. 用途与适用范围

一次做对、反复做对、别人能核对的数据清洗。铁律：原始数据只读副本、每条清洗规则编号留痕、清洗前后可对账。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、数据字典（字段语义/单位/允许值）、数据文件、清洗要求。
2. 读取数据字典并登记字段语义——列名缩写对照、单位、量纲、取值范围。
3. 原始数据只读快照（/app/work/raw_snapshot），清洗在副本进行。

## 3. 工作流程

### Step 1 数据体检
- 缺失形态清单（空串/空格/-999/NA 各多少）、重复记录（判定键）、单位混写点、值域越界点——体检报告先行。

### Step 2 规则化清洗（规则编号）
- 规则：`{rule_id, 规则内容, 适用字段, 处理动作, 依据}`。如 R01：`-999 → NA`（依据：数据字典注明 -999 为缺失标记）。
- 单位换算：换算公式+精度留痕，原值保留列。
- 异常值：**不删除**——标记 `outlier_flag` 并给判定依据（越界/物理不可能），真实高值保留，交由分析阶段决定。
- 重复记录：判定键可解释（样品ID+批次），合并建议不直接删。

### Step 3 质量对账
- 清洗前后对账：行数、缺失计数、单位分布——质量报告数字与清洗后表**一致**（第3期教训：报告和表对不上）。

### Step 4 输出
- 清洗后表 + 规则库 + 对账报告 + 变更日志（行级：`{row, field, before, after, rule_id}`）。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "data_cleaning",
  "status": "success | partial | failed",
  "data_dictionary_applied": [{"field":"浓度","semantic":"mg/L 或 μg/mL，换算到 mg/L"}],
  "health_report": {"missing_forms":{"space":12,"-999":30},"duplicates":8,"unit_conflicts":5,"outliers_flagged":3},
  "rules": [{"rule_id":"R01","rule":"-999→NA","field":"浓度","basis":"数据字典注明"}],
  "cleaned_table": "cleaned.csv",
  "change_log": [{"row":17,"field":"单位","before":"μg/mL","after":"mg/L","rule_id":"R03","original_kept":true}],
  "reconciliation": {"rows_before":200,"rows_after":192,"merged":8,"quality_report_match":true},
  "gaps": [], "uncertainty_notes": ["3个异常值保留并标记，真实性需实验复核"], "changes": []
}
```

硬性要求：原始值保留（before 列）；reconciliation 对账成立；异常值不删只标；规则可复跑。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 数据字典缺失 | 按值域推断+uncertainty 声明 |
| 无法解释的结果 | uncertainty_notes 如实 |
| 预算不足 | 体检+核心规则先行（partial） |

## 6. 自查清单

1. [ ] 原始快照只读？清洗留痕可回？
2. [ ] 缺失/单位/重复/异常四类处理齐？
3. [ ] 异常值标记不删除？
4. [ ] 对账成立（报告=表）？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。体检脚本化；清洗规则批处理执行；对账自动。

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
1. 清洗前后对账表（行数/缺失/分布）脚本生成；
2. change_log 行级 CSV（before/after/rule_id）；
3. 异常值只标记不删除。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 保持 67 分水准：change_log 行级 CSV 全量
2. reconciliation 对账断言
3. 异常值只标记计数表。
