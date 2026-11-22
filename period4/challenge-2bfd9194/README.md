# library-file-manager — 科研资料库与文件管理

> 波尔产品周赛第4期 · library 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「科研资料库与文件管理」的可调用 Skill（library-file-manager）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装后由官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 组织科研资料库并生成可交接清单"
- 输入：`/input/case.json`（含 case_id、任务、材料位置、output_contract）+ 材料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  全文件清单：`{path, type, size, mtime, readable}`——对账基准（总数前后一致）。
-  按题目规则归入目标层级；每文件登记元数据：`{新路径, 类型, 项目/实验归属, 日期, 来源路径}`。
-  **版本关系**：同一材料的演进链（v1→v2→修订版→改名副本）按内容/时间/命名特征识别并链接，不按文件名猜。
-  重命名只做映射登记（原路径→新路径），可回溯。
-  交接清单（含分类统计）；索引（关键词→文件）；版本链图。
-  跳过（权限/损坏/未知类型）、失败、冲突（同名不同内容）逐条记录 + 恢复方式（从哪个底账找回）。

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
