# 引文追踪与关联文献发现 — Skill 使用说明（v6 执行版）

## 用途
引文追踪与关联文献发现：引用链逐条有出处，前向/后向追踪计数对账，关联发现有依据。

## 触发语句示例
- “按材料完成引文追踪与关联文献发现任务，给出可复核的结果与对账表。”
- “对 /input/ 的科研材料执行引文追踪与关联文献发现流水线，交付 result.json 与证据清单。”

## 调用步骤
1. 读 `/input/case.json` 的 output_contract 与 task.md（Step 0）。
2. 按 SKILL.md §2 流水线逐步执行，产物写 `/app/output/`。
3. 跑 scripts/reconcile.py 对账；未过门槛按 §4/§5 处置。
4. 交付 result.json + 对账 CSV + run_log.md + scoring_sheet.csv。

## 输出契约速览
result.json 含 output_contract 全部字段 + case_id 原样 + status 诚实 + deliverables/reconciliation/gaps。

## 数字门槛
1. 各种子 backward 行数 = 其文献区条目数（逐一对账）
2. forward 每条有引用句逐字；材料外信息全标 unverifiable
3. 每条关联有依据；聚类成员计数 = 总文献数
4. 追踪边界（材料内/外）显式说明

## 异常与限制
- 材料缺失/扫描件/依赖不可用：见 SKILL.md §5 异常表；partial 诚实交付。
- 不虚构材料外事实；删除类操作只出计划待确认。

## 复用说明
scripts/ 内脚本可独立复用于同类清点/对账任务；SKILL.md 流水线可换材料直接复用。
