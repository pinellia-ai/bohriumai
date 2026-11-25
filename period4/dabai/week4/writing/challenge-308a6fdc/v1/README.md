# challenge-308a6fdc 写作01｜学术论文写作 v1

## 交付标准清单（自题面提取）

- 产出结构完整、可进入修改环节的章节稿（不是提纲/建议/素材堆叠）。
- 写得实：数值、单位、样本量、图注、结论来自给定材料，不模型补全。
- 引得对：每条引用真正支撑所在论断；作者/年份/期刊/DOI 只抄材料内信息，缺则标 missing-field，不编造。
- 全得起来：学科模板章节、图表、参考文献、声明字段齐备，缺项显式标注。
- 改得动：保留章节层级/图注编号/引用格式，markdown/docx 可继续编辑。
- 一致性检查：正文 vs 图表、摘要 vs 结果、方法 vs 实际步骤；输出待核清单。
- result.json 落实 output_contract 全字段 + case_id。

## 组件

- SKILL.md：六步流水线（材料索引→大纲→成稿→引用对账→一致性检查→交付）。
- scripts/check_paper.py：悬空 [M-n]/[R-n]、摘要数值必须出现在结果段、无来源事实句比例四项校验。

## 自测记录

1. YAML frontmatter 结构校验：PASS（name=paper-writer）。
2. output_contract 覆盖：目标产物（draft/references/index/consistency/todo）、事实与来源映射（fact_source_map）、版本与边界（change_records/manual_review/gaps/anomalies）全覆盖。PASS。
3. 脚本实跑：正例全 PASS（exit=0）；反例（悬空 M-9、摘要 130 vs 结果 120）正确 FAIL 两项（exit=1）。PASS。
4. 资源限额：3 文件约 11KB ≤2MB。PASS。
