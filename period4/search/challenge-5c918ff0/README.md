# multi-db-merge-dedup — 多数据库联合检索

> 波尔产品周赛第4期 · search 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「多数据库联合检索」的可调用 Skill（multi-db-merge-dedup）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装至评测环境 skill 目录后，官方 DeepSeek Harness 在 3 个固定案例上运行（64 请求/900秒/16384token），与基础 Agent 对照评分。离线语料口径：仅依据组织方快照，不声称实时检索与全球覆盖。

## 2. 快速调用

- 触发："请按本 Skill 合并多库检索结果并按标识符去重"
- 输入：`/input/case.json`（含 case_id、任务、语料清单、output_contract）+ 语料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  每库记录先规范化：作者名统一格式（姓全拼+首字母）、期刊名缩写→全称（对照语料）、标识符提取（DOI 小写去 https 前缀、PMID 纯数字）。
-  规范化规则编号留档，可复跑。
-  主键归并：DOI 精确匹配 > PMID > 标题规范化（小写、去标点、去多余空格）+ 年份容差匹配。
-  归并不确定时（标题近似但标识符缺）：标 `needs_human_review`，不静默合并。
-  输出：唯一论文数 + 合并谱系（哪条来自哪个库）。
-  每个字段取值时标注来源库：冲突值（如两库年份不同）并列保留 + 口径解释，不静默择一。

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
