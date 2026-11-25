---
name: nanopub-assertion-extractor
description: |
  Nanopublication：把论文结论段落拆成单条可判断真假的科研断言，输出
  nanopublication 四部分结构（Head/Assertion/Provenance/PublicationInfo），
  每条断言绑定最小充分证据片段与原文位置，溯源链完整（断言→证据→论文→作者→年份）。
  找不到支撑的断言标 unsupported 不删除，不编造证据，先落盘最小 result.json。
---

# Nanopublication 构建与校验 Skill（v1）

## 1. 用途与适用范围

- 适用：从论文段落（摘要/结论/结果）抽取原子断言，按 nanopublication 规范（Head / Assertion / Provenance / Publication Info 四部分）结构化导出，附证据绑定与溯源元数据。
- 不适用（不做也不报）：断言真假的科学裁决（只绑定证据不判定对错）、全文知识图谱、联网查证。
- 四个验收问题（主线）：
  1. **拆得细**：一段结论拆成若干条单义、可判断真假的断言，保留条件与限定。
  2. **对得上**：每条断言绑定最小充分证据片段，位置可指出。
  3. **追得回**：断言→证据→论文→作者→年份→版本链路完整。
  4. **读得懂**：导出 JSON 结构符合约定 schema，下游可直接解析。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：提取 `case_id`（**原样保留**）与 `output_contract` 全字段——result.json 逐字段落实；case.json 优先于本文。
2. 读 `/input/task.md`：确认抽取范围（指定段落或全文）与导出格式要求。
3. 盘点材料：论文文本/元数据文件逐个登记路径与类型；缺元数据（作者/年份/标识符）如实登记 not_found，不编造 DOI。
4. 材料缺失 → status=failed + failure_reason。

## 3. 工作流程（五步流水线）

### Step 1 段落定位（→ /app/work/segments.jsonl）

- 为每个目标段落登记：`{segment_id, doc_id, section_id, para_id, page_no, text_verbatim}`。
- text_verbatim 逐字保留，不清洗改写。
- 验收断言：每条可回查原文；范围外段落不处理。

### Step 2 断言拆解（→ /app/work/assertions.jsonl）

拆解规则（每条断言通过后才入列）：

| 规则 | 判据 | 违反后果 |
|---|---|---|
| R1 单一性 | 一条断言只含一个可判断真假的主张；并列句/因果句拆开 | 拆分或拒绝 |
| R2 条件保留 | "when/if/under X" 等限定全部进 `qualifier` 字段 | 拒绝 |
| R3 忠实性 | 不得引入原文没有的数值、主体、比较 | 拒绝 |
| R4 粒度 | 主语+关系+宾语+限定可独立判断真假；整段话塞一个字段=违反 | 拒绝 |

- 每条：`{assertion_id, segment_id, subject, predicate, object, qualifier, scope_notes}`。
- 复合句拆分策略：and 连接的并列主张拆条；因果主张拆为"机制主张"+"效果主张"两条；数字结论保留数值与单位进 object。
- 验收断言：脚本检查每条断言四字段非空、qualifier 不混入主干。

### Step 3 证据绑定（→ 合并进 assertions.jsonl）

- 每条断言绑定：`{evidence_span: <原文最小充分片段>, evidence_loc: {doc_id, section_id, para_id, page_no, sentence_no}, evidence_type: direct|derived}`。
- **最小充分判据**：片段只含判断该断言所需信息；片段过长（>3句）须截取并说明。
- evidence_span 必须在原文中子串匹配（脚本核验）。
- derived 证据（需要跨句拼接）登记 derivation_notes，说明拼接逻辑。
- 找不到支撑的断言：保留，`evidence_span=null` + `support=unsupported`——**不删除也不编造**。
- 验收断言：verify_assertions.py 通过；unsupported 条目逐条登记。

### Step 4 四部分组装（→ /app/output/nanopubs.jsonl + nanopubs.ttl 可选）

每条断言输出一个 nanopublication 结构：

```json
{"np_id": "NP001",
 "Head": {"np_id": "NP001", "assertion_id": "A001", "title": "<短标题>"},
 "Assertion": {"subject": "", "predicate": "", "object": "", "qualifier": "", "statement_text": ""},
 "Provenance": {"evidence_span": "", "evidence_loc": {}, "evidence_type": "direct",
                "doc_id": "", "doc_title": "", "authors": [], "year": null, "version_or_doi": "",
                "section": "", "page_no": null},
 "PublicationInfo": {"extracted_at_runtime": true, "extractor": "skill-v1", "confidence_basis": "why this evidence suffices"}}
```

