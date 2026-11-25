---
name: literature-reading-benchmark-kit
description: |
  文献阅读 Benchmark 与评测工具：把一次文献阅读评测建成"判得动、跑得一致、查得回、改得动"的最小可复算闭环。
  定义题卡字段规范（含输入类型/难度/失败模式矩阵），固定运行器把 Agent 输出归一到可评分目录，
  规则评分表按 0/1/2 逐题计分并保留判分依据，分数可顺题目 ID 追到原始输出与配置，失败样例归因到题型并只重算受影响分数。
  全程真实执行：先落盘最小 result.json 再充实；金标准与评分规则必须随题集交付、可被脚本复算；不虚构任何分数或案例结果。
---

# 文献阅读 Benchmark 与评测工具 — 可复算最小闭环 Skill（v1）

## 1. 用途与适用范围

- 适用：围绕一个文献阅读任务（问答/提取/核验/解析）建设可运行、可版本化的题集与评测工具，输出原始结果、逐题得分、汇总面板与失败分析。
- 不适用（不做也不报）：完整评测系统平台开发、PDF 像素级解析、联网检索建题、自带正式测试案例或预制答案。
- 四个验收问题（本题主线，每步都要回答）：
  1. **判得动**：任务/输入/参考答案/评分规则齐备，不同人看同一输出给同一结论。
  2. **跑得一致**：固定工具权限与预算重复运行，分数稳定且波动被记录。
  3. **查得回**：每个分数顺题目 ID 可追到原始输出、运行配置、评分记录。
  4. **改得动**：失败能归到题型，转化为专项题，且只重算受影响分数。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：提取 `case_id`（**原样保留，禁止改写**）与 `output_contract` 全字段——result.json 逐字段落实；冲突时以 case.json 为准并记入 run_log。
2. 读 `/input/task.md`：确认本次要求建题的方向（题集管理/统一运行器/评分表/结果面板/失败样例库/版本对比，选明确的一个或两个）与证据范围。
3. `ls -la /input/` 盘点材料：记录每个文件名、类型、大小。**只依据实际文件执行，不依据文件名/标签猜测内容。**
4. 材料缺失或为空 → result.json 写 `status=failed` + `failure_reason`，不虚构；部分缺失 → 可跑部分照跑，缺口如实登记。

## 3. 工作流程（六步流水线，每步留痕）

### Step 1 题集设计（→ /app/work/items.jsonl，题卡规范）

每道题一张题卡，必填字段（缺一不可，脚本可校验）：

| 字段 | 含义 | 验收 |
|---|---|---|
| `item_id` | 全局唯一，形如 `ITEM-<题型>-<序号>` | 与输出、得分可互相追查 |
| `task_type` | 题型：qa 问答 / extraction 提取 / verification 核验 / parsing 解析 | 失败归因的基本单位 |
| `input_type` | 输入类型：plaintext / table_text / paragraph_numbered / pdf_text / figure_caption | 见下方矩阵 |
| `difficulty` | easy / medium / hard（判据：所需跨段数与条件数） | ≥2 档 |
| `prompt` | 题目指令（固定措辞，进入运行器） | 原样进入运行 |
| `input_material_ref` | 输入材料文件+定位（页/段/表） | 每题可回查 |
| `reference_answer` | 金标准答案（字段级，含单位/条件） | 评分脚本可复算 |
| `scoring_rule` | 0/1/2 评分规则（见 Step 3），机器可执行 | 不同人复核同分 |
| `failure_modes` | 预登记失败模式（漏条件/单位换算/数值抄错/over-claim/not_found 误答） | 每题 ≥1 项 |
| `data_license` | 数据来源与授权状态 | 如实登记 |

**输入类型 × 难度 × 失败模式矩阵（题集覆盖要求，缺格要说明）**：至少 3 种 input_type × 2 档 difficulty 的组合，每种组合 ≥1 题；矩阵中空缺的组合在 coverage 里登记为 gap 而不是沉默。

- 验收断言：`python3 scripts/validate_itemcard.py items.jsonl` 退出码 0；题数 ≥6 且矩阵无未登记空格。

