# README — product-arena-05-64faa4a2 方法与实验章节写作 v1

## 交付标准清单（自题面提取）

1. `result.json` 落 `/app/output`：output_contract 全字段 + `case_id` 原样。
2. 目标产物：可执行的方法与实验章节成稿，覆盖六类要素：步骤、实验设置、参数、数据集、对照、复现与限制。
3. 事实与来源映射：步骤/参数/数据集版本/训练评测条件可追溯到配置、日志、代码等具体材料位置。
4. 版本与边界：缺口与人工确认项（author_queries 追问清单）可复核。
5. 题面四重点应对：
   - 写得全 → 可复现四表（材料/步骤/参数/质控）覆盖六类要素。
   - 写得准 → param_trace.py 正文数值溯源，无来源数值不入正文。
   - 做得着 → 复现清单五要件（代码/环境/种子/数据/命令）。
   - 说得住 → 缺口显式标出 + 限制条件落到具体失效场景。
6. 不编造数据与版本号；≤50 文件 / 2MB；预算 64 请求 / 900 秒。

## 文件清单

- SKILL.md：六步流水线（要素抽取→四表→数值对齐→成稿→复现清单→缺口追问）。
- scripts/param_trace.py：正文数字溯源校验 + 参数表来源完整性检查，退出码语义明确。

## 自测记录（2026-11-25）

- YAML frontmatter 解析：通过。
- output_contract 字段覆盖：契约含 case_id/status/chapter_text/四表/param_trace/reproduction_checklist/author_queries/sources/unverified/uncertainty，覆盖题面六类要素。
- 脚本语法：ast.parse 通过。
- 脚本实跑：
  - 合法样例（chapter_text 含 "batch size 256"、parameter_table 含 value 256）→ ok=true；
  - 缺陷样例（正文出现 256 但表中无、参数行无 source）→ unmatched 与错误均正确报出，退出码 1；
  - 年份（2020）正确排除，不误报。
- 资源限额：3 文件约 15KB。
- 无虚构：示例为构造输入并标注示意。
