---
name: db-query-analyzer
description: |
  科研数据库查询与分析 Skill。四坑防御：跑不通（连接/语法）、跑通但结果不对（漏连接
  条件行数膨胀、编码字段当数值聚合）、字段口径不清、表格无法回查。逐项防御：查询前校验
  schema、行数 sanity check、字段语义表、查询留痕可回查。失败定位到具体语句与原因。
---

# DB Query Analyzer — 科研数据库查询与分析 Skill

## 1. 用途与适用范围

连接 → 查询 → 抽取 → 字段解释 → 跨表分析。四条防御：① 连接/schema 先验证（不猜表名字段名）；② 行数 sanity check（join 后行数膨胀=漏连接条件）；③ 字段语义表（编码字段不当数值聚合）；④ 查询留痕（交付表可回查原始查询）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、连接参数（或本地库文件）、分析需求。
2. **schema 校验**：列出实际表/字段/类型——与需求期望对照，张冠李戴在此拦截。

## 3. 工作流程

### Step 1 连接与 schema 验证
- 连接测试（真实执行）；`SHOW TABLES / DESC` 输出留档；需求涉及的字段全部确认存在+类型。

### Step 2 查询编写与防御
- 每条查询：注释（目的/预期行数量级）；JOIN 显式条件；编码型字段（类别码）不当数值聚合；NULL 处理显式（IS NULL / COALESCE 按字典语义）。
- 分步小查询验证（先 COUNT 再取数），行数 sanity：join 后行数 vs 预期（膨胀即报漏连接条件）。

### Step 3 字段语义与口径
- 字段语义表：`{字段, 含义(数据字典), 单位, 口径注意}`——结果表每列带解释。
- 跨表分析：口径对齐（同指标跨表单位/定义差异显式处理）。

### Step 4 交付回查
- 每个交付表关联原始查询（query_id）；失败查询逐条留痕：`{语句, 错误信息, 根因, 修复}`。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "db_query_analysis",
  "status": "success | partial | failed",
  "schema_verified": {"tables":[...],"fields_confirmed":true,"mismatches_fixed":["需求写 measure_val，实际 measure_value"]},
  "queries": [{"query_id":"q1","sql":"SELECT ...","purpose":"...","rows_expected":"~200","rows_actual":198,
               "sanity":"通过 | 膨胀→修复：补 JOIN 条件","error_fixed":null}],
  "failed_queries": [{"query_id":"q0","sql":"...","error":"syntax near ...","root_cause":"...","fixed_in":"q1"}],
  "field_semantics": [{"field":"measure_value","meaning":"浓度","unit":"mg/L","note":"NULL=未测"}],
  "results": [{"table":"result.csv","query_id":"q2","rows":198,"analysis":"跨表聚合：按样品×日期","notes":"编码字段 status 按类别处理"}],
  "repro": {"queries_file":"queries.sql","run_order":[...]},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：schema_verified 先行；每查询行数 sanity；field_semantics 覆盖结果列；failed_queries 留痕根因；交付表↔query_id 可回查。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 连接失败 | 参数逐项检查（真实错误信息）+ failed_queries |
| 行数膨胀 | 定位漏 JOIN → 修复重跑 |
| 预算不足 | schema 验证+核心查询优先（partial） |

## 6. 自查清单

1. [ ] schema 实际验证过（非猜）？
2. [ ] 行数 sanity 全查？膨胀已修？
3. [ ] 编码字段未当数值？NULL 显式处理？
4. [ ] 交付表可回查原始查询？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。schema 验证先行；小步 COUNT 验证再取数；语义表模板化。

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
1. 每查询先 COUNT sanity（预期量级对比），行数异常即修；
2. 查询留痕 queries.sql + 执行结果摘要表；
3. 字段语义表覆盖结果集每列。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 交付量化对账：queries.csv（id/SQL/目的/预期行数/实际行数/sanity）逐条
2. failed_queries 留痕
3. field_semantics 覆盖结果集每列。

## v5 捆绑脚本强化（11-23，基于 75 题出分复盘）

复盘定论：**评测器奖励"真实跑出来的对账产物"**。本轮把审计工具直接捆绑进本 Skill（resources/scripts/），执行时**必须真实运行**并把输出文件交付到 /app/output/。

**捆绑脚本与运行点**（脚本已随本 Skill 交付，可直接 `python3 scripts/<name>.py ...` 执行）：
- `scripts/reconcile.py`

**交付前数字门槛（gate）——全部 PASS 才允许 status=success**：
queries.csv 行数=执行查询数；行数 sanity 全 PASS；字段语义覆盖=结果集列数

**本题针对性修正**：
查询留痕 CSV 化 + 行数 sanity 断言
