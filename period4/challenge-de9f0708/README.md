# compliance-checker — 学术规范与合规检查

> 波尔产品周赛第4期 · review 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「学术规范与合规检查」的可调用 Skill（compliance-checker）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装后由官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 逐项检查学术规范合规并出问题单"
- 输入：`/input/case.json`（含 case_id、任务、材料位置、output_contract）+ 材料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  **引用合规**：逐条引用可追溯、格式与目标要求一致、无虚构（对照文献库）。
-  **方法统计透明**：方法可复算要素齐（对照 methods 清单）、统计量报告齐。
-  **受限数据**：涉及人类/隐私数据的声明（伦理批号/知情同意）有无；个人信息暴露点。
-  **图片与代码授权**：图片来源标注、代码/数据可用性声明与许可。
-  **投稿要求**：目标期刊/会议的格式必查项逐条核对（字数/图表数/声明字段）。
-  每条问题必须引用具体位置与规则条目；风格差异/学科惯例（如不同领域的引用风格）→ 记入 notes 不计问题。

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
