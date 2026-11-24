# 文献数据清洗与标准化 — Skill 使用说明（v6 执行版）

## 用途
文献数据清洗与标准化：单位/命名/格式统一有规则表，转换前后对账，原始值可回溯。

## 触发语句示例
- “按材料完成文献数据清洗与标准化任务，给出可复核的结果与对账表。”
- “对 /input/ 的科研材料执行文献数据清洗与标准化流水线，交付 result.json 与证据清单。”

## 调用步骤
1. 读 `/input/case.json` 的 output_contract 与 task.md（Step 0）。
2. 按 SKILL.md §2 流水线逐步执行，产物写 `/app/output/`。
3. 跑 scripts/reconcile.py 对账；未过门槛按 §4/§5 处置。
4. 交付 result.json + 对账 CSV + run_log.md + scoring_sheet.csv。

## 输出契约速览
result.json 含 output_contract 全部字段 + case_id 原样 + status 诚实 + deliverables/reconciliation/gaps。

## 数字门槛
1. 行数守恒；每被改值有 transform_log 记录
2. 单位集合唯一；命名变体清零或豁免说明
3. 抽样反算验证通过；原始数据副本保留
4. 换算公式全部写明可复核

## 异常与限制
- 材料缺失/扫描件/依赖不可用：见 SKILL.md §5 异常表；partial 诚实交付。
- 不虚构材料外事实；删除类操作只出计划待确认。

## 复用说明
scripts/ 内脚本可独立复用于同类清点/对账任务；SKILL.md 流水线可换材料直接复用。
