# research-trend-analyzer — 研究前沿与趋势分析

> 波尔产品周赛第4期 · research 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「研究前沿与趋势分析」的可调用 Skill（research-trend-analyzer）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装后由官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 分析研究前沿与趋势（术语归一+证据链）"
- 输入：`/input/case.json`（含 case_id、任务、材料位置、output_contract）+ 材料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  按年份统计文献数（口径：快照内、按发表年字段）——抬升/回落标注数据点，不做外推预测。
-  主题词/概念按年份分布 → 演化事件：`{emergence 新出现 | merge 合并 | split 分裂 | decline 衰退}`，每个事件给判定依据（该主题词跨年出现频次变化+代表文献）。
-  **换词≠新兴**：同义术语合并后再看趋势（术语归一表先行）。
-  各阶段代表 = 该阶段主题的核心文献（按"被后续工作引用/方法被沿用"判定，依据在语料内的引用关系或内容证据），**不单看引用数**。
-  反复出现但无可靠答案的问题：跨年份多篇文献提出/讨论但均无定论——每条给文献链。
-  "没检索到"不构成空白：空白=语料内有相关讨论但缺解。

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
