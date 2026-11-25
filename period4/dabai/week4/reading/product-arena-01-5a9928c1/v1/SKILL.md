---
name: lit-translate-terminology-locked
description: |
  文献翻译：术语表驱动的英→中双语对照翻译。术语先抽取成表并全篇锁定同一译名
  （含回填校验），段号与原文一一对应，数字/单位/公式/图表编号/引用标记逐项保真，
  每段带译法依据，译不准处明确标注不含混处理。先落盘最小 result.json 再充实。
---

# 文献翻译 Skill — 术语锁定 + 逐段对照（v1）

## 1. 用途与适用范围

- 适用：英→中科研文献（全文或指定段落区间）翻译，输出段落级双语对照 JSON/Markdown：术语表、逐段号对照、保真核验清单、未译标注。
- 不适用（不做也不报）：中→英以外的语向扩展（默认英→中，题面另有要求以题面为准）、诗歌/文学性改写、机器翻译质量评分。
- 四个验收问题（主线）：
  1. **术语稳**：同一术语全篇同一译名，术语表被执行并回填校验。
  2. **段落全**：不漏段不重复不错位，段号与原文一一对应。
  3. **关系准**：指代/否定/限定/因果、数字单位、公式与引用编号与原文一致。
  4. **可核验**：每段译文指回原文位置并带译法依据，译不准处显式标注。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：提取 `case_id`（**原样保留**）与 `output_contract` 全字段——result.json 逐字段落实；case.json 优先于本文。
2. 读 `/input/task.md`：确认翻译范围（全文/区间）、语向、术语表要求。
3. 盘点材料：有文字层照主流线；扫描件/文字层缺失 → OCR 后整篇标 partial；公式或表格为图片 → 保留位置并标 untranslated:image。
4. 材料缺失 → status=failed + failure_reason。

## 3. 工作流程（五步流水线）

### Step 1 段落切分与编号（→ /app/work/segments.jsonl）

- 按语义边界切分：段落为单位；跨页/跨栏续段合并（句号缺失+同章节），标 `merged: true`。
- 每段：`{seg_id: "P0001", src_ref: {page_no, block_index}, src_text, kind: body|caption|table_header|references|abstract}`。
- **段号与原文一一对应**：图注/表头单独编号（FC 类），参考文献条目逐条编号（RF 类）。
- 验收断言：脚本核对段号连续无重复；漏段检测（相邻段间距异常）登记。

### Step 2 术语表抽取与锁定（→ /app/work/glossary.json）

- 从标题/摘要/正文高频名词短语+首字母缩写定义句抽取术语，每条：`{term_en, term_zh, basis: "<定义句位置>", part_of_speech}`。
- 译名锁定规则：同术语全篇唯一译名；缩写首次出现"全称（缩写）"处理，其后统一用中文译名或保留缩写（化学式、模型名保留原文）。
- 翻译中遇到新术语 → **先补术语表再用**，不允许临时即兴译。
- 验收断言：glossary.json 无同 term_en 多译名冲突；冲突=错误。

### Step 3 逐段翻译（→ /app/work/translation.jsonl）

- 携带上下文翻译：当前段 + 已锁定术语表 + 前段末句（指代消解）。
- 每段输出：`{seg_id, tgt_text, term_usage: [term_zh...], translation_notes: "<译法依据：长难句处理/被动语态/定语从句拆分>", flags: []}`。
- 保真纪律（违反=标 flag 并修正）：
  - 数字与单位逐字保留（3.2%, 350 °C, 10⁻³）；
  - 否定与限定词（not only, unless, at least, up to）不得弱化或丢失；
  - 公式与内联变量保留原样；图表编号、文献引用标记 [12] 原位保留。
- 验收断言：translation.jsonl 行数 = segments 行数（不漏不重）。

### Step 4 数字/术语保真核验（→ /app/output/verification.json，scripts 执行）

- 脚本核验：
  1. **数字保真**：原文每处数值/百分比/单位在译文或 flags 中可找到（正则抽取对比）；缺失即 FAIL。
  2. **术语一致**：译文含 glossary 的 term_en 上下文时，检查 term_zh 出现率；同一 term_en 对应多个译名即 FAIL。
  3. **引用保真**：`[\d+]`、`Figure \d`、`Table \d` 计数原文 vs 译文一致；不一致标 flag。