### Step 2 统一运行器（→ /app/work/runs/）

- 固定四要素并写入 `run_config.json`：工具权限（只读材料+输出目录）、提示模板、资源预算（64 请求/900 秒）、输出格式（JSONL：`item_id, raw_output, parsed_answer`）。
- 每次运行一个目录 `runs/<run_id>/`：`run_config.json` + `outputs.jsonl`（原始输出逐字留存）+ `manifest.json`（时间、输入哈希）。**重复运行 run_id 递增，原始输出不覆盖**——这是"查得回"的物证。
- Agent 没答的题照记：`parsed_answer=null`，算错不算缺席。
- 验收断言：outputs.jsonl 行数 = 题数；每行有 item_id 且能反查题卡。

### Step 3 规则评分（→ /app/work/scores.jsonl，可复算）

评分档位固定 0/1/2，规则按题型取以下之一并写进题卡：

| 规则 | 2 分 | 1 分 | 0 分 |
|---|---|---|---|
| `exact` | 与金标准逐字一致（空白归一后） | — | 其余 |
| `fields` | 全部必答字段正确（值+单位+条件） | ≥一半字段正确且无错误值 | 有错误值或漏过半 |
| `numeric_tol` | 数值落在容差内且单位正确 | 数值对但单位/条件错 | 数值超容差 |
| `verdict` | 支持度判定正确且引用到位 | 判定正确但证据缺失 | 判定错误 |

- **评分必须脚本复算**：`python3 scripts/run_and_score.py --items items.jsonl --outputs runs/<run_id>/outputs.jsonl --out scores.jsonl`。人工只处理脚本判"争议"（rule 无法执行的题），人工分记入 `scores_manual.jsonl` 并写判分依据。
- 每行得分：`{item_id, run_id, score, rule, detail, judge: auto|manual, basis}`——`basis` 是"查得回"的钥匙。
- 验收断言：scores.jsonl 行数 = 题数；manual 行必有 basis；重跑脚本两次分数一致。

### Step 4 汇总面板（→ /app/output/panel.json + panel.csv）

- 按 `task_type × input_type × difficulty` 三维汇总：均分、0/1/2 分布、题数。
- 明确写出优势区（均分=2 的组合）与短板区（均分≤1 的组合），**不允许只报一个总分**。
- 运行间波动：同配置 ≥2 次运行时，逐题对比，波动题登记 `fluctuating: true` 并解释原因。

### Step 5 失败样例库与专项题（→ /app/output/failures.jsonl + next_items.jsonl）

- score≤1 的题逐条整理：`{item_id, task_type, failure_mode, raw_output_excerpt, expected, actual, root_cause}`——根因必须落在题卡预登记的 failure_modes 内或新增登记。
- 每个失败模式转化为 ≥1 道专项题（复用题卡规范，标注 `derived_from`），写入 next_items.jsonl。
- **改得动的证据**：给出只重算受影响分数的命令示例（`run_and_score.py --only ITEM-xxx`），不重算无关分数。

### Step 6 result.json 落盘（先最小后充实）

- 进入 Step 2 前先写最小 result.json（status=partial），任何中断都有可评分产物；走完再覆盖完整版。
- 验收断言：`python3 scripts/run_and_score.py --selftest` 通过；result.json 含 case_id 与 output_contract 全字段。

## 4. 输出契约

result.json 顶层字段（以 case.json output_contract 为最高优先，以下为基准全集）：

```json
{
  "case_id": "<从 /input/case.json 原样读取>",
  "status": "success | partial | failed",
  "deliverables": {
    "items": "items.jsonl",
    "run_config": "runs/<run_id>/run_config.json",
    "scores": "scores.jsonl",
    "panel": "panel.json",
    "failures": "failures.jsonl",
    "next_items": "next_items.jsonl",
    "run_log": "run_log.md"
  },
  "benchmark_summary": {
    "total_items": 0,
    "matrix_coverage": {"input_type_x_difficulty_filled": 0, "gaps": ["<空缺组合与原因>"]},
    "mean_score": 0.0,
    "score_distribution": {"0": 0, "1": 0, "2": 0},
    "weak_cells": ["<均分≤1 的 task_type×input_type×difficulty 组合>"]
  },
  "evidence_and_boundary": {
    "recompute_command": "python3 scripts/run_and_score.py --items items.jsonl --outputs runs/<run_id>/outputs.jsonl --out scores.jsonl",
    "manual_judged": ["<人工判分题 id 与判分依据>"],
    "not_reported": ["<材料未提供的项，如实登记>"]
  },
  "sources": ["<实际使用的输入文件>"],
  "uncertainty_notes": ["<判分争议与波动解释>"],
  "change_log": ["<partial→完整版变化>"]
}
```

