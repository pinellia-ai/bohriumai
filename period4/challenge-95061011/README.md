# multi-doc-compare-matrix — 多文档比较与整合

> 波尔产品周赛第4期 · reading 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「多文档比较与整合」的可调用 Skill（multi-doc-compare-matrix）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装至评测环境后，官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 对多篇论文建立统一字段比较表并归因结论差异"
- 输入：`/input/case.json`（含 case_id、任务、材料位置、output_contract）+ 材料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  定义字段：`{field_id, name, 定义口径, 取值规则, 允许值/单位}`——先于抽取，全表共用。
-  同名不同口径的字段（如 accuracy 的宏/微平均）显式拆分或注明换算。
-  每格取值：`{paper_id, field_id, value, unit, dataset_version, condition, locator(页/段/表行), quote}`。
-  未报告 → "未报告"（不填 0）；口径不明 → 标 uncertain。
-  方法与条件对齐：数据集版本、样本量、划分方式、基线、评价口径归一 → 判定**可比子集**（哪些论文能直接比、哪些只能条件内比）。
-  不可比处显式标注，不强行同表硬比。

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
