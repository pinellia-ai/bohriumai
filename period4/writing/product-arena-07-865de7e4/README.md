# latex-compile-builder — 写作13｜LaTeX 写作与编译

> 波尔产品周赛第4期 · writing 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「写作13｜LaTeX 写作与编译」的可调用 Skill（latex-compile-builder）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装后由官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 生成 LaTeX 源码并编译到零错误交付"
- 输入：`/input/case.json`（含 case_id、任务、事实底稿、output_contract）+ 材料文件。
- 输出：`/app/output/`（稿件文件 + result.json，字段以 output_contract 为最高优先）。

## 3. 方法概述

-  结构化：main.tex + sections/ + figures/ + refs.bib；宏包按需引入；注释关键块。
-  不做 PDF 反推源码——内容材料 → 结构化 LaTeX。
-  公式：符号/编号与原文一致（\eqref 交叉引用）；表格：数值原样、列宽/对齐按模板；图：文件引用+题注+标签。
-  参考文献进 refs.bib，引用用 \cite；模板必填项逐项核对（作者/摘要/关键词）。
-  按预期轮次编译（latexmk/pdflatex+bibtex 循环），每次记录输出。
-  错误处理：逐条定位**根因**（文件:行号），修复后再编译——不在第一条错误停步；undefined references 需多轮收敛，轮次记录。

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
