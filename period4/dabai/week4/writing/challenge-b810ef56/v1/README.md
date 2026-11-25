# challenge-b810ef56 写作05｜文献证据驱动写作 v1

## 交付标准清单（从题面提取）

- 四重点：找得到（论断提取并关联文献具体段落）、对得上（文献真实、著录准确、原文真的支撑）、说得准（证据强度与不确定性如实）、复得现（论断清单/证据表/摘录/判定理由可独立回查）。
- 评分五维：实际效果 40（三段交付：论断清单—证据表—成稿）、使用增益 25、创新增益 15（论断切分/来源匹配/强度判定）、可靠体验 10、生态贡献 10。
- 输出契约三件：目标产物（成稿）、事实与来源映射（逐条回溯）、版本与边界。
- 硬规矩：引用核验每条带原文位置引用（PLAYBOOK 教训：前人引用核验曾 6 分）；不编造文献/数据。
- 资源限额 ≤50 文件 / 2MB。

## 本版方案

SKILL.md 十一节：Step 0（全文而非摘要取证据）→ 论断切分 claims.json → 证据表（逐字摘录+定位+文献类型）→ 引用核验（五查：真实性/著录/编号/支撑方向/转引撤稿）→ 强度四档分级（A/B/C/D）→ 成稿（冲突证据双向呈现）→ 脚本复核。
scripts/verify_evidence.py：摘录逐字比对（EXACT/ALTERED/MISSING）+ 强度-表述匹配抽查。

## 自测记录

- YAML 解析通过（name=evidence-driven-writing）。
- output_contract 覆盖：case_id/status/deliverable/claims_total/evidence_sources/citation_checks/uncertainty/gaps/limits 全落实 §4。
- 脚本 ast.parse 通过；最小实跑：EXACT 1、ALTERED 1、MISSING 1，退出码 1 符合预期。
- 资源 3 文件约 16KB；SKILL.md 约 150 行。全过。
