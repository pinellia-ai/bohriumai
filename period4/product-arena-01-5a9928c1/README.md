# term-table-translator — 阅读03｜文献翻译

> 波尔产品周赛第4期 · reading 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「阅读03｜文献翻译」的可调用 Skill（term-table-translator）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装至评测环境后，官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 用术语表驱动翻译文献并输出双语对照"
- 输入：`/input/case.json`（含 case_id、任务、材料位置、output_contract）+ 材料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  `{英文原文, 译名, 首现位置, source(original 译名表 | contextual 上下文 | common_sense 显式标注)}`。
-  缩写首现"中文全称（英文缩写）"；歧义缩写按语境选定并登记。
-  译名锁定全篇：后续翻译只查表，每处术语用词与表一致。
-  段号一一对应：`{src_loc → tgt_loc}` 映射表；跨页/跨栏段落归并时保留两端定位。
-  不漏段不重段（count 对账：原文段数 = 译文段数）。
-  指代对象明确（it/they/this 复核先行词）；否定与限定范围保持（not A and B 的覆盖面）；因果与让步强度对应。

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
