# topic-selection-evaluator — 科研选题与创新性评估

> 波尔产品周赛第4期 · research 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「科研选题与创新性评估」的可调用 Skill（topic-selection-evaluator）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装后由官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 评估选题创新性与可行性（四面对照）"
- 输入：`/input/case.json`（含 case_id、任务、材料位置、output_contract）+ 材料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  选题表述 → 可检验命题：`{自变量, 因变量/指标, 对照/比较基准, 判定标准}`。
-  不可检验表述（"探索 X 的应用"）→ 改写建议 + 原表述问题说明。
-  已做到哪：按最近工作列 `谁+做了什么+到什么程度+局限`（逐条文献定位）。
-  与选题直接相关的**最近邻工作**重点标出——创新性对照对象。
-  选题 vs 最近邻工作：差异逐项（对象/方法/条件/指标）。
-  创新性分级：`incremental（增量改进）| combinatorial（组合迁移）| novel（全新问题/方法）`——分级依据=差异项数量与性质；禁用"首次/领先"空词。

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
