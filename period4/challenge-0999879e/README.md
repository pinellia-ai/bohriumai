# paper-quality-auditor — 论文质量审查

> 波尔产品周赛第4期 · review 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「论文质量审查」的可调用 Skill（paper-quality-auditor）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装后由官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 出论文质量审查问题单"
- 输入：`/input/case.json`（含 case_id、任务、材料位置、output_contract）+ 材料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  章节要素齐备（摘要/方法/结果/讨论/限制/声明）；图表与正文引用互查；承诺-交付对照（引言说要做的在结果出现）。
-  正文数值 ↔ 表格/图；摘要结论 ↔ 结果正文；方法描述 ↔ 材料步骤——不一致逐条定位。
-  论断-证据清单：无证据论断、引用不支持所引句、缺对照/样本量说明、统计量缺失、论证链断裂点。
-  每条问题：`{issue_id, 位置(段/句), 类型: factual_error | insufficient_evidence | normative | suggestion, severity: major | minor, 依据(原文引用), 建议修改}`。
-  无法确认（材料外事实）→ needs_review，不凭空补结论。

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
