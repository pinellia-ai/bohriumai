# 研究前沿与趋势分析 — Skill 使用说明（v6 执行版）

## 用途
研究前沿与趋势分析：文献计量真实计数，时间线/主题聚类有表可查，结论不超出证据。

## 触发语句示例
- “按材料完成研究前沿与趋势分析任务，给出可复核的结果与对账表。”
- “对 /input/ 的科研材料执行研究前沿与趋势分析流水线，交付 result.json 与证据清单。”

## 调用步骤
1. 读 `/input/case.json` 的 output_contract 与 task.md（Step 0）。
2. 按 SKILL.md §2 流水线逐步执行，产物写 `/app/output/`。
3. 跑 scripts/reconcile.py 对账；未过门槛按 §4/§5 处置。
4. 交付 result.json + 对账 CSV + run_log.md + scoring_sheet.csv。

## 输出契约速览
result.json 含 output_contract 全部字段 + case_id 原样 + status 诚实 + deliverables/reconciliation/gaps。

## 数字门槛
1. corpus 行数 = 材料文献数；yearly 合计 = topics 合计 = corpus 行数
2. 每个前沿判定有 ≥1 条逐字证据与 doc_id 列表
3. 结论引用的每个数字能在 yearly/topics 表中找到
4. 外推结论全部显式标注；矛盾证据不掩盖

## 异常与限制
- 材料缺失/扫描件/依赖不可用：见 SKILL.md §5 异常表；partial 诚实交付。
- 不虚构材料外事实；删除类操作只出计划待确认。

## 复用说明
scripts/ 内脚本可独立复用于同类清点/对账任务；SKILL.md 流水线可换材料直接复用。
