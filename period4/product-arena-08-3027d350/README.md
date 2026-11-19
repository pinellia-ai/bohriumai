# pdf-structured-parser — 阅读01｜文献文档解析

> 波尔产品周赛第4期 · reading 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「阅读01｜文献文档解析」的可调用 Skill（pdf-structured-parser）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装至评测环境后，官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 结构化解析给定 PDF：版面顺序、章节表格公式"
- 输入：`/input/case.json`（含 case_id、任务、材料位置、output_contract）+ 材料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  识别栏结构（单/双/多栏）、页眉页脚区域、题注区、正文区边界（按页记录）。
-  阅读顺序重建：双栏先左栏后右栏；跨栏标题/图表按版面位置插入流。
-  正文流：段落编号连续，**不漏行不丢段**；页眉页脚/行号/水印剔除并记录剔除规则。
-  图表题注、脚注、参考文献单独分区提取（与正文分开标注）。
-  特殊字符与希腊字母、上下标保真（Unicode 表示，不丢字母）。
-  章节层级树：编号+标题+层级，与正文段落挂接。

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
