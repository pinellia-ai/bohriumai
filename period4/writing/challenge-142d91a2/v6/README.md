# 写作15｜开题报告与研究计划书 — Skill 使用说明（v6 执行版）

## 用途
开题报告与研究计划书：要素齐全性逐项验收，研究问题-方法-预期成果对齐，来源可溯。

## 触发语句示例
- “按材料完成写作15｜开题报告与研究计划书任务，给出可复核的结果与对账表。”
- “对 /input/ 的科研材料执行写作15｜开题报告与研究计划书流水线，交付 result.json 与证据清单。”

## 调用步骤
1. 读 `/input/case.json` 的 output_contract 与 task.md（Step 0）。
2. 按 SKILL.md §2 流水线逐步执行，产物写 `/app/output/`。
3. 跑 scripts/reconcile.py 对账；未过门槛按 §4/§5 处置。
4. 交付 result.json + 对账 CSV + run_log.md + scoring_sheet.csv。

## 输出契约速览
result.json 含 output_contract 全部字段 + case_id 原样 + status 诚实 + deliverables/reconciliation/gaps。

## 数字门槛
1. requirements 逐项验收；缺项显式 gap 不冒充齐全
2. alignment 每行问题-方法-成果闭环；无证据论断数 = 0
3. 进度日期顺序检查通过；引用闭合
4. gaps 全部显式登记并给补齐建议

## 异常与限制
- 材料缺失/扫描件/依赖不可用：见 SKILL.md §5 异常表；partial 诚实交付。
- 不虚构材料外事实；删除类操作只出计划待确认。

## 复用说明
scripts/ 内脚本可独立复用于同类清点/对账任务；SKILL.md 流水线可换材料直接复用。
