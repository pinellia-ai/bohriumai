---
name: latex-build-check
description: |
  LaTeX 写作与编译 Skill：对给定 .tex 工程产出可编译骨架、修复编译错误并自查。
  核心机制：①结构正确性（环境配对/导言区/主子文件）②交叉引用闭合（\\ref↔\\label、
  \\cite↔bib 双向对账）③编译错误自查表（错误模式→根因→修复）④编译轮次与复现记录。
  交付可继续编辑的源码，不把 PDF 或片段当结果。
---

# LaTeX 写作与编译（可编译骨架 + 交叉引用闭合 + 错误自查表）

## 1. 用途与适用范围

- 适用：.tex 工程的写作、修复、模板适配与可重复构建。
- 方法主线：**先静态检查、再编译、再按自查表定位修复**，编译轮次固定可复现。
- 硬约束：改动保留原文意图；数值/符号不凭空补造；无法修复的如实标注。
- 不适用：纯排版审美调整（标 out_of_scope）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id` 原样、任务说明、工程路径、`output_contract` 全字段。
2. 读 `/input/task.md`（如有）：目标模板（期刊/会议/学位论文类文件）、TeX 发行版要求。
3. 盘点工程结构：主文件、子文件、.bib/.cls/.sty/.bst、图片资源；逐个真实读取。
4. 工程缺失或模板类文件缺失 → 落 `status=failed` result.json，不虚构模板行为。

## 3. 工作流程

### Step 1 可编译骨架确认
- 确认 `\documentclass` → 导言区（宏包加载顺序）→ `\begin{document}`/`\end{document}` 完整。
- 环境配对检查（scripts/latex_audit.py）：每个 `\begin{x}` 有对应 `\end{x}`，嵌套次序正确。
- 主子文件：`\input`/`\include` 引用的文件存在；`% !TEX root` 指向真实主文件。

### Step 2 交叉引用闭合检查（scripts/latex_audit.py）
- `\ref/\eqref/\autoref` 的每个 key 必须有 `\label{}`；反之未引用的 label 记 orphan_labels。
- `\cite/\citep/\citet` 的每个 key 必须在 .bib 或 `\bibitem` 中；bib 中未引用条目记 orphan_bib。
- 检查编号冲突：同一 key 重复 `\label` 报错。

### Step 3 编译（固定轮次）
- 默认轮次：`pdflatex main → bibtex main → pdflatex main → pdflatex main`（模板要求优先）。
- 每轮保存完整 .log；记录 TeX 发行版与版本（`tex --version`）、宏包版本（如可得）。
- 编译不可用（环境无 TeX）时：静态检查照常全跑，status 标 partial 并写明"未实际编译"。

### Step 4 编译错误自查表（按 log 逐条定位：文件+行号+根因）
| 错误模式 | 常见根因 | 修复策略 |
|---|---|---|
| `Undefined control sequence` | 命令拼错/宏包未加载 | 定位行，补 `\usepackage` 或改用已加载命令 |
| `Environment ... undefined` | 环境宏包缺失（如 algorithm） | 补加载对应宏包 |
| `Missing $ inserted` | 数学符号进了文本模式 | 补 `$...$` 或改转义 |
| `LaTeX Error: File ... not found` | 缺 .cls/.sty/.bib/图片 | 找工程内同名文件或补最小替代，记录依赖 |
| `Reference ... undefined` | label 未定义或轮次不足 | 先跑闭合检查；再补编译轮次 |
| `Citation ... undefined` | bib 缺条目/未跑 bibtex | 对账后补轮次；缺条目标 unverified 不编造 |
| `Runaway argument` | 花括号不平衡 | 定位行配对括号 |
| `Package babel Error`/字体缺失 | 缺字体或语言包 | 换可写字体，记录替代 |
| 报错级联（一条错误后大面积报错） | 只修首个根因，重编译再评估 | 不停在第一条错误信息上 |
| `Overfull \hbox` 超页宽 | 表格/公式溢出 | 调列宽/换行，禁止靠缩放掩盖 |

### Step 5 修复与验证闭环
- 每次修复 → 重新编译 → 确认该错误消失且未引入新错误（比对前后 log）。
- 每处修复记录：`{file, line, error_pattern, root_cause, fix}`。
- 交叉引用收敛判定：最后一轮 log 无 "Rerun to get cross-references right"。

### Step 6 复现记录
- 记录：TeX 发行版与版本、编译命令与轮次、宏包与字体依赖、模板版本。
- 他人按此记录应能得到同一产物；无法记录的项标 unverified。

## 4. 输出契约（/app/output/result.json）

以 case.json 的 `output_contract` 为准，本 skill 保证：

```json
{
  "case_id": "原样保留",
  "status": "complete | partial | failed",
  "tex_artifacts": ["交付的 .tex/.bib 文件相对路径"],
  "compile": {"engine": "pdflatex", "rounds": ["pdflatex","bibtex","pdflatex","pdflatex"],
               "exit_code": 0, "log_digest": "", "tex_distribution": "", "converged": true},
  "audit": {"unmatched_env": [], "dangling_refs": [], "orphan_labels": [],
             "dangling_cites": [], "orphan_bib": [], "duplicate_labels": []},
  "fixes": [{"file":"","line":0,"error_pattern":"","root_cause":"","fix":""}],
  "reproduction": {"engine_version":"","packages":"","fonts":"","command":""},
  "sources": [{"change":"","evidence":"原文/模板位置"}],
  "unverified": [{"item":"","reason":""}], "uncertainty": ""
}
```

### 触发与调用方式
- 触发条件：任务涉及 .tex 写作/修复/编译/模板适配/交叉引用。
- 调用：读 case.json → Step1 骨架确认 → Step2 交叉引用闭合（脚本实跑）→ Step3 编译（固定轮次）→ Step4-5 按自查表修复闭环 → Step6 复现记录 → result.json 落 /app/output。
- 脚本调用：`python3 scripts/latex_audit.py main.tex [refs.bib ...]`，输出 JSON 审计报告，问题存在退出码 1；报告写入 result.json 的 audit 字段。

### 编译轮次与收敛约定
- 默认：`pdflatex → bibtex → pdflatex → pdflatex`；使用 latexmk 的模板按 `.latexmkrc` 执行。
- 收敛判定：最后一轮 log 无 "Rerun to get cross-references right" 且无 "Citation ... undefined"。
- 每轮 log 保存到 /app/work/logs/round<N>.log，供修复前后比对，证明未引入新错误。
- log 摘要提取：错误行（`!` 开头）、未定义引用行、Overfull 超过 10pt 的行，写入 compile.log_digest。

## 5. 数字门槛

- 静态审计五项（环境配对/ref 闭合/cite 闭合/重复 label/主文件结构）必须全跑，脚本结果写入 result.json。
- 编译成功（exit 0）且引用收敛（converged=true）才可标 complete；仅静态通过未编译的最多 partial。
- 每处修复有 file+line+root_cause；报错不级联（修根因，不停在首条错误）。
- 交付物为可编辑源码（.tex/.bib），非 PDF/截图/片段。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 缺宏包且无法安装 | 用工程内替代或最小重写该处，记录于 unverified |
| 模板 .cls 缺失 | 不伪造模板行为；改用最接近的可用 class 并显式声明差异 |
| 编译环境无 TeX | 静态检查全跑，status=partial，注明未实际编译 |
| 报错级联 | 逐轮修复首个根因后重编译，禁止一次大改 |
| 缺字体 | 换可写字体并记录；不静默替换导致版式漂移 |
| .bib 缺条目 | 标 unverified，不编造条目 |
| 权限不足 | 记录具体路径与原因 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 字段全覆盖
- [ ] latex_audit.py 实跑，五项审计结果进 result.json
- [ ] 编译轮次固定且记录；引用收敛
- [ ] 每处修复有 file+line+root_cause+fix
- [ ] 交付物为可编辑源码；模板必填项逐项覆盖
- [ ] 复现记录完整；无法确认项全部标注

## 8. 效率约束

预算 64 请求 / 900 秒。先落最小 result.json（audit+tex_artifacts），再跑编译与修复闭环。
≤50 文件、≤2MB、脚本仅标准库。

## 9. 最小示例（示意输出，非正式案例结果）

输入 main.tex 含 `\ref{sec:method}` 但无对应 `\label`，且 `\begin{itemize}` 未闭合：
```json
{"audit": {"unmatched_env": ["itemize @ L14 begin-only"],
           "dangling_refs": ["sec:method @ L22"],
           "orphan_labels": [], "dangling_cites": [], "orphan_bib": []}}
