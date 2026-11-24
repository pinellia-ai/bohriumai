# methods-stats-reviewer — 研究方法与统计审查

> 波尔产品周赛第4期 · review 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「研究方法与统计审查」的可调用 Skill（methods-stats-reviewer）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装后由官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 出方法与统计审查单"
- 输入：`/input/case.json`（含 case_id、任务、材料位置、output_contract）+ 材料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  设计类型 vs 研究问题匹配（相关设计回答不了因果问题）；对照设置；混杂控制声明。
-  关键变量操作性定义（怎么测的）；自变量/因变量明确；缺失变量定义逐条列出。
-  检验与数据类型/分布假设匹配（如连续非正态用非参）；多重比较校正；方法描述可复算（检验名+自由度/参数）。
-  报告了 n 吗？有依据（功效分析）吗？亚组样本量够吗？——只报稿件层面可确认项。
-  效应量+CI+精确 p（不止"显著"）；检验与描述一致；表格数值与正文一致。

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
