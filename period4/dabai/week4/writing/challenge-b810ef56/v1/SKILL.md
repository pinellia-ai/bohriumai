---
name: evidence-driven-writing
description: |
  文献证据驱动写作 Skill。把"论断清单—证据表—成稿"三段交付做实：每条实质性论断提取编号并关联到具体文献的具体段落（带原文摘录与定位），校验引用真实性与支撑关系，按证据强度分级控制表述，不确定性用恰当限定语。离线运行：不编造文献、不编造数据；每条判定必须带原文位置引用（文件/页/段/摘录），文献不可得时如实标 unverifiable，不猜测内容。
---

# 文献证据驱动写作（论断提取 → 证据表 → 强度分级 → 成稿）

## 1. 用途与适用范围

- 用途：完成需要文献支撑的写作任务，交付论断清单、证据表、成稿三件套，任何一句有依据的话都能指认依据位置与强度。
- 适用：综述/引言/立项依据/回复审稿等证据型写作；不适用无材料依据的观点写作。
- 四大考察点：找得到（论断↔文献段落）、对得上（引用真实且真的支撑）、说得准（强度与不确定性如实）、复得现（他人可独立回查重跑）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id` 原样保留、任务说明、材料路径（稿件/文献 PDF/参考文献列表）、output_contract 全字段。
2. 读 `/input/task.md`：目标体裁、篇幅、引用样式。
3. 用 pdf-text 工具读文献真实全文，**从全文而非摘要取证据**；只有摘要的文献单独标注 abstract_only。
4. 先落盘最小 `result.json`（status=partial 占位）。

## 3. 工作流程（六步流水线）

### Step 1 论断切分（产出 `claims.json`）
把任务/稿件拆成可判定的论断单元：`claim_id | 论断原文 | 类型（事实/方法/结论/观点） | 位置`。一条论断一篇文献能撑 → 单源；需要多篇 → multi-source，逐条列出。

### Step 2 证据抽取（产出 `evidence_table.md`）
对每条论断匹配支撑来源：`claim_id | 文献标识 | 原文摘录（逐字） | 定位（页/段/节） | 支撑范围 | 文献类型（原始研究/综述/指南/预印本）`。摘录必须逐字复制，改一个字都算 FAIL。一篇文献支撑多条论断时每条独立成行。

### Step 3 引用核验（产出 `citation_check.md`）
逐条核验：① 文献是否真实存在于材料中（材料内可指认 → verified；材料外查不到 → **unverifiable，不得编造**）；② 著录信息（作者/年份/期刊/卷期页）与材料一致；③ 编号与参考文献表一致；④ 原文是否真的支撑该论断——识别"支撑了相近但更强/更弱的话"；⑤ 二手转引、撤稿、版本差异逐条标记。**每条核验必须带原文位置引用。**

### Step 4 证据强度分级（写入 evidence_table 附列）
四档口径：`A=领域共识/综述与指南一致支撑`、`B=多项原始研究一致`、`C=单篇原始研究/小样本`、`D=推测/机制假说/作者观点`。分级理由写入判定列（研究设计/样本量/重复验证/共识程度）。**正文表述必须与等级相称**：C 级不得写成"研究表明…（普遍规律）"，D 级必须带"可能/推测"。

### Step 5 成稿（产出 `manuscript.md`，可编辑）
按论断清单组织成文，引用标记与证据表 claim_id 对应；冲突证据如实呈现（"X 报告…，而 Y 报告…，可能因为…"），不隐藏；结论边界、适用人群、机制未明处加限定语。

### Step 6 复核与汇总（result.json）
跑 `scripts/verify_evidence.py`（§6）：摘录逐字比对、定位格式检查、强度-表述匹配抽查。全过 success，否则 partial。

## 4. 输出契约（result.json 逐字段）

```json
{
  "case_id": "<原样保留>",
  "status": "success | partial | failed",
  "deliverable": {
    "manuscript": "/app/output/manuscript.md",
    "claims": "claims.json",
    "evidence_table": "evidence_table.md",
    "citation_check": "citation_check.md"
  },
  "claims_total": 18,
  "evidence_sources": [
    {"claim_id": "C-03", "ref": "[7] Zhang et al. 2021", "quote": "reduced latency by 32%", "location": "zhang2021.pdf p.6 §4.2 para.3", "grade": "B", "verdict": "supports"}
  ],
  "citation_checks": [
    {"claim_id": "C-05", "check": "metadata", "result": "verified", "location": "refs.bib entry 7"}
  ],
  "uncertainty": [
    {"claim_id": "C-09", "issue": "仅可得摘要，全文不可得", "resolution": "表述降级为'作者报告…(摘要级)'", "needs_human_confirm": true}
  ],
  "gaps": ["文献[12]材料未提供全文，无法核验 §3 中的数据细节"],
  "limits": ["C-14 与 C-15 证据冲突，成稿已双向呈现"],
  "reproduce": "按 README 步骤重跑脚本可复现全部判定"
}
```

硬性要求：`evidence_sources` 每条含逐字摘录+定位+等级+判定；`citation_checks` 覆盖全部引用；材料外文献数=0；unverifiable 逐条列明。

## 5. 数字门槛（达不到如实标 partial）

- 论断覆盖：实质论断 100% 有 claim_id；无源论断（稿件自己提出的）单独标 original_claim，不计入证据要求。
- 摘录保真：evidence_table 摘录与原文逐字一致（脚本比对），不一致=FAIL。
- 引用核验率：每条引用都有 citation_check 行；核验不出=unverifiable 如实记录，**禁止编造**。
- 强度匹配：正文强表述（"证实/显著优于"）必须对应 A/B 级，违者 FAIL。

## 6. 校验脚本

捆绑 `scripts/verify_evidence.py`（纯标准库）：输入 `quotes.json`（证据表摘录+定位）与 `originals.json`（从原文复制的关键句），输出逐条 EXACT/ALTERED/MISSING；并对 manuscript.json 的强度词表做分级抽查。先最小样例实跑再正式使用。

## 7. 异常处理表

| 异常 | 处置 |
|---|---|
| 文献不可得/仅有摘要 | 标 abstract_only/unverifiable，表述降级，不编造细节 |
| 原文与摘要矛盾 | uncertainty 记录，以全文为准，needs_human_confirm |
| 证据相互冲突 | 成稿双向呈现+可能原因，limits 说明 |
| 引用格式不支持/权限不足 | gaps 记录，核验项如实标 unverifiable |
| 一条论断需多篇文献 | evidence_table 每篇独立成行，支撑范围分别标注 |
| 撤稿/版本差异 | citation_check 单独标记，成稿降权或移除该支撑 |

## 8. 效率约束

预算 64 请求 / 900 秒：Step 0-1 前 10 请求；文献按 claim 优先级抽取，低价值文献轮空；先落最小 result.json。≤50 文件 / 2MB。

## 9. 最小示例（示意，非正式案例结果）

输入：稿件草稿 + 3 篇文献 PDF。
示意输出：claims.json 12 条；evidence_table 15 行（含 1 条 multi-source）；citation_check 全 verified（1 条 abstract_only 降级）；成稿 4 段；result.json status=success。

## 10. 命令序列

```
1. cat /input/case.json → 最小 result.json
2. 读文献全文 → claims.json（论断切分）
3. evidence_table.md（逐字摘录+定位+分级）
4. citation_check.md（真实性/著录/支撑方向逐条核）
5. manuscript.md（强度相称表述+限定语）
6. python3 scripts/verify_evidence.py quotes.json originals.json
7. 修 FAIL → result.json 定稿
```

## 11. 自查清单（交前全过）

- [ ] YAML frontmatter 可解析
- [ ] 每条论断有 claim_id；每条证据有逐字摘录+定位+等级
- [ ] 每条引用核验带原文位置引用（前人教训：引用核验曾 6 分）
- [ ] 材料外文献=0；unverifiable/gaps 如实
- [ ] result.json 全字段落实（claims_total/evidence_sources/citation_checks/uncertainty/gaps/limits）
- [ ] 脚本 ast.parse + 最小实跑通过
- [ ] ≤50 文件 / 2MB
