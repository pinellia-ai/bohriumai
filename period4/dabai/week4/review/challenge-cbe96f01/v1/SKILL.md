---
name: citation-fact-verify
description: |
  引用与事实核验：对固定论文逐条核对"引用是否支持结论、事实来源是否可靠、证据是否落得到原文"。
  铁律：每条核验必须带原文位置引用（file+locator+逐字quote），无引用的条目一律视为不合格；
  引用支持四判定（完整/部分/不支持/无法判定）逐条对账；无法确认标 pending，不凭空补结论，不虚构文献。
---

# 引用与事实核验 — 逐条引用对账执行版 Skill（v1）

## 0. 铁律（先读，最高优先）

1. **每条结论必须能指到原文具体位置**：`file + locator(P段号/页码) + quote(逐字摘录)`。缺任一项的核验条目不得进入交付（前代教训：引用无原文位置引用 → 低分）。
2. 判定与引文语义一致：**区分"引用存在"与"引用支持结论"**。引文原文取不到时不判"不支持"，标 `undeterminable` 并写明缺什么。
3. 不虚构文献、不编造被引主张、不凭空补结论；材料外内容标 `unverifiable`。
4. 预算 64 请求 / 900 秒 / 16384 token：先落盘最小 result.json（status=partial）再充实。

## 1. 用途与适用范围

- 适用：给定论文/科研材料，产出引用与事实核验的可检查结论清单：逐条问题（位置、原文、判定、严重度、修改建议）+ 引用逐条对账表。
- 不适用：论文润色、综述写作、数据分析建模、代作者判断研究结论。文献阅读只为审查提供材料，本课题只计问题发现、证据定位、严重度判断和修改建议。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id` 原样保留；`output_contract` 全字段逐条落实，与本文冲突以 case.json 为准。
2. 读 `/input/task.md`：确认核验范围（全部引用 or 指定章节）、报告语言。
3. `ls -la /input/` 盘点；材料缺失 → status=failed + failure_reason，不虚构。参考文献表、被引文献全文若在输入中，登记到可用证据源清单 sources.json。

## 3. 工作流程（七步流水线）

### Step 1 材料装载与定位器（→ /app/work/paragraphs.csv, locators.json）

- 运行 `python3 scripts/make_locators.py /input/<材料> --outdir /app/work`：PDF 走 pdftotext→pdf 库降级，docx 解 XML，HTML 剥标签；每段得 `para_id`（P001…）。
- 单独登记参考文献表各条目（ref_id R001…，逐字摘录题名/作者/年份/出版状态）。
- 验收：段落数 >0；失败面如实记 run_log.md。

### Step 2 正文引用点清点（→ citation_spots.csv）

- 扫描全文引用标记（[n]、(Author, year)、脚注），每处登记 {spot_id, locator, quote 论文该句逐字摘录, ref_id 对应参考文献条目, claim_summary 本文借该引用支持的论断}。
- 验收：正文引用点全部登记（漏一个引用点即验收失败）；无引用标记的稿件记录说明并降级为事实核验为主。

### Step 3 引用支持四判定（→ citation_ledger.csv，本题核心）

对每个引用点判定 `{spot_id, verdict, basis, evidence_quote}`：

| verdict | 判据 |
|---|---|
| fully_supported | 被引文献主张（或输入内原文）完整覆盖本文论断的强度与范围 |
| partially_supported | 引文只覆盖论断一部分，本文表述强于引文（指出超出的具体词句） |
| unsupported | 引文主张与本文论断方向相反或无关（必须给出引文主张与本文论断的对照句） |
| undeterminable | 被引文献原文不可得/元数据不全/语义歧义；写明"缺什么证据可定论" |

- 被引文献原文只在 /input 内可得；输入外文献**不检索也不猜**，一律 undeterminable。预印本与正式版本不一致处单独标注。
- 验收：citation_ledger 行数 = citation_spots 行数；每行 verdict ∈ 四值；非 undeterminable 行必须有 evidence_quote。

### Step 4 事实来源可靠性 + 数值一致性（→ findings.json）

- source_reliability：来源等级、出版状态、版本差异、更正/撤稿信息——输入材料内可核的才判，否则 pending。
- numeric_consistency：正文、表格、图注、摘要之间的数字、样本量、显著性表述逐处对照，不一致即 finding（quote 两处原文）。
- 每条 finding 七件：`id/category/location{file,locator,quote}/issue_type/severity/evidence/recommendation`。issue_type ∈ {fact_error, insufficient_evidence, norm_issue, suggestion, pending_review}；severity ∈ {major, minor}。
- 验收：`python3 scripts/audit_check.py /app/output/result.json` 退出码 0。

### Step 5 论证链与规范核查（→ findings.json 追加）

- argument_chain：结论跳跃、循环论证、以偏概全、缺对照的推断——每条给推理两端的原句。
- academic_norm：数据与代码可用性、伦理与利益冲突声明——有则查一致性，无声明只记 suggestion/norm_issue，不判学术不端。
- 误报抑制：作者明确标注的假设情形、转述他人观点、学科惯例不报为事实错误。

### Step 6 覆盖对账（→ coverage.json）

- 六类各记 {checked, items_scanned, findings_count, pass_count, pending_count, na}：citation_support、source_reliability、numeric_consistency、argument_chain、fact_verification、academic_norm。
- 证据定位专项统计：全部 findings 与 citation_ledger 的 locator 覆盖率必须 100%（validator 强制）。

### Step 7 result.json + 执行留痕

- Step 2 完成后即落盘最小 result.json；七步走完充实为完整版。
- run_log.md 逐记录：时间/命令/输入/输出/计数/降级路径。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "status": "success | partial | failed",
  "deliverables": {"citation_spots": "citation_spots.csv", "citation_ledger": "citation_ledger.csv", "findings": "findings.json", "evidence": "evidence.csv", "coverage": "coverage.json", "run_log": "run_log.md"},
  "review_report": {"findings_total": 0, "by_severity": {"major": 0, "minor": 0, "suggestion": 0, "pending_review": 0}, "citation_verdicts": {"fully_supported": 0, "partially_supported": 0, "unsupported": 0, "undeterminable": 0}, "top_issues": []},
  "evidence_and_boundary": {"quotation_policy": "所有 quote 为原文逐字摘录；引文主张对照句逐字", "pending_review": [], "unchecked": []},
  "coverage": {"citation_support": 0, "source_reliability": 0, "numeric_consistency": 0, "argument_chain": 0, "fact_verification": 0, "academic_norm": 0},
  "sources": [], "uncertainty_notes": [], "change_log": []
}
```