```
对应自查表行：`Undefined references → label 未定义或轮次不足 → 补 \label{sec:method} 并重编译`。
### 最小 result.json 完整示意（示意，非正式案例结果）
```json
{"case_id": "示例占位", "status": "complete",
 "tex_artifacts": ["main.tex", "refs.bib"],
 "compile": {"engine": "pdflatex", "rounds": ["pdflatex", "bibtex", "pdflatex", "pdflatex"],
   "exit_code": 0, "log_digest": "0 errors, 2 warnings (Overfull 12pt L45)",
   "tex_distribution": "TeX Live 2023", "converged": true},
 "audit": {"unmatched_env": [], "dangling_refs": ["sec:m @ L22"], "orphan_labels": [],
   "dangling_cites": [], "orphan_bib": ["unused1"], "duplicate_labels": []},
 "fixes": [{"file": "main.tex", "line": 22, "error_pattern": "Undefined references",
   "root_cause": "label 未定义", "fix": "在 §3 首行补 \\label{sec:m}"}],
 "reproduction": {"engine_version": "pdfTeX 1.40.25", "packages": "graphicx, booktabs",
   "fonts": "Times", "command": "pdflatex main && bibtex main && pdflatex main && pdflatex main"},
 "sources": [{"change": "表格改 booktabs 三线表", "evidence": "模板示例第3节"}],
 "unverified": [{"item": "orphan_bib: unused1", "reason": "未引用条目，保留待作者决定"}],
 "uncertainty": ""}
```
