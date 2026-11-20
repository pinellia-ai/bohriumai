# study-quality-appraiser — 文献研究质量评价

> 波尔产品周赛第4期 · search 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「文献研究质量评价」的可调用 Skill（study-quality-appraiser）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装至评测环境 skill 目录后，官方 DeepSeek Harness 在 3 个固定案例上运行（64 请求/900秒/16384token），与基础 Agent 对照评分。离线语料口径：仅依据组织方快照，不声称实时检索与全球覆盖。

## 2. 快速调用

- 触发："请按本 Skill 按固定维度评价文献研究质量并锚定原文"
- 输入：`/input/case.json`（含 case_id、任务、语料清单、output_contract）+ 语料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  研究设计（横断面/队列/RCT/案例报告）能否支持其结论强度？相关被说成因果 → 降档，引原文结论句。
-  样本量/代表性（有无说明）、对照组设置、统计方法适用性（检验选择、多重比较校正）、效应量与显著性报告完整性——逐项对照表格数据。
-  选择偏倚（入组方式）、测量偏倚（指标定义）、混杂控制（校正与否）、失访（随访率）——每项判断引用原文位置，risk: low/moderate/high。
-  必要要素核查：方法细节、样本描述、统计声明、局限声明——缺项逐条列出。
-  结论是否超出数据与条件范围（外推、绝对化表述），引原文对照。

## 4. 契约速览

- case_id 原样；status ∈ success|partial|failed；每条结果带来源定位与原文短句。
- gaps/uncertainty_notes 诚实登记；status=partial 时已完成部分完整可交。
- 不编造记录/引用/状态/覆盖。

## 5. 异常速查

| 情况 | 处置 |
|---|---|
| 语料缺失/损坏 | status=failed |
| 子任务零命中/无数据 | 如实登记 + 已试策略列表 |
| 预算不足 | 落盘 partial，gaps 列剩余 |
| contract 与本文件冲突 | 以 case.json output_contract 为准 |

## 6. 复用与版本

- v1（p4 首发）；再跑按 SKILL.md §3 流程；自查清单见 SKILL.md §6。
