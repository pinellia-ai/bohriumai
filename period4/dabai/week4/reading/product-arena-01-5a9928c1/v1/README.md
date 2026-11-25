# product-arena-01-5a9928c1 · 阅读03｜文献翻译（v1）

## 交付标准清单（自题面提取）

- output_contract 全字段逐字段落实 result.json（评测时以 /input/case.json 为最高优先），case_id 原样保留。
- **术语锁定**：术语表先抽取后翻译，全篇唯一译名；新术语先补表再使用；脚本校验无同术语多译名。
- **逐段号对照**：段号与原文一一对应（段落守恒：translated + untranslated(reason) = total），跨页续段合并显式标注。
- **数字保真**：数值/百分比/单位逐字保留，脚本核验缺失即 FAIL；引用标记/图表编号计数原文=译文。
- 每段带译法依据（translation_notes）；译不准处标 issue+note 不含混处理。
- 异常处置：扫描件 OCR 标 partial、图片公式标 untranslated、参考文献无法解析整段标注，不虚构。
- 资源限额：≤50 文件 / 2MB。

## 自测记录

- YAML frontmatter 可解析：name=lit-translate-terminology-locked，通过。
- scripts/fidelity_check.py 语法（ast.parse）通过；`--selftest` 实跑通过：数字保真（92%/350 °C 均在译文）与引用计数（Figure 2 src=tgt=1）通过；故意丢弃数字的负例被正确捕获。
- output_contract 覆盖：SKILL.md §4 基准全集（case_id/status/translation/terminology/fidelity/evidence_and_boundary/run_status/sources/uncertainty_notes/change_log），声明 case.json 优先。
- SKILL.md 约 190 行，含数字门槛（§5）、异常处理表（§6）、自查清单（§7）、最小示例（§9）。
- 文件数 3、总量 <2MB，通过。

## 版本说明

v1 初版：切分编号→术语锁定→逐段翻译（保真纪律）→脚本三重核验（数字/术语/引用）→result.json，附 fidelity_check.py。
