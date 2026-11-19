# literature-review-generator — 文献综述生成

> 波尔产品周赛第4期 · research 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「文献综述生成」的可调用 Skill（literature-review-generator）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装后由官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 生成句句可回链的文献综述"
- 输入：`/input/case.json`（含 case_id、任务、材料位置、output_contract）+ 材料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  读纳入文献 → 按研究问题/方法/发现聚类主题：`{theme_id, 名称, 成员文献, 归并依据}`。
-  主题数量与边界由**文献实际分布**决定，模板框架（背景/方法/挑战/展望）不硬套。
-  每主题证据表：`{theme_id, 文献, 结论要点, 适用条件, 强度, locator(章节/页)}`。
-  反面证据与分歧专门登记（不混入主线），综述正文必须呈现。
-  每个论断句带引用且引用确实支撑该句：写前先定证据，禁止"句子通顺引文随便挂"。
-  层次：主题内综合 → 主题间关系 → 整体图景与分歧。

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
