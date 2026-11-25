---
name: systematic-review-pipeline
description: |
  系统性文献综述 Skill：走完"研究问题结构化→检索式构造→纳排条款→两轮筛选留痕→质量评价→带证据回链的综述结论"全链路，
  每一步可复算、可追溯。方法主线：PICO 拆检索要素（P/I/C/O/S 各配同义词与受控词）→检索式逐段注明意图→
  纳排标准条款化且筛选途中不放宽（判定留痕）→PRISMA 式计数流水→质量评价逐条给维度判断与依据位置→
  冲突证据矩阵+研究空白。筛选判定脚本化（依据条款表），他人可重算纳入集。
---

# 系统性文献综述（Protocol · Screen · Appraise · Synthesize）

## 1. 用途与适用范围

- **做**：从研究问题到综述结论的可复核流程：检索式、纳排标准、筛选记录、质量评价、结论+冲突+空白。验收三件事：每篇纳/排有可查理由；每条论断回链到证据；他人拿同样输入与条款能复算出一致的纳入集。
- **不做**：单篇精读翻译、写作润色、事实核查（属学术审查）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：case_id 原样保留、研究问题、题录集/PDF 集、纳排输入约束、输出要求。
2. 题录数、字段完整率、全文可得性盘点。
3. 输入为空 → status=failed。

## 3. 工作流程（六步）

### Step 1 协议与检索式（产物 protocol.json）
- PICO(+S) 结构化：P 对象 / I 干预 / C 比较 / O 结局 / S 研究类型，每要素配同义词+受控词组。
- 检索式：布尔式逐段生成，**每段注明意图**（如 `("cell apoptosis" OR "programmed cell death") -- 覆盖 P 要素同义词`）。
- 声明：数据库/字段/时间范围/语言限制；检索日期记录。

### Step 2 纳排标准（产物 criteria.json，先于筛选写定）
条款化、可判定：`{crit_id, type: include|exclude, clause(研究类型/对象/时间/语言/全文可得), priority, conflict_rule}`。
- 条款间冲突处理规则写死：排除性条款（综述/语言/对象不符）先行；同为纳入时按 priority。
- **版本化**：筛选途中修订条款 → 记 diff 并重新筛已判条目，不允许悄悄放宽。

### Step 3 两轮筛选（`screen.py` 脚本化判定 + 模型复核，产物 screening_log.jsonl）
- 题录级：标题+摘要 vs include/exclude 条款，逐条判定 `hit_clause`（哪条条款、命中词）。
- 全文级：仅对题录级通过者做（PDF/正文可得时），记全文级排除理由（条款+位置）。
- 每条记录：`{rec_id, round, verdict: include|exclude, clause_id, reason_terms, judged_by: script|model|human, date}`。
- 分歧标记：脚本 include 但模型判 exclude → `disagreement` 单列，双人/双法不一致不清除记录。

### Step 4 质量评价（产物 quality_appraisal.csv）
- 对纳入研究逐条：维度（设计/样本/测量/偏倚控制）判断 + **依据位置（locator）** + 总体等级（high/moderate/low）。
- 等级如何影响结论的规则写明（如 low 级证据只支撑"有提示性证据"强度，不支撑"已被证明"）。

### Step 5 综合与 PRISMA 计数（产物 synthesis.json + prisma_counts.json）
- 计数流水：识别→去重→题录筛→全文筛→纳入，每步数量与排除原因分布。
- 结论每条：`{claim, supported_by: [rec_id...], strength: proven|indicative|contested, locator 逐条}`；冲突证据矩阵并列。
- 空白基于纳入集覆盖范围（哪些 PICO 格子无纳入研究）。

### Step 6 交付（→ /app/output/result.json）

## 4. 输出契约（result.json 逐字段）

```json
{
  "case_id": "原样保留",
  "status": "ok|partial|failed",
  "protocol": {"pico": {"P": "...", "I": "...", "C": "...", "O": "...", "S": "..."},
                "search_string": "((\"term1\" OR \"term2\") AND ...) -- 分段意图注释",
                "databases": ["local corpus"], "date_range": "...", "languages": "...", "search_date": "..."},
  "criteria": {"include": [{"crit_id": "I1", "clause": "...", "priority": 1}], "exclude": [{"crit_id": "E1", "clause": "..."}],
                "conflict_rule": "...", "version": "v1"},
  "screening": {"prisma": {"identified": 0, "duplicates_removed": 0, "title_screened": 0, "title_excluded": 0,
                             "fulltext_assessed": 0, "fulltext_excluded": 0, "included": 0},
                 "exclusion_reasons": {"E1": 12, "E2": 3}, "disagreements": 0,
                 "log": "screening_log.jsonl"},
  "quality": [{"rec_id": "...", "design": "adequate", "sample": "unclear", "measurement": "adequate",
                "bias_control": "inadequate", "overall": "moderate", "basis_locators": ["..."]}],
  "synthesis": [{"claim": "...", "supported_by": ["rec1", "rec2"], "strength": "proven|indicative|contested",
                  "evidence_locators": ["..."]}],
  "conflicts": [{"topic": "...", "rec_a": "...", "rec_b": "...", "note": "..."}],
  "gaps": [{"pico_cell": "O=长期结局", "note": "纳入集无该格研究", "exclusion_query": "..."}],
  "uncertainty": ["3 篇全文不可得，仅题录级判定"],
  "operation_evidence": {"scripts": ["screen.py"], "rerun_cmd": "screen.py criteria.json corpus.json 可复算纳入集"}
}
```

## 5. 数字门槛

- 筛选可复算率 100%：重跑 screen.py，纳入集与首次一致（条款未变时）。
- 排除理由覆盖率 100%：每条 exclude 有 clause_id + 命中依据。
- 回链率 100%：synthesis 每条 claim 的证据可定位到纳入研究原文。
- 强度不越界：low 质量证据不得支撑"已被证明"。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 检索为空 | 检查检索式覆盖（同义词/受控词），仍空 → 如实报告 0 纳入 |
| 数据库/接口超时 | 记录 + 降级本地语料，uncertainty 声明范围 |
| 全文不可得 | 仅题录级判定，单独计数 |
| 术语歧义 | 词表归一 + 歧义条目列出 |
| 条款冲突 | 按优先级 + conflict_rule，判定留痕 |
| 纳入证据互相矛盾 | conflicts 矩阵并列 |
| 筛选途中改条款 | 版本化 diff + 已判条目重筛 |

## 7. 自查清单

- [ ] case_id 原样；检索式分段有意图；纳排先于筛选写定且版本化。
- [ ] PRISMA 计数对账（每步数字能相互推算）。
- [ ] 每条纳入/排除可查理由；quality 逐条有依据位置。
- [ ] 论断回链 + 强度与质量等级一致。

## 8. 效率约束

题录级筛选全脚本化（<1s/千条）；模型请求：协议构造 1、全文级复核 ≤6、综合 ≤3。先落 prisma_counts.json，再综合。

## 9. 最小示例（示意输出，非正式案例结果）

`screen.py screen criteria.json corpus.json --round title --out screening_log.jsonl`
→ `{"rec_id": "R0012", "verdict": "exclude", "clause_id": "E3", "reason_terms": ["综述(review)"], "judged_by": "script"}`
