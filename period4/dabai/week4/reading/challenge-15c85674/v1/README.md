# README — challenge-15c85674 文献智能问答 (v1)

## 交付标准清单（从题面提取）

- 输入标识：`case_id`、`paper_id`、`material_version` 与本次输入一致。
- 逐题回答：`answers[]` 每个问题一项，含 `question_id`、`answer`、`conditions[]`；不得省略无法回答的问题。
- 回答状态四态：`answered` / `partial` / `insufficient_evidence` / `input_error`。
- 论断与证据：`claims[]` 含 `claim_id`、`text`、`kind`（`reported`/`inferred`）、`evidence[]`（`paragraph_id` + 逐字短引文 `quote`）。
- 未完成部分：`unanswered_parts[]` 列明未答部分及原因，没有则空列表。
- 阅读范围：`coverage` 说明已读/未读章节及原因。
- 输出路径：`/app/output/result.json`（题面修订：主产物路径适配，原答案字段与完整原文保留）。
- 边界：仅依据给定材料；不做 PDF 解析/图像识别/联网检索；"材料未报告"也是有依据的有效回答。

## 文件

- `SKILL.md` — 五步流水线（段落索引→逐题证据检索→回答与论断绑定→状态与缺口→校验落盘）
- `scripts/validate_answers.py` — 标识一致性/问题覆盖/枚举/quote 子串匹配校验，带 `--selftest`

## 自测记录（2026-11-25）

- [x] YAML frontmatter 可解析
- [x] output_contract 全字段覆盖（上表逐项对照题面）
- [x] validate_answers.py ast.parse 通过，`--selftest` 实跑 0 error（2 段落合成示例 + reported/inferred 分层）
- [x] 无虚构：不含题面外接口；inferred 需指向依据证据
- [x] 资源限额：4 文件 / <40KB
