# challenge-96263d10 学术格式与模板适配 v1

## 交付标准清单（从题面提取）

- 4 个重点问题：认得准（提取可核对规格而非猜测）、排得对（逐项符合模板）、转得全（内容单元不丢失不改写）、交得出（导出可用、可编辑源保留、可复核）。
- 评分五维：实际效果 40（完成度/正确性/完整性/可核验性）、使用增益 25、创新增益 15（反推检查项清单、题注与交叉引用联动、转换后保真度比对）、可靠体验 10、生态贡献 10。
- 输出契约三件：目标产物（可编辑稿件+导出件）、事实与来源映射（逐条回溯）、版本与边界（修改差异/人工确认项/缺口/异常）。
- result.json 必含 case_id、status（honest）、sources、uncertainty、change records；partial 必须写明边界。
- 资源限额：≤50 文件、2MB；不提交预制答案。
- 组织方修订：字体用提供的 Liberation Serif；先前缺字体输入/结果视为历史。

## 本版方案

SKILL.md 九节结构：输入识别（Step 0 先落最小 result.json）→ 模板字段盘点表（template_spec.md，每项带 source_location）→ 内容单元盘点（units_inventory.md 对账基准）→ 逐字段映射（field_mapping.md）→ 转换 → 格式校验（validation_report.md + scripts/validate_output.py）→ result.json。
scripts/validate_output.py：规格逐项 PASS/FAIL + 内容单元对账，纯标准库。

## 自测记录

- YAML frontmatter 解析：通过（python3 yaml 解析 name/description）。
- output_contract 覆盖：case_id/status/deliverable/template_fields/facts_sources/changes/uncertainty/gaps/limits 全部落到 SKILL.md §4。
- 脚本语法：ast.parse 通过；实跑最小样例（spec 3 项 + actual 2 过 1 错）输出 PASS/FAIL/SUMMARY 正确，退出码 1。
- 资源：3 文件，约 14KB ≤ 50 文件/2MB。
- SKILL.md 行数：约 175 行 ∈ [150,400]。
