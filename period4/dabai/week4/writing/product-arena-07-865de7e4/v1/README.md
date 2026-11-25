# README — product-arena-07-865de7e4 LaTeX 写作与编译 v1

## 交付标准清单（自题面提取）

1. `result.json` 落 `/app/output`：output_contract 全字段 + `case_id` 原样。
2. 目标产物：可编译、可继续编辑、可维护的 .tex/.bib 源码（非 PDF/截图/片段）。
3. 事实与来源映射：源码改动、编译过程与产物可独立复核；每处修复有 file+line+root_cause。
4. 版本与边界：无法确认项（缺模板/缺字体/未编译）显式标注，partial 说明边界。
5. 题面四重点应对（前人弱项 61.3，加重交付）：
   - 编译得通 → 固定编译轮次 + 引用收敛判定 + 报错级联处理（修根因不停在首条错误）。
   - 改得对 → latex_audit.py 五项静态审计（环境配对/ref↔label/cite↔bib/重复label/主文件结构）。
   - 交得可用 → 交付源码 + 修复记录表。
   - 复现得了 → reproduction 记录：TeX 发行版、宏包字体依赖、命令与轮次。
6. 10 行编译错误自查表（错误模式→根因→修复策略）写入 SKILL.md。
7. 不编造 bib 条目与模板行为；≤50 文件 / 2MB；预算 64 请求 / 900 秒。

## 文件清单

- SKILL.md：六步流水线（骨架确认→交叉引用闭合→编译→错误自查表→修复闭环→复现记录）。
- scripts/latex_audit.py：静态审计脚本——环境配对（含嵌套错误）、\ref/\label 与
  \cite/bib 双向闭合、重复 label、主文件结构检查；自动展开 \input/\include、剔除注释；
  问题存在退出码 1。

## 自测记录（2026-11-25）

- YAML frontmatter 解析：通过。
- output_contract 字段覆盖：契约含 case_id/status/tex_artifacts/compile/audit/fixes/reproduction/sources/unverified/uncertainty，覆盖题面四重点。
- 脚本语法：ast.parse 通过。
- 脚本实跑（构造最小工程）：
  - 病例 main.tex：itemize 未闭合 + `\ref{sec:m}` 无 label + `\cite{foo}` bib 无此条目 +
    bib 中 orphan 条目 → 五类问题全部正确报出，退出码 1；
  - 修复后重跑 → 环境/ref/cite 三类告警清零，仅剩 bib 中真实未引用条目 unused 被正确报为
    orphan_bib（属预期审计功能），剔除后 ok=true 退出码 0；
  - 注释行中的伪命令与 \input 子文件展开均验证有效。
- 资源限额：3 文件约 16KB。
- 无虚构：示例为构造输入并标注示意。
