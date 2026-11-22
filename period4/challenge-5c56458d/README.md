# db-query-analyzer — 科研数据库查询与分析

> 波尔产品周赛第4期 · analysis 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「科研数据库查询与分析」的可调用 Skill（db-query-analyzer）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装后由官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 查询科研数据库并做跨表分析（schema验证+留痕）"
- 输入：`/input/case.json`（含 case_id、任务、数据字典/材料、output_contract）+ 数据文件。
- 输出：`/app/output/`（数据/图/代码 + result.json，字段以 output_contract 为最高优先）。

## 3. 方法概述

-  连接测试（真实执行）；`SHOW TABLES / DESC` 输出留档；需求涉及的字段全部确认存在+类型。
-  每条查询：注释（目的/预期行数量级）；JOIN 显式条件；编码型字段（类别码）不当数值聚合；NULL 处理显式（IS NULL / COALESCE 按字典语义）。
-  分步小查询验证（先 COUNT 再取数），行数 sanity：join 后行数 vs 预期（膨胀即报漏连接条件）。
-  字段语义表：`{字段, 含义(数据字典), 单位, 口径注意}`——结果表每列带解释。
-  跨表分析：口径对齐（同指标跨表单位/定义差异显式处理）。
-  每个交付表关联原始查询（query_id）；失败查询逐条留痕：`{语句, 错误信息, 根因, 修复}`。

## 4. 契约速览

- case_id 原样；status ∈ success|partial|failed；保留原始值/规则/结果/代码与质量检查。
- 缺失、异常、无法解释如实说明；partial 时已完成部分完整可交；不编造。

## 5. 异常速查

| 情况 | 处置 |
|---|---|
| 数据/材料缺失 | status=failed 写明 |
| 无法解释的结果 | uncertainty 如实登记 |
| 预算不足 | 落盘 partial，gaps 列剩余 |
| contract 与本文件冲突 | 以 case.json output_contract 为准 |

## 6. 复用与版本

- v1（p4 首发）；自查清单见 SKILL.md §6。
