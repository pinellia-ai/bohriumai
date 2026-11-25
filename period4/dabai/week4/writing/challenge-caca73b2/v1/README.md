# challenge-caca73b2 写作10｜结果与讨论章节写作 v1

## 交付标准清单（从题面提取）

- 四重点：读得准（图表数值/单位/误差棒/统计量正确读入）、分得清（结果=事实，讨论=解释/文献对照/局限）、说得住（表述强度与证据匹配，有边界的写法）、核得了（数值回溯图表、论断对应文献）。
- 五方向：数据与图表/结果描述/趋势与差异/讨论证据/因果边界与局限。
- 评分五维：实际效果 40（可编辑可提交的结果段+讨论段、图表读数与统计一致、阴性结果/不一致文献/局限如实）、使用增益 25、创新增益 15、可靠体验 10（缺图/缺统计量/单位不明处置）、生态贡献 10。
- 输出契约三件；result.json 含 case_id/honest status/sources/uncertainty/change records。
- 资源限额 ≤50 文件 / 2MB。

## 本版方案

SKILL.md 十一节：Step 0 图表盘点（读数不确定不猜）→ 数值台账 numbers_ledger.json（误差棒含义依图注）→ 发现清单（含阴性结果）→ 结果段（只写事实+有边界写法）→ 讨论段（数据/文献对照三式+因果三词区分+局限四层面）→ 证据回溯表 → 脚本校验。
scripts/check_results.py：正文数值↔台账比对、图表引用编号存在性、结果段解释句 CROSSING WARN。

## 自测记录

- YAML 解析通过（name=results-discussion-writing）。
- output_contract 覆盖：case_id/status/deliverable/facts_sources/claims/changes/uncertainty/gaps/limits 全落实 §4。
- 脚本 ast.parse 通过；最小实跑：NUM OK 1 + NUM FAIL 1（台账外）+ FIG FAIL 1（不存在的 Fig.5）+ CROSSING WARN 1，全部正确抓出，退出码 1。
- 资源 3 文件约 17KB；SKILL.md 约 150 行。全过。
