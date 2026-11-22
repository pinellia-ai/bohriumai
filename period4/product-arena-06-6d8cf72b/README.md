# structured-paper-notes — 阅读10｜文献总结与结构化笔记

> 波尔产品周赛第4期 · reading 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「阅读10｜文献总结与结构化笔记」的可调用 Skill（structured-paper-notes）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装至评测环境后，官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 生成对齐论文结构的结构化笔记并回链原文"
- 输入：`/input/case.json`（含 case_id、任务、材料位置、output_contract）+ 材料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  笔记主骨架 = 论文自身章节与论证顺序（而非通用模板）：每节笔记对应论文节。
-  套模板处显式标注 mapping（模板字段 ↔ 论文章节）。
-  必录字段：研究问题、数据（来源/规模）、方法条件（参数/设置——结论成立的前提）、主要发现（数值+条件）、局限。
-  **前提条件专门字段**：让结论成立的每个前提单独记录（如"仅在 N=30 雄性样本"）。
-  每条笔记：`{note_id, content, source_locator(章节/段/页/图表号), quote(原文短句≤40词), type(fact | paraphrase | inference)}`。
-  inference 显式标注推断依据，不与 fact 混排。

## 4. 契约速览

- case_id 原样；status ∈ success|partial|failed；关键结论带页码/段落/图表定位。
- gaps/uncertainty 诚实登记；partial 时已完成部分完整可交；不编造。

## 5. 异常速查

| 情况 | 处置 |
|---|---|
| 材料缺失/损坏 | status=failed 写明 |
| 定位失败 | 用章节+段落描述，标注不确定 |
| 预算不足 | 落盘 partial，gaps 列剩余 |
| contract 与本文件冲突 | 以 case.json output_contract 为准 |

## 6. 复用与版本

- v1（p4 首发）；自查清单见 SKILL.md §6。
