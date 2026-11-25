---
name: lit-review-generator
description: |
  文献综述生成 Skill：在一批真实文献上跑完"筛选→主题归纳→证据表→带引用草稿"四步，交付每句可回链、强度不越界的综述。
  方法主线：先写筛选标准再执行（记录留痕）→主题从文献实际分布归纳（方法/对象/结论分歧维度，非通用框架硬套）→
  证据表（文献标识/原文摘录/页码段落/支撑论断/证据强度，草稿可反查证据行）→草稿逐句绑定证据行并标注表述强度
  （已被证明/有提示性证据/仍有争议）→冲突文献并列呈现、空白落到具体证据缺口。全文离线可复算。
---

# 文献综述生成（Screen · Theme · Evidence-Table · Draft）

## 1. 用途与适用范围

- **做**：给定文献集与研究问题，产出筛选记录、主题划分、证据表、带引用综述草稿。验收三件事：筛选标准先于写作写明且一致执行；每条实质论断指回文献具体位置；主题与空白从文献里长出来。
- **不做**：单篇精读、翻译润色、选刊、事实审查。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：case_id 原样保留、文献集（题录/PDF）、研究问题、输出要求（字数/结构/引用格式）。
2. 盘点：文献数、全文可得数、重复数、元数据完整率。
3. 文献集为空 → status=failed。

## 3. 工作流程（五步）

### Step 1 筛选（标准先行；产物 screening.json）
- 先写纳入/排除标准（相关到研究问题、有全文或摘要、语言/时间窗），再逐条执行。
- 处理：完全重复（哈希/DOI）归并、低相关（关键词命中<阈值）排除并留理由、仅摘要文献标 abstract_only。
- 每条筛选结论留痕：`{rec_id, verdict, reason}`。**记录与筛选同步产生，不事后补写。**

### Step 2 主题归纳（产物 themes.json）
- 归纳维度：方法路线、研究对象、结论方向（一致/分歧）；**不从通用框架（背景/方法/挑战/展望）硬套**。
- 每个主题：`{theme_id, name, definition, member_refs[], boundary(主题边界与排他), basis(哪些文献支撑此划分)}`。
- 校验：主题间无重叠（每篇文献只进一个主主题，跨主题文献在 boundary 说明）；无遗漏（unassigned 清单必须为空或说明理由）。

### Step 3 证据表（`evidence_table.py` 校验；产物 evidence_table.csv）
- 每行：`{ev_id, rec_id, theme_id, quote(原文摘录), locator(文件+页/段), supports(支撑的论断 id), strength: direct|partial}`。
- 摘录必须真实：脚本校验 quote 在对应文献文本中可定位（归一空白匹配）；对不上 → 该行标 `quote_unverified` 不入正式表。

### Step 4 草稿生成（模型，≤5 次；产物 draft.md）
- 结构：主题即章节；每段围绕 1-2 个论断句。
- **逐句绑定**：每个实质论断句尾 `[EVxx]` 引用证据行；引用格式按案例要求。
- 强度标注三档：已被证明（≥2 独立文献 direct 且无冲突）/ 有提示性证据（单文献或 partial）/ 仍有争议（冲突文献并存）；句式与强度匹配（争议主题不用断言句式）。
- 冲突文献并列呈现（"A 报告 X[EV1]；B 报告相反 Y[EV2]"），不抹平叙事线。

### Step 5 空白与交付（`draft_check.py` 全检；→ /app/output/result.json）
- 研究空白 = 证据表覆盖矩阵中的空格（某主题×某维度无 direct 证据），逐条附缺口说明，禁止套话收尾。
- 全检通过后交付 result.json + draft.md。

## 4. 输出契约（result.json 逐字段）

```json
{
  "case_id": "原样保留",
  "status": "ok|partial|failed",
  "screening": {"criteria": {"include": ["..."], "exclude": ["..."]},
                 "records": [{"rec_id": "...", "verdict": "include|exclude", "reason": "..."}],
                 "counts": {"input": 0, "included": 0, "excluded": 0, "abstract_only": 0, "duplicates": 0}},
  "themes": [{"theme_id": "T1", "name": "...", "definition": "...", "member_refs": [...], "boundary": "...", "basis": "..."}],
  "evidence_table": [{"ev_id": "EV1", "rec_id": "...", "theme_id": "T1", "quote": "...", "locator": "file.pdf#p3,para2",
                       "supports": "C1", "strength": "direct"}],
  "draft": {"file": "draft.md", "n_claims": 0, "claims": [{"claim_id": "C1", "text": "...", "evidence": ["EV1", "EV2"],
              "strength": "已被证明|有提示性证据|仍有争议"}]},
  "conflicts": [{"topic": "...", "claim_a": "C1", "claim_b": "C3", "refs": [...]}],
  "gaps": [{"theme": "T2", "dimension": "方法对比", "note": "无 direct 证据行", "excluded_reason": "..."}],
  "uncertainty": ["2 篇仅有摘要（abstract_only），相关论断强度降为 partial"],
  "operation_evidence": {"scripts": ["evidence_table.py", "draft_check.py"],
                          "rerun_cmd": "evidence_table.py 校验 quote→draft_check.py 全检"}
}
```

## 5. 数字门槛

- 引用绑定率 100%：draft 中每个实质论断句带 ≥1 个 [EVxx]，且 EV 存在于证据表。
- quote 真实率 100%：证据表正式行全部通过脚本定位校验（quote_unverified 不入表）。
- 主题覆盖：included 文献 100% 归入主题或在 boundary 说明。
- 强度一致性：有冲突证据的主题不得出现"已被证明"强度论断。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 缺全文 | abstract_only 标注，相关论断 strength=partial |
| 元数据不全 | 从首行/文件名补录并标注 |
| 文献重复 | 归并留一条，其余 duplicates 计数 |
| 结论冲突 | conflicts 并列呈现 |
| 超出上下文（长文献） | 分块抽证据，不整篇塞入 |
| 检索/输入为空 | status=failed |
| quote 校验失败 | quote_unverified，不入正式表 |

## 7. 自查清单

- [ ] case_id 原样；筛选标准先于执行写明。
- [ ] 主题有 basis/boundary；无 unassigned 遗漏。
- [ ] 每条论断有 [EVxx] 回链；强度与证据量一致。
- [ ] draft_check 全项 pass 后交付。

## 8. 效率约束

筛选与 quote 校验脚本化；模型请求：主题归纳 1、每主题草稿 1（≤5）、空白判读 1。先落 screening.json + evidence_table.csv（脚本产物），再写草稿。

## 9. 最小示例（示意输出，非正式案例结果）

证据行：`EV3, R07, T2, "we observed no dose-response", lit07.pdf#p5,para1, supports C2, partial`
草稿句："在高剂量区间的剂量-效应关系仍有争议 [EV1][EV3]。"（强度=仍有争议，因 EV1/EV3 方向相反）
