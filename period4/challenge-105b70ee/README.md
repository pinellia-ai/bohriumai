# conclusion-data-extractor — 文献结论与数据提取

> 波尔产品周赛第4期 · reading 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「文献结论与数据提取」的可调用 Skill（conclusion-data-extractor）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装至评测环境后，官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 按统一字段表抽取论文结论与数据并绑定条件与定位"
- 输入：`/input/case.json`（含 case_id、任务、材料位置、output_contract）+ 材料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  从摘要/结果/讨论抽取结论并分级：`explicit`（作者明确结论）/ `limitation`（作者自述限制）/ `speculative`（"可能/提示/有望"类推测表述）。
-  **推测不得改写成确定事实**——保留原文限定词，speculative 结论的 claim_text 必须含原限定语。
-  每个数值绑定成立条件：样本（n/人群/材料）、实验设置、数据来源、时间点、比较基线。
-  条件不明的数值标 condition_unknown，不默认填常见条件。
-  逐值保留：数值、单位、误差（±SD/SEM/CI 按原文）、显著性（p 值/标记）、范围值保留区间形式。
-  跨页表格、合并单元格：按单元格归属还原行列关系；"未报告"/"—"如实记录。

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
