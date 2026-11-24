# 阅读03｜文献翻译 — Skill 使用说明（v6 执行版）

## 用途
文献翻译：术语表先行、逐段对齐、数字引用回对，译文忠实可复核。

## 触发语句示例
- “按材料完成阅读03｜文献翻译任务，给出可复核的结果与对账表。”
- “对 /input/ 的科研材料执行阅读03｜文献翻译流水线，交付 result.json 与证据清单。”

## 调用步骤
1. 读 `/input/case.json` 的 output_contract 与 task.md（Step 0）。
2. 按 SKILL.md §2 流水线逐步执行，产物写 `/app/output/`。
3. 跑 scripts/reconcile.py 对账；未过门槛按 §4/§5 处置。
4. 交付 result.json + 对账 CSV + run_log.md + scoring_sheet.csv。

## 输出契约速览
result.json 含 output_contract 全部字段 + case_id 原样 + status 诚实 + deliverables/reconciliation/gaps。

## 数字门槛
1. alignment 行数 = 切分单元数；术语违规 = 0 或豁免说明
2. 数字集合差异 = 0（换算显式登记）；引用编号保留
3. 抽样 10 段忠实性检查记录在案
4. needs_review 全部显式列出

## 异常与限制
- 材料缺失/扫描件/依赖不可用：见 SKILL.md §5 异常表；partial 诚实交付。
- 不虚构材料外事实；删除类操作只出计划待确认。

## 复用说明
scripts/ 内脚本可独立复用于同类清点/对账任务；SKILL.md 流水线可换材料直接复用。
