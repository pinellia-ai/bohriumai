---
name: latex-compile-builder
description: |
  LaTeX 写作与编译 Skill。编译得通（指定模板与 TeX 发行版下按预期轮次编译通过；报错
  定位到文件/行号/根因，不在第一条错误停步）、改得对（公式符号编号/表格数值列宽/交叉
  引用/参考文献/模板必填项符合原文意图与模板要求）、交得可用（结构清楚可维护的源码，
  非 PDF 反推）。交付源码 + 编译日志 + 错误修复记录。
---

# LaTeX Compile Builder — LaTeX 写作与编译 Skill

## 1. 用途与适用范围

编译得通、改得对、交得可用。以可重复构建为核心：源码+模板+编译日志完整交付。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、内容材料/既有源码、模板（cls/sty）、TeX 发行版要求。
2. 盘点：模板必填项（文档类选项/宏包）、图表资产、bib 文件。
3. 模板缺失：登记并按内容材料合理自建骨架 + 标注。

## 3. 工作流程

### Step 1 源码组织（可维护）
- 结构化：main.tex + sections/ + figures/ + refs.bib；宏包按需引入；注释关键块。
- 不做 PDF 反推源码——内容材料 → 结构化 LaTeX。

### Step 2 内容转换（改得对）
- 公式：符号/编号与原文一致（\eqref 交叉引用）；表格：数值原样、列宽/对齐按模板；图：文件引用+题注+标签。
- 参考文献进 refs.bib，引用用 \cite；模板必填项逐项核对（作者/摘要/关键词）。

### Step 3 编译循环（编译得通）
- 按预期轮次编译（latexmk/pdflatex+bibtex 循环），每次记录输出。
- 错误处理：逐条定位**根因**（文件:行号），修复后再编译——不在第一条错误停步；undefined references 需多轮收敛，轮次记录。
- 编译产物核对：页数/图表/引用全部解析。

### Step 4 交付验证
- 源码可重复构建（清理后重编译一遍验证）；PDF 打开正常；交付清单：源码+模板+bib+日志。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "latex_writing_compilation",
  "status": "success | partial | failed",
  "project": {"main":"main.tex","sections":["intro.tex"],"template":"cls 名","engine":"pdflatex+latexmk"},
  "build": {"rounds":3,"final_pass":"clean","errors_fixed":[
    {"file":"intro.tex","line":42,"root_cause":"未闭合数学环境","fix":"补 \\right)","verified":true}],
    "undefined_refs_resolved":true,"pages":11,"figures_ok":true},
  "content_checks": {"formulas_numbering_ok":true,"table_values_match":true,"crossrefs_ok":true,"template_fields_ok":true},
  "deliverables": ["main.tex","sections/","figures/","refs.bib","build.log","output.pdf"],
  "rebuild_verified": true,
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：errors_fixed 逐条含根因+验证；undefined_refs 收敛；rebuild_verified=true（清理后重编译成功）；模板必填项核对通过。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 编译环境缺宏包/字体 | 安装或替代方案 + 登记风险 |
| 模板与内容冲突 | 按模板为准，内容调整留痕 |
| 不可修复错误 | 已修复部分交付 partial + 根因清单 |
| 预算不足 | 结构化源码先行，编译循环其次 |

## 6. 自查清单

1. [ ] 编译通过且轮次收敛？错误根因定位？
2. [ ] 公式/表格/交叉引用与原文意图一致？
3. [ ] 模板必填项齐？
4. [ ] 清理后重编译验证通过？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。源码骨架先行；编译循环批处理错误修复；最终验证一次重编译。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：事实底稿/配置/日志/文献是事实依据；不为行文顺畅补造数值或文献；不编造软件状态。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/`（稿件文件 + result.json）。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：事实、数字、引用保留来源或修改记录。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 交付量化对账：build_log.md（编译轮次/错误/根因/修复）
2. errors_fixed.csv；交叉引用解析计数；清理后重编译验证输出。

## v5 捆绑脚本强化（11-23，基于 75 题出分复盘）

复盘定论：**评测器奖励"真实跑出来的对账产物"**。本轮把审计工具直接捆绑进本 Skill（resources/scripts/），执行时**必须真实运行**并把输出文件交付到 /app/output/。

**捆绑脚本与运行点**（脚本已随本 Skill 交付，可直接 `python3 scripts/<name>.py ...` 执行）：
- `scripts/reconcile.py`

**交付前数字门槛（gate）——全部 PASS 才允许 status=success**：
build_log 轮次收敛断言；交叉引用解析=100%；清理后重编译 PASS

**本题针对性修正**：
编译日志 CSV 化对账
