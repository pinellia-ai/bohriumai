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
