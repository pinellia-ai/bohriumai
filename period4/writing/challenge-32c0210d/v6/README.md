# 学位论文与长文档写作 — Skill 使用说明（v6 执行版）

## 用途
学位论文与长文档写作：章节规划对账 + 跨章节一致性 + 逐条来源映射 + 可回退改稿。

## 触发语句示例
- “按材料完成学位论文与长文档写作任务，给出可复核的结果与对账表。”
- “对 /input/ 的科研材料执行学位论文与长文档写作流水线，交付 result.json 与证据清单。”

## 调用步骤
1. 读 `/input/case.json` 的 output_contract 与 task.md（Step 0）。
2. 按 SKILL.md §2 流水线逐步执行，产物写 `/app/output/`。
3. 跑 scripts/reconcile.py 对账；未过门槛按 §4/§5 处置。
4. 交付 result.json + 对账 CSV + run_log.md + scoring_sheet.csv。

## 输出契约速览
result.json 含 output_contract 全部字段 + case_id 原样 + status 诚实 + deliverables/reconciliation/gaps。

## 数字门槛
1. outline_map 行数 = 提纲条目数；各节字数合计与任务要求对账
2. term_check.py 违规数 = 0 或逐条标注豁免理由
3. source_map 覆盖全部论断与数字；无来源的论断数 = 0（或显式 gap）
4. xref_audit：编号断号数 = 0、悬空引用数 = 0；docx 清点计数与稿件一致

## 异常与限制
- 材料缺失/扫描件/依赖不可用：见 SKILL.md §5 异常表；partial 诚实交付。
- 不虚构材料外事实；删除类操作只出计划待确认。

## 复用说明
scripts/ 内脚本可独立复用于同类清点/对账任务；SKILL.md 流水线可换材料直接复用。
