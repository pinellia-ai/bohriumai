# coverage-gap-analyzer — 检索覆盖率与遗漏分析

> 波尔产品周赛第4期 · search 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「检索覆盖率与遗漏分析」的可调用 Skill（coverage-gap-analyzer）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装至评测环境 skill 目录后，官方 DeepSeek Harness 在 3 个固定案例上运行（64 请求/900秒/16384token），与基础 Agent 对照评分。离线语料口径：仅依据组织方快照，不声称实时检索与全球覆盖。

## 2. 快速调用

- 触发："请按本 Skill 审计检索覆盖率并归因遗漏"
- 输入：`/input/case.json`（含 case_id、任务、语料清单、output_contract）+ 语料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  参照集 = 组织方提供的文献全集/标注相关集。明确记录分母定义与大小。
-  禁止用检索命中反推应检集合。
-  参照集 ∩ 检索命中 = 已检出；参照集 - 命中 = **遗漏清单**（逐条列出，含 ID）。
-  覆盖率 = |已检出 ∩ 参照相关集| / |参照相关集|，按快照口径表述（不宣称全局覆盖率）。
-  每条遗漏检查：哪个查询式漏了它（逐查询式回放匹配）？哪个字段本可命中（标题/摘要/关键词）？哪个限定（时间窗/类型过滤）排除了它？
-  归因输出：`{record_id, missed_by_query:[...], fixable_field:"abstract 未检索", root_cause:"查询式q2未含术语X"}`。

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
