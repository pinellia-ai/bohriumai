# README — product-arena-02-7051d92d 学术语言润色 v1

## 交付标准清单（自题面提取）

output_contract / 运行时契约逐字段：
1. `result.json` 落 `/app/output`，含 output_contract 全部原始字段 + `case_id` 原样保留。
2. 目标产物：润色后**完整可编辑文本**（非建议、非整段重写）+ 逐句修改说明。
3. 事实与来源映射：数字、术语、引用、图表、关键论断可逐条回溯，不新增材料外事实。
4. 版本与边界：修改差异（原句/改句/类型/理由）、人工确认项、材料缺口、异常全部标注。
5. 状态字段：complete/partial/failed 如实；partial 必须说明边界。
6. 资源限额：≤50 文件、单文件 ≤500KB、总量 ≤2MB、无符号链接。
7. 不预制答案、不编造评测分数；预算 64 请求 / 900 秒。

题面四个重点问题的应对：
- 改得对 → 六类逐句检查表（SKILL.md Step 3）+ change_type 分类。
- 说得像 → 术语表先行（Step 1）+ 语域检查 + 目标文体假设显式记录。
- 没改坏 → 最小编辑原则 + 禁改清单 + polish_check.py 限定强度漂移告警。
- 讲得清 → 改动对照表必含 locus/original/revised/type/reason，理由写到第三方可判断。

## 文件清单

- SKILL.md：skill 本体（流水线 + 输出契约 + 门槛 + 异常 + 自查 + 示例）。
- scripts/polish_check.py：改动对照表校验器（字段完整性 + id 去重 + 限定词漂移告警）。

## 自测记录（2026-11-25）

- YAML frontmatter 解析：通过（python yaml.safe_load）。
- output_contract 字段覆盖：result.json 契约含 case_id/status/polished_text/changes/term_table/sources/unverified/change_records/uncertainty，对照题面"目标产物/事实与来源映射/版本与边界"三块全覆盖。
- 脚本语法：`python3 -c "import ast; ast.parse(open('polish_check.py').read())"` 通过。
- 脚本实跑：构造含 1 条合法 + 1 条缺字段样例 result.json 实测，能正确报错与告警（见下）。
- 资源限额：3 文件，约 12KB，远低于 2MB。
- 无虚构：SKILL.md 不含题面外接口/字段；示例明确标注为示意输出。
