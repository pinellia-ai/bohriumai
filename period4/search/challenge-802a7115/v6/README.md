# 跨语言文献检索 — Skill 使用说明（v6 执行版）

## 用途
跨语言文献检索：多语检索式对齐，命中跨语去重，术语映射有依据，覆盖度可验收。

## 触发语句示例
- “按材料完成跨语言文献检索任务，给出可复核的结果与对账表。”
- “对 /input/ 的科研材料执行跨语言文献检索流水线，交付 result.json 与证据清单。”

## 调用步骤
1. 读 `/input/case.json` 的 output_contract 与 task.md（Step 0）。
2. 按 SKILL.md §2 流水线逐步执行，产物写 `/app/output/`。
3. 跑 scripts/reconcile.py 对账；未过门槛按 §4/§5 处置。
4. 交付 result.json + 对账 CSV + run_log.md + scoring_sheet.csv。

## 输出契约速览
result.json 含 output_contract 全部字段 + case_id 原样 + status 诚实 + deliverables/reconciliation/gaps。

## 数字门槛
1. 概念×语种覆盖矩阵齐全；缺口显式登记
2. 去重后总数 = 各语种命中之和 - 去重组重复数（对账）
3. 每命中有原文逐字句；跨语匹配抽样验证记录
4. 术语映射每行有依据；零命中有原因

## 异常与限制
- 材料缺失/扫描件/依赖不可用：见 SKILL.md §5 异常表；partial 诚实交付。
- 不虚构材料外事实；删除类操作只出计划待确认。

## 复用说明
scripts/ 内脚本可独立复用于同类清点/对账任务；SKILL.md 流水线可换材料直接复用。
