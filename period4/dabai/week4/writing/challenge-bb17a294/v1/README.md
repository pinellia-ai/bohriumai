# challenge-bb17a294 写作12｜学术翻译与双语写作 v1

## 交付标准清单（从题面提取）

- 四重点：术语稳（同一译法贯穿摘要/正文/题注/附录，符合学科惯用）、数字实（数值/单位/量级/年份/统计口径原样落地，万/亿 vs million/billion 换算规范）、对得齐（句段一一对应可双语修改，公式/表格/题注/脚注/参考文献原位保留）、边界清（增译省译/否定范围/因果强度/限定语/引用归属保真）。
- 评分五维：实际效果 40（整篇译出+三种输出形态之一+可进入修改流程）、使用增益 25（减少后编辑工时）、创新增益 15（术语抽取/分块/对齐约束/二次校验）、可靠体验 10、生态贡献 10。
- 输出契约三件 + GitHub 附加分条款；result.json 含 case_id/honest status/sources/uncertainty/change records。
- 资源限额 ≤50 文件 / 2MB。前人弱项 59.0：本版加严为"术语锁定表先行 + 段号 100% 对照 + 数字保真脚本校验"。

## 本版方案

SKILL.md 十一节：Step 0 盘点完整性对账基准 → 术语锁定表（先行，含学科依据与适用范围）→ 数字资产盘点 numbers.json（换算式固定记录）→ 结构对账表（段号骨架）→ 逐段双语翻译（边界守卫四查）→ 数字保真脚本校验 → 引用与边界自查。
scripts/check_translation.py：数字保真（norm 归一匹配+EXTRA 增译检查）+ 术语唯一（MULTI 报警）。

## 自测记录

- YAML 解析通过（name=academic-translation-bilingual）。
- output_contract 覆盖：case_id/status/deliverable/facts_sources/term_locks/changes/boundary_checks/uncertainty/gaps/limits 全落实 §4。
- 脚本 ast.parse 通过；最小实跑：NUM OK 2 + NUM FAIL 1（漏译）+ NUM EXTRA 1（增译）+ TERM FAIL 1（多形式），全部正确抓出，退出码 1。
- 资源 3 文件约 17KB；SKILL.md 约 160 行。全过。
