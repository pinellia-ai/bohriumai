# systematic-review-screener — 系统性文献检索与纳排筛选

> 波尔产品周赛第4期 · search 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「系统性文献检索与纳排筛选」的可调用 Skill（systematic-review-screener）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装至评测环境 skill 目录后，官方 DeepSeek Harness 在 3 个固定案例上运行（64 请求/900秒/16384token），与基础 Agent 对照评分。离线语料口径：仅依据组织方快照，不声称实时检索与全球覆盖。

## 2. 快速调用

- 触发："请按本 Skill 执行系统性纳排筛选并输出可复跑流程报告"
- 输入：`/input/case.json`（含 case_id、任务、语料清单、output_contract）+ 语料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  固化协议：PICO 要素 → 纳入标准（Inclusion）与排除标准（Exclusion）逐条编号（I1/I2…、E1/E2…），每条标准写成可判定规则（什么样的记录满足/不满足）。
-  检索式与限定留档：库、字段、时间截止日、语料快照版本。
-  **标准版本化**：v1 定稿后才筛选；筛选中途改标准必须记录并重判受影响记录。
-  重复按标识符归并（规则编号留档）；PRISMA 式计数：`识别 → 去重后 → 筛选 → 纳入`，各环节条目数首尾对账。
-  每条记录对照 I/E 标准逐条判：`included | excluded(E1/E2…) | uncertain`。
-  依据 = 摘要/正文原文短句（不是标题词面）；excluded 必须指明触发哪条排除标准。

## 4. 契约速览

- case_id 原样；status ∈ success|partial|failed；每条结果带来源定位与原文短句。
- gaps/uncertainty_notes 诚实登记；status=partial 时已完成部分完整可交。
- 不编造记录/引用/状态/覆盖。

## 5. 异常速查

| 情况 | 处置 |
|---|---|
| 语料缺失/损坏 | status=failed |
| 子任务零命中/无数据 | 如实登记 + 已试策略列表 |
| 预算不足 | 落盘 partial，gaps 列剩余 |
| contract 与本文件冲突 | 以 case.json output_contract 为准 |

## 6. 复用与版本

- v1（p4 首发）；再跑按 SKILL.md §3 流程；自查清单见 SKILL.md §6。
