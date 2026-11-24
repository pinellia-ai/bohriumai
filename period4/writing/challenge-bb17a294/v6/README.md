# 写作12｜学术翻译与双语写作 — Skill 使用说明（v6 执行版）

## 用途
学术翻译与双语写作：术语表先行、逐句对齐、数字回对，译文可复核可回改。

## 触发语句示例
- “按材料完成写作12｜学术翻译与双语写作任务，给出可复核的结果与对账表。”
- “对 /input/ 的科研材料执行写作12｜学术翻译与双语写作流水线，交付 result.json 与证据清单。”

## 调用步骤
1. 读 `/input/case.json` 的 output_contract 与 task.md（Step 0）。
2. 按 SKILL.md §2 流水线逐步执行，产物写 `/app/output/`。
3. 跑 scripts/reconcile.py 对账；未过门槛按 §4/§5 处置。
4. 交付 result.json + 对账 CSV + run_log.md + scoring_sheet.csv。

## 输出契约速览
result.json 含 output_contract 全部字段 + case_id 原样 + status 诚实 + deliverables/reconciliation/gaps。

## 数字门槛
1. alignment.csv 行数 = 原文切分句数（脚本对账）
2. term_check.py 术语违规数 = 0 或逐条豁免说明
3. numeric_audit：原文译文数字集合差异 = 0（单位换算需显式登记）
4. 引用标记数量原文译文一致；needs_review 项全部显式列出

## 异常与限制
- 材料缺失/扫描件/依赖不可用：见 SKILL.md §5 异常表；partial 诚实交付。
- 不虚构材料外事实；删除类操作只出计划待确认。

## 复用说明
scripts/ 内脚本可独立复用于同类清点/对账任务；SKILL.md 流水线可换材料直接复用。
