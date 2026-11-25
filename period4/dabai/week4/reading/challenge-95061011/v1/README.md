# README — challenge-95061011 多文档比较与整合 (v1)

## 交付标准清单（从题面提取）

- 接口（组织方修订 v2）：读 `/input/comparison-workorder.json` 与全部语料文档；建统一字段比较矩阵，每格带精确 `source_document_id` + `paragraph_id`；**定量合成前先做可比性判定**（task/metric/units/material/pollutant/budget）；保留全部不可比与未报告条件；不合并不同数据集或染料。
- 红线：单篇摘要不构成多文档比较；不合并不同数据集。
- 四关注：对得齐（同一字段定义）/ 填得准（值来自标注的那篇）/ 说得清（冲突归因到样本/方法/条件/指标）/ 查得回（逐格定位可复算）。
- 输出：`/app/output/result.json`，含 case_id、字段字典、矩阵、可比性、一致性+归因、证据卡片、整合报告、未报告清单、状态、不确定性、变更记录。

## 文件

- `SKILL.md` — 六步流水线（字段字典→逐篇抽取→两级对齐→一致性判定→证据卡片→校验落盘）
- `scripts/validate_matrix.py` — 行覆盖/格状态/quote 子串匹配/六项判定/冲突归因校验，带 `--selftest`

## 自测记录（2026-11-25）

- [x] YAML frontmatter 可解析
- [x] output_contract 全字段覆盖
- [x] validate_matrix.py ast.parse 通过；`--selftest` 实跑两文档合成示例（含 not_reported 格、可比性六项、partially_consistent 归因）0 error
- [x] 无虚构：不含题面外接口
- [x] 资源限额：4 文件 / <35KB
