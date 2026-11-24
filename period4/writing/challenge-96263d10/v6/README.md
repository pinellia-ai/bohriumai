# 学术格式与模板适配 — Skill 使用说明（v6 执行版）

## 用途
学术格式与模板适配：把目标模板拆成规则清单，逐条执行逐条验收，差异可复算。

## 触发语句示例
- “按材料完成学术格式与模板适配任务，给出可复核的结果与对账表。”
- “对 /input/ 的科研材料执行学术格式与模板适配流水线，交付 result.json 与证据清单。”

## 调用步骤
1. 读 `/input/case.json` 的 output_contract 与 task.md（Step 0）。
2. 按 SKILL.md §2 流水线逐步执行，产物写 `/app/output/`。
3. 跑 scripts/reconcile.py 对账；未过门槛按 §4/§5 处置。
4. 交付 result.json + 对账 CSV + run_log.md + scoring_sheet.csv。

## 输出契约速览
result.json 含 output_contract 全部字段 + case_id 原样 + status 诚实 + deliverables/reconciliation/gaps。

## 数字门槛
1. rules.csv 每条规则在 compliance.csv 有且仅有一条判定
2. violation 数 = changes.csv 行数 + needs_manual 数（对账）
3. recheck 残留违规 = 0 或全部转 needs_manual 并说明
4. docx_inventory 修改前后计数差异与 changes 记录一致

## 异常与限制
- 材料缺失/扫描件/依赖不可用：见 SKILL.md §5 异常表；partial 诚实交付。
- 不虚构材料外事实；删除类操作只出计划待确认。

## 复用说明
scripts/ 内脚本可独立复用于同类清点/对账任务；SKILL.md 流水线可换材料直接复用。
