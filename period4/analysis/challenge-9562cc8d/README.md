# 科研数据可视化 — Skill 使用说明（v6 执行版）

## 用途
科研数据可视化：图表选型有依据，数据-图形逐点对账，渲染真实，标注规范可复核。

## 触发语句示例
- “按材料完成科研数据可视化任务，给出可复核的结果与对账表。”
- “对 /input/ 的科研材料执行科研数据可视化流水线，交付 result.json 与证据清单。”

## 调用步骤
1. 读 `/input/case.json` 的 output_contract 与 task.md（Step 0）。
2. 按 SKILL.md §2 流水线逐步执行，产物写 `/app/output/`。
3. 跑 scripts/reconcile.py 对账；未过门槛按 §4/§5 处置。
4. 交付 result.json + 对账 CSV + run_log.md + scoring_sheet.csv。

## 输出契约速览
result.json 含 output_contract 全部字段 + case_id 原样 + status 诚实 + deliverables/reconciliation/gaps。

## 数字门槛
1. 每图有选型依据与编码映射；渲染文件真实存在
2. 数据系列数对账通过；抽样点与原始数据一致
3. 轴/单位/图例齐全；误导性处理显式标注
4. 绘图脚本可复跑得到相同图形

## 异常与限制
- 材料缺失/扫描件/依赖不可用：见 SKILL.md §5 异常表；partial 诚实交付。
- 不虚构材料外事实；删除类操作只出计划待确认。

## 复用说明
scripts/ 内脚本可独立复用于同类清点/对账任务；SKILL.md 流水线可换材料直接复用。
