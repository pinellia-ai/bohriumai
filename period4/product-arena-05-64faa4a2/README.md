# methods-section-writer — 写作09｜方法与实验章节写作

> 波尔产品周赛第4期 · writing 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「写作09｜方法与实验章节写作」的可调用 Skill（methods-section-writer）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装后由官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 写方法与实验章节：参数对齐、复现包齐备"
- 输入：`/input/case.json`（含 case_id、任务、事实底稿、output_contract）+ 材料文件。
- 输出：`/app/output/`（稿件文件 + result.json，字段以 output_contract 为最高优先）。

## 3. 方法概述

-  对照标准清单：关键步骤、实验设置、参数、数据集与划分、对照设置、重复次数、评价指标、环境版本——缺项列出。
-  只留"能读通的主干"不够：复做所需的每个决策点都要写。
-  章节中每个参数回查来源：`{param, value, source(config.yaml line / log / code)}`。
-  **不为段落顺畅补数值**：来源缺失的参数写"未报告"或按 needs_human_review 标注。
-  数据集版本与划分、训练/评测条件与材料严格一致。
-  复现包：环境（依赖版本）、随机种子、硬件（如有）、关键命令/入口——读者照做能跑。

## 4. 契约速览

- case_id 原样；status ∈ success|partial|failed；事实/数字/引用保留来源或修改记录。
- 材料不足与冲突显式标注；partial 时已完成部分完整可交；不编造。

## 5. 异常速查

| 情况 | 处置 |
|---|---|
| 底稿缺失/损坏 | status=failed 写明 |
| 约束冲突 | 以实际材料为准 + 登记 |
| 预算不足 | 落盘 partial，gaps 列剩余 |
| contract 与本文件冲突 | 以 case.json output_contract 为准 |

## 6. 复用与版本

- v1（p4 首发）；自查清单见 SKILL.md §6。
