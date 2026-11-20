# auto-classifier-renamer — 文献与资料自动分类

> 波尔产品周赛第4期 · library 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「文献与资料自动分类」的可调用 Skill（auto-classifier-renamer）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装后由官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 批量分类文献资料并补齐元数据重命名"
- 输入：`/input/case.json`（含 case_id、任务、材料位置、output_contract）+ 材料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  每文件：`{type判定依据(内容/元数据特征), 目标层级}`——依据引用文件内证据（题名行/期刊名/DOI 前缀）。
-  无法判定（内容缺失/纯图片）：uncertain 组 + needs_human_review，不硬分。
-  从文件内容/文件名/路径抽取：标题、作者、年份、期刊、DOI；缺失字段标 null（不猜）。
-  预印本 vs 正式版：按 DOI 前缀/版本标记区分并链接。
-  规则化：`{年份}_{第一作者}_{标题缩写}_{类型}{版本}`；重命名=映射表登记（原→新），不实际删除/覆盖原文件。
-  重复下载（同内容多份）：按哈希/标识符识别，保留主份+dup 记录。

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
