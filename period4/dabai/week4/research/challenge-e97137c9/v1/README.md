# challenge-e97137c9 文献综述生成 v1

## 交付标准清单（自题面提取）

- [x] output_contract 三块：研究产物（draft.md + claims/强度）、证据矩阵（evidence_table：文献/摘录/定位/支撑论断/强度）、不确定性（abstract_only/冲突/空白不越界）
- [x] result.json 含 case_id + status
- [x] 突破方向覆盖：文献筛选（标准先行+留痕+重复/低相关/仅摘要处理）、主题归纳（方法/对象/结论分歧维度+basis/boundary，非通用框架）、证据组织与回链（quote 脚本校验可定位、草稿可反查证据行）、草稿生成（[EVxx] 逐句绑定+强度三档匹配句式）、冲突并列+空白落证据缺口
- [x] 脚本实跑通过（quote 校验+草稿全检，含坏草稿抓错）

## 自测记录（2026-11-24）

1. YAML frontmatter PASS；name=lit-review-generator。
2. output_contract 字段 100% 覆盖：PASS。
3. ast.parse：draft_check.py PASS。
4. 构造 2 文献语料实跑：
   - quotes 校验：2/2 quote 在对应文献文本可定位（归一空白）：PASS
   - 好草稿：dangling=0、硬违规=0、未绑定论断=0 → pass：PASS
   - 坏草稿（悬空 EV9 + 单证据称"已被证明"）：fail，dangling=["EV9"]、hard=1：PASS
5. 无虚构：quote_unverified 不入正式表；abstract_only 论断强度降 partial：PASS

## 调用方式

```bash
# Agent 五步执行；产物落 /app/work：screening.json / themes.json / evidence_table.csv / draft.md
python3 scripts/draft_check.py quotes /app/work/evidence_table.csv --corpus /app/work/corpus.json --out /app/work/ev_check.json
python3 scripts/draft_check.py draft /app/work/draft.md --evidence /app/work/evidence_table.csv --out /app/work/draft_check.json
# 两检 pass 后汇总写 /app/output/result.json + draft.md（schema 见 SKILL.md §4）
```

## 边界与限制

- quote 校验基于题录文本（title/abstract/head）；全文 PDF 场景以分块文本定位。
- 强度判定规则写死（≥2 direct 无冲突=已被证明），争议主题不得用断言句式。
