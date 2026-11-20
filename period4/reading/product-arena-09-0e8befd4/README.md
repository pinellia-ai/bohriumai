# nanopub-assertion-builder — 阅读14｜Nanopublication

> 波尔产品周赛第4期 · reading 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「阅读14｜Nanopublication」的可调用 Skill（nanopub-assertion-builder）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装至评测环境后，官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 把结论拆成原子断言并绑定证据生成 nanopub"
- 输入：`/input/case.json`（含 case_id、任务、材料位置、output_contract）+ 材料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  每段结论 → 原子断言清单：`{assertion_id, text(独立可判真假), assertion_type(fact | comparison | causal | scope), 原文限定词保留}`。
-  拆分原则：不遗漏（复合句全拆）、不重复、每条不含多个可独立判断的命题。
-  每条断言找**最小充分证据**：`{quote(逐字), locator(页/段/句/表), 支持程度(supports | partial | insufficient)}`。
-  主题相关≠支持；无证据断言标 unsupported_evidence（不是删除——诚实暴露）。
-  每条 nanopub：`{assertion → evidence → paper(题名/作者/年份/版本/DOI) → 原文位置}` 全链可走通。
-  版本信息（预印本/正式版）如实登记。

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
