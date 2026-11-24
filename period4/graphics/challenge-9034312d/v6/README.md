# 实验装置与技术路线图 — Skill 使用说明（v6 执行版）

## 用途
实验装置与技术路线图：组件/步骤逐条有依据，连接与流向正确，渲染真实，参数标注可回溯。

## 触发语句示例
- “按材料完成实验装置与技术路线图任务，给出可复核的结果与对账表。”
- “对 /input/ 的科研材料执行实验装置与技术路线图流水线，交付 result.json 与证据清单。”

## 调用步骤
1. 读 `/input/case.json` 的 output_contract 与 task.md（Step 0）。
2. 按 SKILL.md §2 流水线逐步执行，产物写 `/app/output/`。
3. 跑 scripts/reconcile.py 对账；未过门槛按 §4/§5 处置。
4. 交付 result.json + 对账 CSV + run_log.md + scoring_sheet.csv。

## 输出契约速览
result.json 含 output_contract 全部字段 + case_id 原样 + status 诚实 + deliverables/reconciliation/gaps。

## 数字门槛
1. 组件/连接计数对账通过；悬空端点 = 0
2. 每组件/连接有依据；参数标注可回指原文
3. 渲染预览真实生成；图例与单位齐全
4. 分支判据显式标注

## 异常与限制
- 材料缺失/扫描件/依赖不可用：见 SKILL.md §5 异常表；partial 诚实交付。
- 不虚构材料外事实；删除类操作只出计划待确认。

## 复用说明
scripts/ 内脚本可独立复用于同类清点/对账任务；SKILL.md 流水线可换材料直接复用。
