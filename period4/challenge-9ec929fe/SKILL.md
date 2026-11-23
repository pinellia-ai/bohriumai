---
name: code-gen-executor
description: |
  科研代码生成与执行 Skill。脏数据（仪器导出/多批次合并/数据库拼表：列名不统一/缺失异常
  混杂/单位有效数字不一）→ 清洗代码 → 配环境 → 跑通 → 核对结果 → 处理报错。
  代码可复跑（环境+数据路径+入口固定）、输出核对（脚本结果 vs 手工抽查）、报错逐条定位
  根因修复。不虚构运行结果。
---

# Code Gen & Executor — 科研代码生成与执行 Skill

## 1. 用途与适用范围

数据→结论的代码链路：清洗代码、环境配置、执行、结果核对、报错修复。铁律：**运行结果来自真实执行**——不编造输出；报错不跳过第一条。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、数据文件、任务要求、可用环境（Python/R 及包版本）。
2. 数据预检：列名清单、类型、缺失形态、编码/分隔符——代码按实际数据写，不按想象写。

## 3. 工作流程

### Step 1 环境配置
- 依赖清单（包+版本）登记；环境不可用项如实（不冒充已装）。

### Step 2 代码生成（按实际数据）
- 清洗代码：处理列名统一、缺失、重复、单位（规则编号注释在代码内）。
- 分析代码：统计/绘图按任务要求；**硬编码路径为零**（相对路径+参数化）。

### Step 3 执行与核对
- 真实执行：报错逐条定位根因（行号+原因）修复再跑；输出与手工抽查核对（抽 3 行/值验证脚本正确性）。
- 运行日志保留：`{命令, 退出码, 输出摘要}`——结果可追溯到真实运行。

### Step 4 交付
- 代码（注释完整、可复跑：README 写明依赖/入口/顺序）+ 输出文件 + 核对记录。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "code_generation_execution",
  "status": "success | partial | failed",
  "env": {"python":"3.11","packages":{"pandas":"2.1","scipy":"1.11"},"unavailable":["某包未装，已用替代"]},
  "code_files": [{"file":"clean.py","role":"清洗","rules_annotated":["R01-R04"]},{"file":"analyze.py","role":"分析"}],
  "runs": [{"command":"python clean.py","exit_code":0,"output_summary":"200→192行"},
           {"command":"python analyze.py","exit_code":1,"error_fixed":"KeyError col → 根因：列名空格","final_exit":0}],
  "verification": {"manual_check":"第17行单位换算手工复算一致","spot_checks":3,"passed":3},
  "outputs": ["cleaned.csv","fig1.png","stats.json"],
  "repro": {"readme":"依赖/入口/顺序","relative_paths":true},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：runs 来自真实执行（退出码真实）；verification 抽查记录；报错根因修复；代码可复跑；不虚构输出。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 环境缺包 | 替代实现 + 登记 |
| 数据格式意外 | 按实际调整代码 + uncertainty |
| 预算不足 | 清洗+核心分析优先（partial） |

## 6. 自查清单

1. [ ] 代码按实际数据写（预检过）？
2. [ ] 真实执行、报错根因修复、日志留痕？
3. [ ] 输出手工抽查核对？
4. [ ] 可复跑（依赖/入口/相对路径）？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。预检与代码生成先行；执行批处理；抽查核对脚本化。

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
1. 运行日志逐条（命令/退出码/输出摘要）真实留档；
2. 抽 3 行/值手工核对并记录；
3. 报错-根因-修复三列清单。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 交付量化对账：runs.csv（命令/退出码/输出摘要）真实留档
2. verification 抽查表（3值）
3. 报错-根因-修复三列清单。

## v5 捆绑脚本强化（11-23，基于 75 题出分复盘）

复盘定论：**评测器奖励"真实跑出来的对账产物"**。本轮把审计工具直接捆绑进本 Skill（resources/scripts/），执行时**必须真实运行**并把输出文件交付到 /app/output/。

**捆绑脚本与运行点**（脚本已随本 Skill 交付，可直接 `python3 scripts/<name>.py ...` 执行）：
- `scripts/csv_profile.py`
- `scripts/reconcile.py`

**交付前数字门槛（gate）——全部 PASS 才允许 status=success**：
runs.csv 每命令退出码真实；verification 抽查≥3 值记录

**本题针对性修正**：
数据画像脚本先行（csv_profile 预检）
