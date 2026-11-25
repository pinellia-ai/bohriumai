---
name: logic-argument-audit
description: |
  论文逻辑与论证审查：抽取作者主张并逐条与证据对齐，追踪推理链，检查章节衔接与前后一致性，
  产出带位置、类型、严重度和可执行建议的问题清单。防误报三原则：作者有意设置的对照、明确标注的
  假设情形、转述他人观点不得报为作者自相矛盾；每条问题定位到句（file+locator+逐字quote），不凭空补结论。
---

# 论文逻辑与论证审查 — 主张-证据对齐执行版 Skill（v1）

## 1. 用途与适用范围

- 适用：对论文完成论点/证据/推理链/章节衔接四维逻辑审查，产出问题清单：每条有位置（到句）、类型、严重度、可解释分级依据、能落到具体句子的修改建议。
- 不适用：文字润色与语言优化、查重与学术不端判定、参考文献格式检查、原始数据重分析、投稿策略。
- 做对三问：报出的问题真实存在且能回到原句；定位精确到评审可直接核对；修改建议可执行（补什么证据/改哪一句/把哪个结论强度降下来）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id` 原样保留；`output_contract` 全字段逐条落实，冲突以 case.json 为准。
2. 读 `/input/task.md`：确认审查范围与报告语言。
3. `ls -la /input/` 盘点；缺失 → status=failed + failure_reason。
4. **长度检查**：估算全文段落总数；若预算内无法覆盖全文，先扫摘要/引言承诺/结果/讨论，coverage 如实记录未深扫区域并标 partial——**禁止截断后宣称完成全文审查**。

## 3. 工作流程（七步流水线）

### Step 1 材料装载与定位器（→ /app/work/paragraphs.csv, locators.json）

- `python3 scripts/make_locators.py /input/<材料> --outdir /app/work` 生成段落定位器 P001…与章节归属。
- 验收：段落数 >0；章节数登记进 outline.json（章名+起止 locator）。

### Step 2 主张清单（→ claims.json，本题核心输入）

从摘要、引言、结果、讨论抽取每条核心主张：

```json
{"claim_id":"C001","locator":"P023","quote":"原文逐字","claim_source":"author_claim|cited_view|hypothetical","qualifier":"限定词（如 only in mice / suggests / may）","strength":"strong|hedged","supports":"支撑它的证据 locator 列表（可暂空）"}
```

- **claim_source 三分（防误报关键）**：`author_claim` 作者自己的主张；`cited_view` 转述/引用他人观点；`hypothetical` 明确标注的假设情形（如 if X were true, we would expect…）。逐条判准看原文措辞；拿不准标 `ambiguous` 并在 evidence 说明。
- 验收：主张数 ≥ 摘要与讨论中可辨识结论数；每条有 locator+quote。

### Step 3 主张-证据对齐（→ alignment.csv）

对每条 author_claim 判 `{claim_id, verdict, basis, evidence_locators}`：

| verdict | 判据 |
|---|---|
| supported | 本文实验/数据或所引内容足以支撑该强度表述（含限定词） |
| overclaimed | 结论强度超出数据范围（指出超出的具体词句，建议降强度或补证据） |
| no_evidence | 找不到任何支撑证据 |
| undeterminable | 证据存在但不可及（图表读不出/引文取不到），写明缺什么 |

- 引文原文不在输入内时按引文摘要句判断；不足以判 → undeterminable。
- 验收：author_claim 全覆盖；cited_view/hypothetical 不参与"自相矛盾"判定。

### Step 4 推理链检查（→ findings.json）

逐类扫描，每条 finding 八件 `id/category/location{file,locator,quote}/issue_type/severity/evidence/recommendation`：

- `reasoning_jump` 推理跳跃：从前提到结论缺中间步骤（给出两端原句）。
- `hidden_assumption` 隐含假设未说明。
- `alt_explanation` 替代解释未排除（如未设对照即归因）。
- `correlation_causation` 相关性表述被换成因果表述（给出原句与建议改法）。
- `circular` 循环论证；`overgeneralization` 以偏概全/外推超出数据范围。
- issue_type ∈ {fact_error, insufficient_evidence, norm_issue, suggestion, pending_review}；severity ∈ {major, minor, suggestion}。

### Step 5 跨章节一致性（→ consistency.csv）

- 逐项对照，每行 {pair, a_locator, a_quote, b_locator, b_quote, verdict: consistent|inconsistent|unverifiable}：
  - 引言承诺的问题 ↔ 方法/结果是否交付；
  - 方法口径 ↔ 结果口径（指标、单位、分组数）；
  - 摘要 ↔ 正文结论；
  - 图表 ↔ 正文描述。
- 验收：pairs ≥ 6（材料不足时如实少记并在 run_log 说明）。

### Step 6 严重度与建议（并入 findings）

- 每条 major/minor 的 evidence 必须回答三问：是否影响主结论、是否可修正、是否影响可复现性。
- recommendation 必须可执行到句子：改哪一句、补什么证据、把哪个结论的强度降下来；"建议加强逻辑"这类空话不允许出现。

### Step 7 覆盖对账 + result.json + run_log

- coverage.json：六类（claim_evidence_alignment、reasoning_chain、cross_section_consistency、fact_verification、citation_support、academic_norm）+ 五维（论点/证据/推理链/衔接/严重度建议）。
- Step 2 完成后先落盘最小 result.json（partial）；七步走完充实。
- run_log.md 逐记录时间/命令/输入/输出/计数/降级。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "status": "success | partial | failed",
  "deliverables": {"claims": "claims.json", "alignment": "alignment.csv", "findings": "findings.json", "consistency": "consistency.csv", "coverage": "coverage.json", "outline": "outline.json", "run_log": "run_log.md"},
  "review_report": {"findings_total": 0, "claims_total": 0, "by_severity": {"major": 0, "minor": 0, "suggestion": 0, "pending_review": 0}, "alignment_verdicts": {"supported": 0, "overclaimed": 0, "no_evidence": 0, "undeterminable": 0}, "top_issues": []},
  "evidence_and_boundary": {"quotation_policy": "quote 逐字", "pending_review": [], "unchecked": []},
  "coverage": {"claim_evidence_alignment": 0, "reasoning_chain": 0, "cross_section_consistency": 0, "fact_verification": 0, "citation_support": 0, "academic_norm": 0},
  "sources": [], "uncertainty_notes": [], "change_log": []
}
```

