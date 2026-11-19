# cross-lingual-search — 跨语言文献检索

> 波尔产品周赛第4期 · search 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「跨语言文献检索」的可调用 Skill（cross-lingual-search）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装至评测环境 skill 目录后，官方 DeepSeek Harness 在 3 个固定案例上运行（64 请求/900秒/16384token），与基础 Agent 对照评分。离线语料口径：仅依据组织方快照，不声称实时检索与全球覆盖。

## 2. 快速调用

- 触发："请按本 Skill 建立多语言术语映射并执行跨语言检索"
- 输入：`/input/case.json`（含 case_id、任务、语料清单、output_contract）+ 语料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  `{概念, 中文, 英文, 其他语言写法(日语转写/德语复合词等，材料内出现的), 缩写与歧义, source(original|contextual|common_sense)}`。
-  映射表是检索依据，也是交付物（可复用）。
-  每个概念 → 每种语言的查询式（原生写法，非翻译腔）；组合查询（英文术语+中文同义词）覆盖语言混合记录。
-  缩写歧义处理：歧义缩写加限定词共现过滤。
-  在语料上按语言变体执行；结果按语言分组；**保留记录原文术语**（不翻译替换），另附中文对照说明。
-  每条结果标注：命中语言变体、匹配字段、原文短句。

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