以 case.json `output_contract` 为最高优先补齐字段。每条结论满足三问：指得到原文位置、判定与引文语义一致、换一人按记录复核能得到同一批结论。

## 5. 数字门槛

1. citation_spots 与 citation_ledger 行数相等且全覆盖。
2. findings + ledger 全部条目 location.quote 非空（validator 强制，违者退出码 1）。
3. unsupported 判定必须附引文主张对照句；undeterminable 必须写缺什么。
4. coverage 六类全出现。
5. pending_review 条目写明缺失证据。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| PDF 无法解析 | 降级链如实记录；不可解析部分标 unchecked，result=partial |
| 引用标记格式异常 | 人工语义扫描兜底（it、these studies 等指代也逐条登记） |
| 参考文献表缺失 | 支持判定全部 undeterminable，只审正文引用位置存在性 |
| 被引文献原文不在输入 | 不检索不猜，undeterminable + 缺证据说明 |
| 扫描件无文本层 | 按页记 failed，result=partial，不编造文本 |
| 稿件超长 | 分批扫描，coverage 记未深扫区域，标 partial |

## 7. 自查清单

- [ ] case_id 原样；output_contract 全覆盖
- [ ] 每个 finding/ledger 行有 file+locator+quote
- [ ] 四判定用对：没把"引用存在"当"引用支持"
- [ ] undeterminable 条目全写了缺什么
- [ ] audit_check.py 退出码 0
- [ ] run_log.md 完整

## 8. 效率约束

Step 1-3 脚本化+结构化输出为主；引用点分批判定；单响应只处理一类事务；先落盘后充实。≤50 文件 / 单文件 500KB / 总 2MB。

## 9. 最小示例（示意输出，非正式案例结果）

citation_ledger.csv 片段：

```csv
spot_id,locator,quote,ref_id,verdict,basis,evidence_quote
S001,P004,"Prior work shows transformer accuracy exceeds 90% on this task [3]","R003","undeterminable","输入未包含文献[3]原文","缺：文献[3]的主张原文"
```

findings.json 片段：

```json
{"id":"F001","category":"numeric_consistency","location":{"file":"manuscript.pdf","locator":"P001 (Abstract)","quote":"n=214 participants"},"issue_type":"fact_error","severity":"major","evidence":"§3.1 P012 称 n=204，摘要 P001 称 n=214","recommendation":"核对原始记录并统一样本量"}
```
