# challenge-142d91a2 开题报告与研究计划书 v1

## 交付标准清单（自题面提取）

- 七要素齐全：研究背景 / 问题定义 / 目标 / 技术路线 / 阶段计划 / 风险 / 预期成果，与给定周期和资源相容。
- 四问题：立得住（问题具体可证伪、指向真实缺口）、对得上（目标-路线-验证-成果一一对应）、排得开（计划落在周期/经费/数据/人员内，里程碑与任务量匹配）、说得清（风险有触发信号与备选，论断与引用可追溯）。
- 目标数量 1-3，每个有可考核目标与判断标准（指标、样本、对照、时间点）。
- 风险按数据获取/方法可行性/进度/伦理合规分类，含触发信号、影响范围、备选方案、决策时点。
- 论断-引用一一对应，引用可追溯；材料外内容标 unverifiable；不编造文献。
- result.json 落实 output_contract 全字段 + case_id；含 status/sources/uncertainty/change_records。
- 可编辑 markdown/docx 交付；Office 类附渲染预览。

## 组件

- SKILL.md：六步流水线（约束抽取→缺口陈述→大纲→成稿→脚本校验→交付留痕）。
- scripts/check_proposal.py：七要素标题、悬空引用、来源覆盖率、周期/经费门槛校验。

## 自测记录

1. YAML frontmatter 解析：PASS（python yaml 解析通过）。
2. output_contract 字段覆盖：题面通用契约（目标产物/事实与来源映射/版本与边界）→ result.json deliverables / fact_source_map / version_and_boundaries 三块全覆盖；case_id/status/uncertainty 均落实。PASS。
3. 脚本语法 + 实跑：构造最小 proposal.md 与 constraints.json 实跑通过（见下）。
4. 资源限额：3 个文件，约 9KB ≤2MB。PASS。
