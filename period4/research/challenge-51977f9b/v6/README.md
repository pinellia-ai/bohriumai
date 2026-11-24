# 系统性文献综述 — Skill 使用说明（v6 执行版）

## 用途
系统性文献综述：检索-纳排-提取-综合全流程 PRISMA 式计数对账，每步可复核。

## 触发语句示例
- “按材料完成系统性文献综述任务，给出可复核的结果与对账表。”
- “对 /input/ 的科研材料执行系统性文献综述流水线，交付 result.json 与证据清单。”

## 调用步骤
1. 读 `/input/case.json` 的 output_contract 与 task.md（Step 0）。
2. 按 SKILL.md §2 流水线逐步执行，产物写 `/app/output/`。
3. 跑 scripts/reconcile.py 对账；未过门槛按 §4/§5 处置。
4. 交付 result.json + 对账 CSV + run_log.md + scoring_sheet.csv。

## 输出契约速览
result.json 含 output_contract 全部字段 + case_id 原样 + status 诚实 + deliverables/reconciliation/gaps。

## 数字门槛
1. flow 每阶段计数闭合；纳入+排除 = 去重后总数
2. 每排除有理由分类；extraction 每篇齐全或 NR 标注
3. 质量评价逐篇有依据；结论绑定证据强度
4. 检索式与命中数可复跑核对

## 异常与限制
- 材料缺失/扫描件/依赖不可用：见 SKILL.md §5 异常表；partial 诚实交付。
- 不虚构材料外事实；删除类操作只出计划待确认。

## 复用说明
scripts/ 内脚本可独立复用于同类清点/对账任务；SKILL.md 流水线可换材料直接复用。
