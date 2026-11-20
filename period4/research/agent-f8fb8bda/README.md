# deep-research-workflow — 深度研究 Agent

> 波尔产品周赛第4期 · research 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「深度研究 Agent」的可调用 Skill（deep-research-workflow）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装后由官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 执行多步深度研究流程并留痕可恢复"
- 输入：`/input/case.json`（含 case_id、任务、材料位置、output_contract）+ 材料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  研究任务 → 子问题 DAG：`{subq_id, 依赖, 检索策略, 预期产出}`——计划先行落盘，后续执行对照。
-  每步：`{step_id, action(检索/解析/计算), inputs, outputs(文件/记录), status}`。
-  工具调用失败：重试一次 → 仍失败则标注 failed_step + 依赖该步的子问题降级为"无法确定"，**不编造该步结果**。
-  证据表：`{evidence_id, subq_id, 内容要点, 来源定位, 可比字段}`——跨材料对齐可比字段。
-  结论分层：`material_fact`（材料直接陈述）/ `inference`（合理推断+推断链）/ `undetermined`（材料不足）。
-  每条结论带 evidence_ids；冲突证据并列不抹平。

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
