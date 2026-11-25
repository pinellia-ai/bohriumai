# product-arena-10-760d1a0b · 阅读15｜文献知识图谱构建（v1）

## 交付标准清单（自题面提取）

- output_contract 全字段逐字段落实 result.json（评测时以 /input/case.json 为最高优先），case_id 原样保留。
- **schema 先行**并随产物交付；三元组 100% 带 evidence_span + source_ref + strength（direct/indirect/inferred）。
- 实体对应论文真实出现的对象（mention_verbatim 子串校验，脚本防常识补全）；区分作者自述与转述。
- 实体对齐：合并有 basis，同名不同对象不合并（conflicts 清单），不强迫合并。
- 多文档输入：corpus-manifest 划分 doc_id，根元数据不套到第二篇；跨篇不错并条件/样本/数值。
- 共现/推测不建边；关系证据冲突建两条边各带证据并登记，不裁决。
- ≥3 个真实执行查询，结果回溯 triple_id，无结果如实 empty。
- not_found/冲突如实登记；资源限额 ≤50 文件 / 2MB。

## 自测记录

- YAML frontmatter 可解析：name=literature-kg-evidence-graph，通过。
- scripts/verify_graph.py 语法（ast.parse）通过；`--selftest` 实跑通过：1 条合法三元组通过校验，1 条伪造 evidence_span + direct 边缺 self_reported 被正确捕获。
- output_contract 覆盖：SKILL.md §4 基准全集（case_id/status/graph/queries/evidence_and_boundary/run_status/sources/uncertainty_notes/change_log），声明 case.json 优先。
- SKILL.md 约 190 行，含数字门槛（§5）、异常处理表（§6）、自查清单（§7）、最小示例（§9）。
- 文件数 3、总量 <2MB，通过。

## 版本说明

v1 初版：schema 先行 + 证据绑定抽取流水线（schema→实体抽取→对齐→三元组→查询→result.json）+ 证据核验脚本（原文子串匹配 + direct 边约束）。
