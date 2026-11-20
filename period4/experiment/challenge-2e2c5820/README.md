# feasibility-assessor — 实验方案可行性评估

> 波尔产品周赛第4期 · experiment 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「实验方案可行性评估」的可调用 Skill（feasibility-assessor）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装后由官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 评估实验方案可开工性（七类约束逐条核对）"
- 输入：`/input/case.json`（含 case_id、任务、数据字典/材料、output_contract）+ 数据文件。
- 输出：`/app/output/`（数据/图/代码 + result.json，字段以 output_contract 为最高优先）。

## 3. 方法概述

-  方案逐步骤抽：`{需要什么, 数量/规格, 何时需要, 依赖哪步}`。
-  每条需求 vs 约束文档：`{constraint_id, 需求, 供给(文档+位置), 状态: satisfied | gap | unknown}`。
-  具体核对：设备型号匹配？货期 vs 需要日期？样本量 vs 来源量？容差有 SOP 依据？
-  动物/人体样本 → 审批状态核对（审批表单）；安全边界（危化品/生物安全等级）与 SOP 对照。
-  审批缺失 = 硬性阻断项（不改判"可以开工"）。
-  `可开工 | 有条件开工（列缺口+补齐路径） | 暂缓（硬阻断项）`；每条 gap 给补齐动作与责任人建议。

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