- **断言溯源**：Provenance 链必须完整到论文级（doc_title/authors/year）；元数据缺失的字段填 null 并登记 not_found，不造值。
- 验收断言：脚本校验四部分字段齐全。

### Step 5 result.json 组装（先最小后充实）

- 进入 Step 2 前写最小 result.json（status=partial）；走完覆盖完整版。

## 4. 输出契约

result.json（以 case.json output_contract 为最高优先，以下为基准全集）：

```json
{
  "case_id": "<原样>",
  "status": "success | partial | failed",
  "nanopublications": {
    "file": "nanopubs.jsonl",
    "count": 0,
    "four_part_valid": 0,
    "unsupported_count": 0
  },
  "assertions_summary": {
    "total": 0, "with_direct_evidence": 0, "with_derived_evidence": 0, "unsupported": 0,
    "per_segment": [{"segment_id": "", "assertions": 0}]
  },
  "evidence_and_boundary": {
    "locator_format": "doc_id+section_id+para_id+page_no+sentence_no",
    "not_found": ["<元数据/证据缺失项>"],
    "unverifiable": ["<无法判断真假的断言及原因>"]
  },
  "run_status": {"state": "", "failure_reason": "", "manual_intervention_point": ""},
  "sources": ["<实际输入文件>"],
  "uncertainty_notes": ["<derived 拼接说明、存疑绑定>"],
  "change_log": []
}
```

## 5. 数字门槛（达不到诚实标 partial）

1. 100% 断言过 R1-R4 拆解规则（脚本初筛+人工语义复核记录）。
2. 100% 断言有 evidence_loc；evidence_span 子串匹配率 100%（unsupported 除外且单独登记）。
3. Provenance 四部分齐全：四部分字段校验通过率 100%。
4. 元数据（authors/year/doi）缺失逐条 not_found，编造=0。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 扫描件无文本层 | 标 unresolved + OCR 说明，不虚构证据片段 |
| 断言跨图表证据 | evidence_loc 指图表 id+页码；无位置信息→unsupported |
| 断言与证据冲突 | 保留断言 + 标 conflict + 双方片段都登记，不裁决 |
| 复合句拆分存疑 | 拆条并在 scope_notes 说明拆分依据 |
| 元数据缺失 | 填 null + not_found 登记 |
| 段落重复抽取 | 按 segment_id 去重，重复登记 deduped |
| output_contract 与本文冲突 | 以 case.json 为准 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 全字段落实
- [ ] 每条断言单一可判真假，qualifier 保留条件
- [ ] 每条证据最小充分且可子串匹配；unsupported 如实保留
- [ ] 四部分结构校验通过；溯源链到论文级
- [ ] not_found/unverifiable 如实登记
- [ ] nanopubs.jsonl 每行可独立解析

## 8. 效率约束

预算 64 请求 / 900 秒。策略：拆解规则初筛、证据子串核验、四部分校验全部脚本化（scripts/verify_assertions.py）；模型请求只用于断言拆解与最小充分片段选择；先落盘最小 result.json。限额 ≤50 文件 / 2MB。

## 9. 最小示例（示意输出，非正式案例结果）

```json
{"np_id":"NP001","Head":{"np_id":"NP001","assertion_id":"A001","title":"Catalyst activity claim"},
 "Assertion":{"subject":"the Ni-Fe catalyst","predicate":"achieves","object":"92% conversion","qualifier":"at 350 C, H2/CO2=3","statement_text":"The Ni-Fe catalyst achieves 92% CO2 conversion at 350 C with H2/CO2=3."},
 "Provenance":{"evidence_span":"92% CO2 conversion was obtained at 350 C","evidence_loc":{"doc_id":"primary","section_id":"S3","para_id":"P8","page_no":4,"sentence_no":2},"evidence_type":"direct","doc_title":"<原文标题>","authors":["<原文作者>"],"year":2024,"version_or_doi":"<原文DOI或null>","section":"3. Results","page_no":4},
 "PublicationInfo":{"extracted_at_runtime":true,"extractor":"skill-v1","confidence_basis":"span contains both value and conditions of the assertion"}}
```

（以上为格式示意，正式结果以实际材料运行为准。）
