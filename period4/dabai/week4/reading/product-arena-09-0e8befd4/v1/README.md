# product-arena-09-0e8befd4 · 阅读14｜Nanopublication（v1）

## 交付标准清单（自题面提取）

- output_contract 全字段逐字段落实 result.json（评测时以 /input/case.json 为最高优先），case_id 原样保留。
- **四部分结构校验**：Head / Assertion / Provenance / PublicationInfo 每条 nanopub 齐备（脚本校验）。
- **断言溯源**：Provenance 链完整（断言→证据片段+位置→论文标题/作者/年份/DOI）；元数据缺失填 null + not_found，不编造。
- 拆解规则 R1-R4：单一性、条件保留、忠实性、粒度；整段话塞一个字段=违反。
- 证据最小充分判据 + 原文子串匹配（脚本核验）；derived 拼接登记说明。
- 找不到支撑的断言保留并标 unsupported，不删除不编造。
- 异常处置：扫描件/跨图表证据/断言证据冲突/元数据缺失逐项有路径。
- 资源限额：≤50 文件 / 2MB。

## 自测记录

- YAML frontmatter 可解析：name=nanopub-assertion-extractor，通过。
- scripts/verify_assertions.py 语法（ast.parse）通过；`--selftest` 实跑通过：1 条合法 nanopub（四部分齐+证据子串匹配）通过校验，1 条缺 Assertion 字段/Provenance 字段/证据不在语料的被正确捕获。
- output_contract 覆盖：SKILL.md §4 基准全集（case_id/status/nanopublications/assertions_summary/evidence_and_boundary/run_status/sources/uncertainty_notes/change_log），声明 case.json 优先。
- SKILL.md 约 190 行，含数字门槛（§5）、异常处理表（§6）、自查清单（§7）、最小示例（§9）。
- 文件数 3、总量 <2MB，通过。

## 版本说明

v1 初版：段落定位→断言拆解（R1-R4 规则）→证据绑定（最小充分+子串核验）→四部分组装→result.json，附结构校验脚本。
