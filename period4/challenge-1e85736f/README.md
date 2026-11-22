# incremental-literature-tracker — 最新文献发现与追踪

> 波尔产品周赛第4期 · search 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「最新文献发现与追踪」的可调用 Skill（incremental-literature-tracker）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装至评测环境 skill 目录后，官方 DeepSeek Harness 在 3 个固定案例上运行（64 请求/900秒/16384token），与基础 Agent 对照评分。离线语料口径：仅依据组织方快照，不声称实时检索与全球覆盖。

## 2. 快速调用

- 触发："请按本 Skill 判定文献增量新增并过滤版本/重复噪声"
- 输入：`/input/case.json`（含 case_id、任务、语料清单、output_contract）+ 语料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  从导入状态建立基线集合：`{record_id, batch, first_seen}`——"新"的定义=不在基线中的记录。
-  预印本→正式版→修订/勘误 按标识符与版本关系归并成**一条实体**的版本链。
-  判定类型：`new_work（全新论文）| new_version（已知论文的新版本）| late_indexed（旧文新入库）| duplicate（转载）| retraction（撤稿/更正）`。
-  new_version 与 new_work 分开报告——用户要的是"新东西"，不是"旧文的第 2 版冒充新发现"。
-  对每条非基线记录给出判定与依据（标识符关联/日期对比/重复文本）。
-  重复转载：与基线内容一致的记录标 duplicate 并给匹配依据，不进"新发现"列表。

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
