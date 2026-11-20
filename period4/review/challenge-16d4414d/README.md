# argument-logic-reviewer — 论文逻辑与论证审查

> 波尔产品周赛第4期 · review 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「论文逻辑与论证审查」的可调用 Skill（argument-logic-reviewer）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装后由官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 审查论证断裂并给修改方向"
- 输入：`/input/case.json`（含 case_id、任务、材料位置、output_contract）+ 材料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  逐段抽取论断（主张+强度词）与证据（数据/图表/文献）——断裂检测的基础。
-  强度越界：结论句 vs 数据支撑范围（样本/条件/显著性）。
-  引用错配：所引文献内容 vs 被支撑句。
-  方法-问题错配：研究问题需要因果/比较，方法只能给相关/描述。
-  口径反向：统计口径与结论描述方向矛盾。
-  承诺缺口：三清单交叉（承诺∧未交付；交付∧未讨论）。

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
