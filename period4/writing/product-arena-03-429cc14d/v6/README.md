# 写作04｜参考文献与引用管理 — Skill 使用说明（v6 执行版）

## 用途
参考文献与引用管理：文内引用-文献表双向闭合，著录字段齐全，孤儿悬空逐条清零。

## 触发语句示例
- “按材料完成写作04｜参考文献与引用管理任务，给出可复核的结果与对账表。”
- “对 /input/ 的科研材料执行写作04｜参考文献与引用管理流水线，交付 result.json 与证据清单。”

## 调用步骤
1. 读 `/input/case.json` 的 output_contract 与 task.md（Step 0）。
2. 按 SKILL.md §2 流水线逐步执行，产物写 `/app/output/`。
3. 跑 scripts/reconcile.py 对账；未过门槛按 §4/§5 处置。
4. 交付 result.json + 对账 CSV + run_log.md + scoring_sheet.csv。

## 输出契约速览
result.json 含 output_contract 全部字段 + case_id 原样 + status 诚实 + deliverables/reconciliation/gaps。

## 数字门槛
1. citations 行数 = 脚本命中数；refs 行数 = 文献区条目数
2. 修复后孤儿引用 = 0、悬空条目 = 0（或显式 needs_manual）
3. 著录字段缺失全部标 missing；不编造 DOI/年份
4. 每条修复有 changes 记录

## 异常与限制
- 材料缺失/扫描件/依赖不可用：见 SKILL.md §5 异常表；partial 诚实交付。
- 不虚构材料外事实；删除类操作只出计划待确认。

## 复用说明
scripts/ 内脚本可独立复用于同类清点/对账任务；SKILL.md 流水线可换材料直接复用。
