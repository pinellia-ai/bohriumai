# README — challenge-105b70ee 文献结论与数据提取 (v1)

## 交付标准清单（从题面提取）

- 接口：读 `/input/target-fields.json`，每个 field_id 输出一条结果，保留
  scalar / units / statistic / experimental condition / comparator / 精确 paragraph_id / quote，
  状态四态 `reported | not_reported | source_conflict | extraction_failed`。
- 三条红线（题面组织方修订 v2 原文）：猜的值不是抽取；缺的字段不是零；字面引文匹配≠语义正确。
- 输出：`/app/output/result.json`，含 case_id、主结果、证据定位、运行状态、不确定性、变更记录。
- 评分关注：统一字段表还原而非压缩总结；数值/单位/误差/统计量/条件不改写不合并；缺项区分"未报告"与"抽取失败"；字段可回指定位，他人可按同一口径复跑。
- 附加分：GITHUB_URL.txt（第一行链接）。

## 文件

- `SKILL.md` — 六步流水线（字段表展开→来源索引→逐字段抽取→四态判定→脚本校验→落盘）
- `scripts/validate_extraction.py` — 覆盖率/枚举/引文子串匹配/数值同现校验，带 `--selftest`

## 自测记录（2026-11-25）

- [x] YAML frontmatter 可解析（python3 yaml.safe_load）
- [x] output_contract 覆盖：case_id/status/fields[](field_id,status,value,units,statistic,experimental_condition,comparator,source,paragraph_id,quote,conflicts,notes)/uncertainty/change_log 全部落盘
- [x] validate_extraction.py `ast.parse` 语法通过，`--selftest` 实跑通过（3 字段合成示例，0 error）
- [x] 无虚构：SKILL.md 不含题面外接口/字段/数据，not_reported 不填 0
- [x] 资源限额：文件数 4，总大小 < 60KB（≤50 文件 / 2MB）
- [x] SKILL.md 约 200 行，信息密度达标
