# challenge-51977f9b 系统性文献综述 v1

## 交付标准清单（自题面提取）

- [x] output_contract 三块：研究产物（synthesis 结论+PRISMA 计数一致）、证据矩阵（纳入研究/纳排理由/质量评价/定位）、不确定性（冲突/偏倚/空白/不可得声明）
- [x] result.json 含 case_id + status
- [x] 突破方向覆盖：检索式（PICO 要素+同义词/受控词+分段意图）、纳排标准（条款化+版本化+冲突规则）、筛选记录（两轮逐条判定+judged_by+分歧标记）、质量评价（维度判断+依据位置+等级影响结论规则）、可复核流程（脚本化复算纳入集+PRISMA）
- [x] 排除性条款先行、筛选途中不放宽
- [x] 脚本实跑通过（含复算一致性验证）

## 自测记录（2026-11-24）

1. YAML frontmatter PASS；name=systematic-review-pipeline。
2. output_contract 字段 100% 覆盖：PASS。
3. ast.parse：screen.py PASS。
4. 构造 5 条题录 + 5 条款实跑：
   - 筛选逐条留痕（verdict/clause_id/reason_terms/judged_by）；综述条目被 E3 正确排除（排除先行）
   - PRISMA 计数对账：identified 5 = title_excluded 2 + included 3
   - 复算一致性：重跑筛选日志 sha256 相同：PASS
5. 无虚构：全文不可得走 fulltext_unavailable 条款，不冒充全文判定：PASS

## 调用方式

```bash
python3 scripts/screen.py screen criteria.json corpus.json --round title --out /app/work/screening_log.jsonl
python3 scripts/screen.py screen criteria.json corpus.json --round fulltext --out /app/work/screening_log.jsonl --fulltext-dir <PDF目录>
python3 scripts/screen.py prisma /app/work/screening_log.jsonl --out /app/work/prisma_counts.json
# Agent 补 quality_appraisal.csv 与 synthesis（规则见 SKILL.md §3 Step4/5），汇总写 /app/output/result.json
```

## 边界与限制

- 题录级判定基于标题/关键词/摘要词命中，全文级由模型复核并留 disagreement 记录。
- 质量评价维度可按领域换量表，但"依据位置"必填。
