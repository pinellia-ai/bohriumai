# citation-fact-verify-run — 引用与事实核验

> 波尔产品周赛第4期 · review 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「引用与事实核验」的可调用 Skill（citation-fact-verifier）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装后由官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 核验引用与事实并逐条给依据"
- 输入：`/input/case.json`（含 case_id、任务、材料位置、output_contract）+ 材料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  逐处引用：找被引文献的对应结论（材料内可及部分），比对稿件表述：
-  转引、跨页引用、摘要-正文不一致情形按规则处理（同 p3 证据核验规则）。
-  数值/事实陈述与给定材料对照：一致/不一致/来源缺失。
-  来源可靠性：引用的来源本身是否在可信清单内（材料提供）。
-  每条核验的证据定位回原文（文件/页/段）；定位失败的如实标注。
-  类型分级：事实错误 / 证据不足 / 规范问题 / 建议；needs_review 单列（材料外、无法访问）。

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

- v2（执行导向重写：真实工具链跑通+四件套/运行日志交付）；自查清单见 SKILL.md §6。