以 case.json `output_contract` 为最高优先补齐。

## 5. 数字门槛

1. claims 每条有 locator+quote+claim_source；author_claim 100% 进入 alignment。
2. findings 每条八件齐全，quote 非空（validator 强制）。
3. consistency pairs ≥6 或 run_log 说明材料不足。
4. major/minor 的 evidence 含三问回答；recommendation 无空话。
5. coverage 六类全出现。
6. 全文覆盖或如实标 partial + 未深扫区域清单。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 论文解析失败/扫描版无文本 | 降级链记录；result=partial，列不可解析页 |
| 超长截断风险 | 优先摘要/引言/结果/讨论；coverage 记未扫区域；标 partial，不宣称全文完成 |
| 章节缺失 | 对应一致性对 unverifiable，不判 inconsistent |
| 引用无法获取 | 对齐判 undeterminable，不判 overclaimed |
| 表述歧义（是作者主张还是转述） | claim_source=ambiguous + uncertainty_notes，不出双判定 |
| 图表无法读取 | 相关一致性对 pending，不猜内容 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 全覆盖
- [ ] 每条 claim/finding/consistency 行有 file+locator+quote
- [ ] 未把 cited_view/hypothetical 报成作者自相矛盾
- [ ] recommendation 全部可执行到句
- [ ] audit_check.py 退出码 0
- [ ] run_log.md 完整

## 8. 效率约束

Step 1 脚本化；主张抽取与对齐按章节分批；单响应一类事务；先落盘后充实。≤50 文件 / 500KB / 2MB。

## 9. 最小示例（示意输出，非正式案例结果）

alignment.csv 片段：

```csv
claim_id,verdict,basis,evidence_locators
C003,overclaimed,"数据仅两个剂量点，结论写'proves safety across all doses'，超出范围","P031;P033"
```

findings.json 片段：

```json
{"id":"F002","category":"reasoning_chain","location":{"file":"manuscript.pdf","locator":"P042","quote":"Since gene X correlates with disease severity, targeting gene X will reduce severity"},"issue_type":"insufficient_evidence","severity":"major","evidence":"观察性数据（P038 称 no intervention）；影响主结论：治疗建议直接建立在该因果句上；可修正：改因果为相关表述","recommendation":"将 P042 改为 'is associated with disease severity, suggesting a potential therapeutic target'，并在讨论明确未做干预实验"}
```
