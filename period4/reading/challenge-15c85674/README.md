# literature-qa-cited-answers — 文献智能问答

> 波尔产品周赛第3期 · Skill 交付包使用与方法说明（文档与 Skill 同版本）

## 1. 这是什么

围绕「文献智能问答」构建的可被 Agent 调用的 Skill（literature-qa-cited-answers）：按 SKILL.md 定义的工作流，在平台固定案例上完成实际任务，交付可独立复核的结果，全程保留来源定位与不确定性说明。核心方法：paragraph index first; per-question sub-question decomposition; three-layer answ。

平台评测方式：本 Skill 被安装到评测环境的 skill 目录，官方 DeepSeek Harness 在 3 个固定案例上运行本 Skill（64 次模型请求 / 900 秒 / 单响应 16384 token 预算），与不加载 Skill 的基础 Agent 对照评分。本包不含、也不需要预制答案。

## 2. 快速调用

- 触发语句示例："请按本 Skill 读取 /input/ 下的论文材料并完成本案例的解析/核验任务"
- 输入：`/input/case.json`（含 case_id、任务说明、材料位置、output_contract）+ 题目材料文件。
- 输出：/app/answers.json（本题主输出）+ /app/output/result.json（平台归档）（字段以 case.json 的 `output_contract` 为最高优先，缺省时按 SKILL.md §4 结构）。
- 过程产物：`/app/work/`（文本抽取、中间数据、核验脚本，可复核）。

## 3. 方法概述（与 SKILL.md 一致）

- paragraph index first; per-question sub-question decomposition; three-layer answer separation reported|interpreted|inferred; every major claim carries paper id + paragraph number + verbatim short quote; uncertainty handling (unreported / partial / conflicts with both paragraph numbers); output /app/answers.json compatible with result.json archive

## 4. 输入输出契约速览

- `case_id` 原样保留；`status ∈ success | partial | failed`；证据定位到页/段/句/表号/图号。
- `gaps`：材料缺失、未提供像素/数值的项——只登记，不构造。
- `uncertainty_notes`：范围限制、单来源、无法判定项。
- `changes`：对草稿/基线的修改记录（如适用）。
- 部分完成时 status=partial：已完成部分完整可交，未完成项列明剩余工作量。

## 5. 适用范围与限制

- 仅依据给定材料执行；不联网、不使用材料外知识补充事实。
- 预算内优先保证最小可用交付，再逐层增强；长任务在预算边缘主动收敛并如实标注。
- 与相邻课题的分工边界见 SKILL.md §1（不越界处理统计计算/版式美化/正文写作等）。

## 6. 异常处理速查

| 情况 | 处置 |
|---|---|
| 输入缺失/损坏 | status=failed 写明缺失项；不编造 |
| 材料与任务约束冲突 | 以实际材料为准，冲突登记 uncertainty_notes |
| 预算不足 | 落盘 partial（已完成部分完整），gaps 列剩余项 |
| 输出 contract 与本文件冲突 | 以 case.json 的 output_contract 为准 |

（完整异常表见 SKILL.md §5）

## 7. 复用与再跑

- 依赖：仅评测环境预装工具（见 environment/resources.yaml）；本包全部为 UTF-8 文本资源，无二进制依赖。
- 再跑：按 SKILL.md §3 工作流以相同输入重跑即得一致结构的结果；数据/材料更新后按相同契约重生成。
- 自查：输出前按 SKILL.md 自查清单逐条核对；`python3 -m json.tool result.json` 验证合法性。

## 8. 版本与维护

- 版本：v2（本次按运行时硬性契约强化 output_contract 合规、尽早落盘与不虚构条款）。
- 维护：结构问题、契约变更、材料 schema 变化时同步修订 SKILL.md 与本文件。
