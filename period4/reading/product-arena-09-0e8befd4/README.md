# 阅读14｜Nanopublication — Skill 使用说明（v6 执行版）

## 用途
Nanopublication：断言-证据-出处三元组逐条结构化，标识符闭合，可序列化可复核。

## 触发语句示例
- “按材料完成阅读14｜Nanopublication任务，给出可复核的结果与对账表。”
- “对 /input/ 的科研材料执行阅读14｜Nanopublication流水线，交付 result.json 与证据清单。”

## 调用步骤
1. 读 `/input/case.json` 的 output_contract 与 task.md（Step 0）。
2. 按 SKILL.md §2 流水线逐步执行，产物写 `/app/output/`。
3. 跑 scripts/reconcile.py 对账；未过门槛按 §4/§5 处置。
4. 交付 result.json + 对账 CSV + run_log.md + scoring_sheet.csv。

## 输出契约速览
result.json 含 output_contract 全部字段 + case_id 原样 + status 诚实 + deliverables/reconciliation/gaps。

## 数字门槛
1. nanopubs 数 = assertions 行数；每条三层结构齐全
2. np_id 唯一；无证据断言全部显式 unverifiable
3. 抽样 10 条回查通过并记录
4. 冲突断言对显式登记待人工确认

## 异常与限制
- 材料缺失/扫描件/依赖不可用：见 SKILL.md §5 异常表；partial 诚实交付。
- 不虚构材料外事实；删除类操作只出计划待确认。

## 复用说明
scripts/ 内脚本可独立复用于同类清点/对账任务；SKILL.md 流水线可换材料直接复用。
