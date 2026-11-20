# screening-smart-ranking — 文献筛选与智能排序

> 波尔产品周赛第4期 · search 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「文献筛选与智能排序」的可调用 Skill（screening-smart-ranking）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装至评测环境 skill 目录后，官方 DeepSeek Harness 在 3 个固定案例上运行（64 请求/900秒/16384token），与基础 Agent 对照评分。离线语料口径：仅依据组织方快照，不声称实时检索与全球覆盖。

## 2. 快速调用

- 触发："请按本 Skill 对候选文献全量筛选并给出可解释排序"
- 输入：`/input/case.json`（含 case_id、任务、语料清单、output_contract）+ 语料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  判据表：`{criterion_id, 维度(对象/设计/人群/类型/时间), 判定规则, 权重}`。
-  每条判据可第三方复核（写成"什么样的记录满足"）。
-  对**全部记录**逐条判定：`relevant | partially_relevant | not_relevant`，每条给依据（引摘要原文短句，不是标题）。
-  类型分离：review vs original research；preprint vs published version——同文多版本归并为一条（按 DOI/标识符），版本状态标注。
-  重复导出（同一论文不同格式出现）：按标识符归并 + dup_of 记录。
-  冲突意见（元数据互斥）：并列保留双方，标注 conflict，不擅自择一。

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
