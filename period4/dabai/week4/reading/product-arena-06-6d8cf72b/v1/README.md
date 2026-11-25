# product-arena-06-6d8cf72b · 阅读10｜文献总结与结构化笔记（v1）

## 交付标准清单（自题面提取）

- output_contract 全字段逐字段落实 result.json（评测时以 /input/case.json 为最高优先），case_id 原样保留。
- **章节对齐**：按论文自身章节提炼（purpose/content/result/transition 承接关系），禁止合并多节成通篇摘要模板。
- **论文卡片字段化**：research_question/data/methods+条件/findings/limitations/conclusions 六字段一项一源带锚点；方法条件不省略；原文无 limitations 标 not_found 不编造。
- **锚点回链**：每条关键笔记带 anchor（section_id+para_id+page_no）+ support_span，脚本校验子串匹配与节存在性。
- **知识点可检索**：JSONL 条目，缩写/同义归并有 basis，无重复无矛盾。
- 异常处置：扫描件/双栏错序/图表公式缺失/超长文/无编号章节逐项有路径。
- 资源限额：≤50 文件 / 2MB。

## 自测记录

- YAML frontmatter 可解析：name=structured-paper-notes-anchor，通过。
- scripts/verify_notes.py 语法（ast.parse）通过；`--selftest` 实跑通过：1 条合法笔记（span 在原文+anchor 节存在）通过，1 条伪造 span+无效 section 被正确捕获 2 个问题。
- output_contract 覆盖：SKILL.md §4 基准全集（case_id/status/notes/anchors/evidence_and_boundary/run_status/sources/uncertainty_notes/change_log），声明 case.json 优先。
- SKILL.md 约 190 行，含数字门槛（§5）、异常处理表（§6）、自查清单（§7）、最小示例（§9）。
- 文件数 3、总量 <2MB，通过。

## 版本说明

v1 初版：章节切分→论文卡片→章节摘要（承接关系）→知识点条目与锚点校验→result.json，附 verify_notes.py。
