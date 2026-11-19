# smart-file-finder — 科研文件智能检索

> 波尔产品周赛第4期 · library 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「科研文件智能检索」的可调用 Skill（smart-file-finder）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装后由官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 跨目录内容级检索科研文件并给出处"
- 输入：`/input/case.json`（含 case_id、任务、材料位置、output_contract）+ 材料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  遍历范围（含子目录），登记 `{path, type, size, mtime, text_extractable}`；内容抽取到 /app/work 索引。
-  改名副本/修订版/扫描件：按内容相似+时间戳+元数据归并同一材料的形态链；检索结果标形态（原文/修订版/扫描）。
-  问题拆解 → 关键词/概念查询（内容级，不只文件名）；每条结果：`{file, version, locator(页/行/段落), match_evidence(命中原文短句), relevance}`。
-  多个候选时按匹配度排序，并列说明差异。
-  找不到：报告已检索范围（哪些目录/哪些类型）、排除原因（权限/不可读）；不编造"大概在某文件"。

## 4. 契约速览

- case_id 原样；status ∈ success|partial|failed；每条结果/判定带来源定位。
- gaps/uncertainty 诚实登记；partial 时已完成部分完整可交；不编造。

## 5. 异常速查

| 情况 | 处置 |
|---|---|
| 输入缺失/损坏 | status=failed 写明 |
| 无法判定 | needs_review / uncertainty，不硬判 |
| 预算不足 | 落盘 partial，gaps 列剩余 |
| contract 与本文件冲突 | 以 case.json output_contract 为准 |

## 6. 复用与版本

- v1（p4 首发）；自查清单见 SKILL.md §6。
