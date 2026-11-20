# kb-qa-with-citations — 科研知识库问答

> 波尔产品周赛第4期 · library 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「科研知识库问答」的可调用 Skill（kb-qa-with-citations）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装后由官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 基于知识库回答问题并逐句带可回链引用"
- 输入：`/input/case.json`（含 case_id、任务、材料位置、output_contract）+ 材料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  问题拆解 → 关键词/概念查询 → 候选片段：`{file, version, locator, 原文短句}`。
-  版本敏感：同一材料多版本时，引用**与问题时间/版本语境匹配**的版本并说明。
-  每个论断句附引用：`[文件名 v2, p3 para1]`——引用与论断严格对应。
-  综合多文件时逐条引用，不合并成模糊出处。
-  自查：每条引用回原文核对——引用的文件/段落/版本与论断内容一致（错位=回改）。
-  回链路径写明：读者按引用能一步找到原文。

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
