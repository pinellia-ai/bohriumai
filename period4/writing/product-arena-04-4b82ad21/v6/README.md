# 写作08｜引言与相关工作写作 — Skill 使用说明（v6 执行版）

## 用途
引言与相关工作写作：研究缺口从文献对比推出，论断逐条绑定引用，逻辑链可复核。

## 触发语句示例
- “按材料完成写作08｜引言与相关工作写作任务，给出可复核的结果与对账表。”
- “对 /input/ 的科研材料执行写作08｜引言与相关工作写作流水线，交付 result.json 与证据清单。”

## 调用步骤
1. 读 `/input/case.json` 的 output_contract 与 task.md（Step 0）。
2. 按 SKILL.md §2 流水线逐步执行，产物写 `/app/output/`。
3. 跑 scripts/reconcile.py 对账；未过门槛按 §4/§5 处置。
4. 交付 result.json + 对账 CSV + run_log.md + scoring_sheet.csv。

## 输出契约速览
result.json 含 output_contract 全部字段 + case_id 原样 + status 诚实 + deliverables/reconciliation/gaps。

## 数字门槛
1. works 行数 = 材料相关工作数；每缺口有支撑 doc_id
2. 每论断有绑定；悬空引用数 = 0
3. 贡献-gap 对齐检查通过；术语违规 = 0 或豁免说明
4. 逻辑链四段齐全；材料外事实数 = 0

## 异常与限制
- 材料缺失/扫描件/依赖不可用：见 SKILL.md §5 异常表；partial 诚实交付。
- 不虚构材料外事实；删除类操作只出计划待确认。

## 复用说明
scripts/ 内脚本可独立复用于同类清点/对账任务；SKILL.md 流水线可换材料直接复用。
