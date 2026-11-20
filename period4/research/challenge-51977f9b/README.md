# systematic-review-workflow — 系统性文献综述

> 波尔产品周赛第4期 · research 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「系统性文献综述」的可调用 Skill（systematic-review-workflow）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装后由官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 执行系统性综述全流程并输出可复跑报告"
- 输入：`/input/case.json`（含 case_id、任务、材料位置、output_contract）+ 材料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  PICO/研究问题拆解 → 检索式：`{语料源, 查询式, 字段, 时间范围, 语言限制}`——全部留档（离线快照口径，声明非实时）。
-  题录轮：按标题/摘要判纳入潜力，逐条留理由；全文轮：对题录轮纳入者读全文判定，排除逐条给标准号+依据。
-  计数流：`识别 N → 去重 → 题录筛后 → 全文筛后 → 纳入`，首尾对账。
-  纳入研究按固定维度（设计/样本/对照/统计/偏倚）评级，判断锚定原文。
-  证据表：`{研究, 设计, 样本, 关键结果, 条件, 质量级}`——可比字段对齐。
-  综合结论：一致/部分一致/冲突逐主题给出；冲突并列双方数据。

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
