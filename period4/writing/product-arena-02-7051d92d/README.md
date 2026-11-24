# 写作02｜学术语言润色 — Skill 使用说明（v6 执行版）

## 用途
学术语言润色：逐句修改留痕，事实数字零改动验收，术语一致，风格符合学术语体。

## 触发语句示例
- “按材料完成写作02｜学术语言润色任务，给出可复核的结果与对账表。”
- “对 /input/ 的科研材料执行写作02｜学术语言润色流水线，交付 result.json 与证据清单。”

## 调用步骤
1. 读 `/input/case.json` 的 output_contract 与 task.md（Step 0）。
2. 按 SKILL.md §2 流水线逐步执行，产物写 `/app/output/`。
3. 跑 scripts/reconcile.py 对账；未过门槛按 §4/§5 处置。
4. 交付 result.json + 对账 CSV + run_log.md + scoring_sheet.csv。

## 输出契约速览
result.json 含 output_contract 全部字段 + case_id 原样 + status 诚实 + deliverables/reconciliation/gaps。

## 数字门槛
1. numeric_audit 前后数字差异 = 0；引用标记数一致
2. 每修改有原句新句+理由；无记录修改数 = 0
3. 术语违规 = 0 或豁免说明；语义偷换抽样检查通过
4. 切分句数对账；润色稿可编辑

## 异常与限制
- 材料缺失/扫描件/依赖不可用：见 SKILL.md §5 异常表；partial 诚实交付。
- 不虚构材料外事实；删除类操作只出计划待确认。

## 复用说明
scripts/ 内脚本可独立复用于同类清点/对账任务；SKILL.md 流水线可换材料直接复用。
