# reference-citation-manager — 写作04｜参考文献与引用管理

> 波尔产品周赛第4期 · writing 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「写作04｜参考文献与引用管理」的可调用 Skill（reference-citation-manager）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装后由官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 管理参考文献：位置审计、编号同步、去重核验"
- 输入：`/input/case.json`（含 case_id、任务、事实底稿、output_contract）+ 材料文件。
- 输出：`/app/output/`（稿件文件 + result.json，字段以 output_contract 为最高优先）。

## 3. 方法概述

-  每处引用检查：是否落在**真正需要来源支撑的论断句**上（不是段末凑数/图表注旁误挂）。
-  论断-引用匹配：引用文献是否支撑该句结论（supports | partial | related_only | contradicts）。
-  误挂/装饰性引用 → 建议移位或删除，理由登记。
-  插入/删除/调序后**全文重新编号**：正文编号、上标/方括号样式统一、交叉引用（如 "见[3]"）同步更新。
-  文末列表顺序与正文首次出现顺序一致；编号连续无跳号。
-  同一文多形态（中英题名/预印本 DOI vs 正式版）按标识符+题名规范化归并，保留**正式优先**版本并记录合并链。

## 4. 契约速览

- case_id 原样；status ∈ success|partial|failed；事实/数字/引用保留来源或修改记录。
- 材料不足与冲突显式标注；partial 时已完成部分完整可交；不编造。

## 5. 异常速查

| 情况 | 处置 |
|---|---|
| 底稿缺失/损坏 | status=failed 写明 |
| 约束冲突 | 以实际材料为准 + 登记 |
| 预算不足 | 落盘 partial，gaps 列剩余 |
| contract 与本文件冲突 | 以 case.json output_contract 为准 |

## 6. 复用与版本

- v1（p4 首发）；自查清单见 SKILL.md §6。