- `status=success`：题集+运行+评分+面板+失败库全链走通且脚本复算通过；`partial`：链路有缺口（如材料只够建题不够跑运行）；`failed`：材料缺失不可执行。partial/failed 必须写明界限与可人工接管位置。

## 5. 数字门槛（达不到诚实标 partial）

1. 题卡 10 字段齐全，validate_itemcard.py 退出码 0。
2. 矩阵覆盖：input_type×difficulty 组合 ≥3，空格有 gap 登记。
3. scores.jsonl 每行有 rule+judge+basis，脚本重跑两次一致。
4. panel.json 按三维汇总，含弱项区，不只报总分。
5. 失败样例每条有 root_cause 且对应专项题 ≥1。
6. 每个分数可顺 item_id → run_id → outputs.jsonl 原始输出 → basis 逐级追查。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 材料不足以构造金标准 | 该题 scoring_rule 标 `manual_only`，不伪造金标准；登记 not_reported |
| 题目缺参考答案 | 不给分也不给 0——登记为 `unscored`，面板单独列 |
| 输出为空/超长/格式不合规 | parsed_answer=null 或截断留痕，按规则计 0 分并记 failure_mode=format_break |
| 文件损坏/权限不足 | 记 run_log，受影响题标 `skipped_input_error`，不冒充已评 |
| 重复运行分数波动 | 不取最好一次；逐题登记 fluctuating 并解释（温度/解析非确定性） |
| 评分规则对某题不可执行 | 判"争议"转人工，basis 必填 |
| output_contract 与本文冲突 | 以 case.json 为准，run_log 记录差异 |

## 7. 自查清单（提交前逐项过）

- [ ] case_id 原样；output_contract 字段全覆盖
- [ ] 题卡 10 字段齐；矩阵无未登记空格
- [ ] 评分可复算：脚本退出码 0，重跑同分
- [ ] 每个分数可追到原始输出与判分依据
- [ ] 面板三维汇总、弱项明确
- [ ] 失败样例→专项题→只重算受影响分数，链条闭合
- [ ] 未报告/无法判断项如实登记，无编造分数

## 8. 效率约束

预算 64 请求 / 900 秒 / 单响应 16384 token。策略：建题、校验、评分、面板全部脚本化（不耗模型请求）；模型请求只用于按材料生成金标准与判分依据；先落盘最小 result.json 再充实。资源限额 ≤50 文件 / 单文件 ≤500KB / 总量 ≤2MB。

## 9. 最小示例（示意输出，非正式案例结果）

题卡（items.jsonl 一行）：

```json
{"item_id":"ITEM-qa-001","task_type":"qa","input_type":"paragraph_numbered","difficulty":"medium","prompt":"按段落回答：该催化剂在什么条件下活性最高？给出段落号。","input_material_ref":"material.txt#P012-P018","reference_answer":{"value":"350 C, H2/CO2=3","conditions":["常压"],"locators":["P015"]},"scoring_rule":"fields","failure_modes":["漏条件","单位换算"],"data_license":"synthetic-demo"}
```

scores.jsonl 片段：`{"item_id":"ITEM-qa-001","run_id":"R001","score":1,"rule":"fields","detail":"值与单位正确但缺常压条件","judge":"auto","basis":"fields 规则：≥一半字段正确且无错误值"}`

panel.json 片段：`{"weak_cells":[{"task_type":"qa","input_type":"table_text","difficulty":"hard","mean":0.67,"n":3}]}`

（以上均为格式示意，正式案例结果以实际运行为准。）
