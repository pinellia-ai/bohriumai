# product-arena-08-3027d350 · 阅读01｜文献文档解析（v1）

## 交付标准清单（自题面提取）

- output_contract 全字段逐字段落实 result.json（评测时以 /input/case.json 为最高优先），case_id 原样保留。
- 产物必须是结构化 JSON：**元数据/节/段/表/图五层** + 页码定位，不是纯文本堆砌。
- 四验收问题：提得全（页眉页脚剔除清单）、排得对（多栏 reading_order）、拆得清（表格 cells 结构+公式逐字保留）、核得回（page_no+block 锚点）。
- 每个解析结果指回原文页码、区块位置与解析依据；读不出的部分标 unresolved（带原因码），不猜补。
- 异常处置：加密/无文字层/图片型表格/乱码字体/页码错乱逐项有处理路径。
- 运行状态三态 + uncertainty_notes + change_log 如实登记。
- 资源限额：≤50 文件 / 单文件 ≤500KB / 总量 ≤2MB。

## 自测记录

- YAML frontmatter 可解析：name=scientific-pdf-parse-structured，通过。
- scripts/validate_result.py 语法校验（ast.parse）通过，并用最小示意 result.json 实跑退出码 0（五层+定位字段全检）。
- output_contract 覆盖：SKILL.md §4 基准全集（case_id/status/document五层/evidence_and_boundary/run_status/sources/uncertainty_notes/change_log），声明 case.json 优先。
- SKILL.md 行数约 160，含数字门槛（§5）、异常处理表（§6）、自查清单（§7）、最小示例（§9）。
- 文件数 3、总量 <2MB，通过。

## 版本说明

v1 初版：五层结构化 JSON 流水线（逐页提取→版面分类排序→章节层级→表格还原→图注公式参考文献→result.json 组装）+ 结构校验脚本。