- 核验不通过的段回到 Step 3 修正，直至通过或登记 unresolved（译不准处：`{seg_id, issue: "ambiguous_source|untranslatable_term", note}`）。
- 验收断言：verification.json 数字/术语/引用三类核验各有 pass 计数与 fail 清单。

### Step 5 result.json 组装（先最小后充实）

- 进入 Step 3 前写最小 result.json（status=partial）；走完覆盖完整版。
- 同时输出人类可读版 bilingual.md（段号并排：原文 | 译文 | notes）。

## 4. 输出契约

result.json（以 case.json output_contract 为最高优先，以下为基准全集）：

```json
{
  "case_id": "<原样>",
  "status": "success | partial | failed",
  "translation": {
    "segments_total": 0, "translated": 0, "with_flags": 0,
    "bilingual_file": "translation.jsonl", "readable_file": "bilingual.md"
  },
  "terminology": {
    "glossary_file": "glossary.json", "entries": 0,
    "consistency_check": "pass | fail:<明细>"
  },
  "fidelity": {
    "numbers_check": {"pass": 0, "fail": []},
    "references_check": {"src_count": 0, "tgt_count": 0, "pass": true},
    "formula_citation_preserved": true
  },
  "evidence_and_boundary": {
    "locator_format": "seg_id -> page_no+block_index",
    "untranslated": [{"seg_id": "", "reason": "image_formula|missing_text_layer|reference_list", "note": ""}],
    "unverifiable": ["<源文歧义无法确认的译法>"],
    "not_reported": ["<材料未提供项>"]
  },
  "run_status": {"state": "", "failure_reason": "", "manual_intervention_point": ""},
  "sources": ["<实际输入文件>"],
  "uncertainty_notes": ["<OCR 段落、存疑译法>"],
  "change_log": []
}
```

## 5. 数字门槛（达不到诚实标 partial）

1. 段落守恒：translated + untranslated（有 reason）= segments_total，无静默漏段。
2. 术语一致率 100%（脚本核验 pass）；数字保真 fail 清单为空或逐条解释。
3. 引用/图表编号计数原文=译文。
4. 每段有 src_ref 与 translation_notes；flags 有 issue+note。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 文字层缺失/扫描件 | OCR 后标 partial + 逐段置信度进 uncertainty_notes |
| 公式/表格为图片 | 保留位置标 untranslated:image，不虚构公式内容 |
| 参考文献无法解析 | references 区整段标 untranslated:reference_list，不硬译 |
| 原文残缺/语言混杂 | 残缺段标 flag；混杂语言段按实际语言处理并登记 |
| 术语译名冲突 | 回退首次定义句译名，冲突登记 |
| 长文超预算 | 按章节顺序翻，每章完成即落盘，中断处标 partial 并写明已译范围 |
| output_contract 与本文冲突 | 以 case.json 为准 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 全字段落实
- [ ] 术语表锁定执行，无同术语多译名
- [ ] 段号一一对应，无漏段/重复/错位
- [ ] 数字/单位/公式/引用标记保真核验通过
- [ ] 每段带译法依据；译不准处显式标注
- [ ] untranslated 逐条有 reason

## 8. 效率约束

预算 64 请求 / 900 秒。策略：切分、编号、数字/术语/引用核验全脚本化（scripts/fidelity_check.py）；模型请求只用于术语抽取与逐段翻译；每章落盘防中断。限额 ≤50 文件 / 2MB。

## 9. 最小示例（示意输出，非正式案例结果）

```json
{"seg_id":"P0012","src_ref":{"page_no":3,"block_index":8},
 "src_text":"The catalyst exhibits superior activity, achieving 92% conversion at 350 °C.",
 "tgt_text":"该催化剂表现出更优的活性，在 350 °C 下实现 92% 的转化率。",
 "term_usage":["转化率"],"translation_notes":"superior activity 译为'更优的活性'，保留比较级含义；数字单位逐字保留","flags":[]}
{"seg_id":"FC002","untranslated":false,"src_text":"Figure 3: XRD patterns of...","tgt_text":"图 3：……的 XRD 图谱"}
{"seg_id":"P0020","issue":"ambiguous_source","note":"原文指代 it unclear, 译法以最近名词为准，需人工确认"}
```

（以上为格式示意，正式结果以实际材料运行为准。）
