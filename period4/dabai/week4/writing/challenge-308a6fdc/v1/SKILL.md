---
name: paper-writer
description: |
  学术论文学术写作 Skill：从实验记录、图表、文献等固定材料出发，产出结构
  完整、可进入修改环节的章节稿。核心方法：先建材料索引（每条材料支撑正文
  哪一部分），再大纲先行逐节成稿，论断-材料/引用双向绑定（引用带作者年份
  期刊DOI与材料位置），成稿前跑事实一致性检查（正文vs图表vs摘要），输出
  待核清单。不编造文献与数据，材料外内容标 unverifiable。
---

# 学术论文写作 Skill

## 1. 用途与适用范围

- 用途：给定研究材料（实验记录/问卷/代码输出/图表/文献条目），写出章节齐全、事实可溯源、引用可对账、可直接编辑的论文章节稿（非提纲、非建议）。
- 适用：IMRaD 学科论文、结果段/图注转写、综述整理。
- 边界：材料不足的部分显式标缺，不用模型知识补数值/样本量/结论。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id` 原样、`output_contract` 全字段、材料清单。
2. 读 `/input/task.md`：学科模板、章节要求、字数、引用格式（GB/T 7714 / APA / 期刊名）。
3. 逐个打开材料；PDF/CSV/图片读实际内容，不凭文件名臆测。
4. 建 `/app/work/material-index.md`：每条材料一行 → `M-n | 路径 | 类型 | 关键内容(数值/结论) | 可支撑的正文位置`。口径冲突（两材料数值矛盾）显式标注，不擅自取舍。
5. 材料缺失 → status=failed + missing_inputs。

## 3. 工作流程（6 步流水线）

### Step 1 材料索引 → /app/work/material-index.md
- 验收：每条材料有唯一 ID；数值类材料抄录原值+单位+样本量；冲突项标 `conflict`。

### Step 2 章节大纲 → /app/work/outline.md
- 按学科模板列章节：摘要/引言/方法/结果/讨论/结论/参考文献/数据可得性声明（按 task.md 增删）。
- 每节：论证任务、引用材料（M-n 列表）、字数预算（总和=要求字数）。
- 验收：任务要求的章节/图表/声明字段无缺项；缺项显式标 `gap` 并在 README/result 说明。

### Step 3 逐节成稿 → /app/work/draft.md
- 写作规则：
  - 每个数值/单位/样本量后带 `[M-n]`；每条引用句末带 `[R-n]`；
  - 图注引用与图面一致（误差范围/显著性标记照抄材料原值）；
  - 趋势不得写成因果（"与…相关"≠"导致"）；
  - 摘要与结果数值逐一一致（最后核对）。
- 验收：无未标注来源的事实句（脚本核对 [M-n]/[R-n] 覆盖）。

### Step 4 引用清单与对账 → /app/work/references.md
- 每条：`[R-n] 作者. 题名. 期刊, 年, 卷(期): 页. DOI`，字段只抄材料内已有信息；材料未给的字段留空标 `missing-field`，不编造。
- 双向对账：正文每个 [R-n] ↔ references.md 条目；references.md 每条 ↔ 正文引用位置。
- 验收：悬空引用=0；每条引用标注它支撑的论断句。

### Step 5 事实一致性检查 → scripts/check_paper.py
- 运行 `python3 scripts/check_paper.py draft.md references.md material-index.md`
- 核对：① 材料 ID / 引用 ID 无悬空；② 摘要中的数值都在结果段出现；③ 数字抄录与 material-index 一致（抽取正文数值比对）；④ 未标注来源的事实句比例。
- fail 项回 Step 3 修复，最多 2 轮。输出 `consistency.json`。

### Step 6 交付 → /app/output/
- `result.json`、`draft.md`、`references.md`、`material-index.md`、`consistency.json`、`todo-review.md`（待人工复核清单：材料冲突、missing-field 引用、推断句）。
- 稿件保留章节层级/图注编号/引用格式，markdown 可直接续编；docx 需求时附渲染预览。

## 4. 输出契约（result.json 逐字段）

以 `output_contract` 为准，通用骨架：

```json
{
  "case_id": "<原样>",
  "status": "completed | partial | failed",
  "deliverables": {
    "draft_markdown": "/app/output/draft.md",
    "references": "/app/output/references.md",
    "material_index": "/app/output/material-index.md",
    "consistency_report": "/app/output/consistency.json",
    "todo_review": "/app/output/todo-review.md"
  },
  "fact_source_map": [
    {"claim": "两组差异显著(p=0.03)", "source": "M-3 table2", "ref_id": null}
  ],
  "version_and_boundaries": {
    "change_records": ["结果段数值全部抄自M-3，未做换算"],
    "manual_review_items": ["R-2 缺DOI字段", "摘要句'提示因果'已降级为相关表述"],
    "material_gaps": ["无讨论部分所需同领域对比文献"],
    "anomalies": []
  },
  "uncertainty": [
    {"item": "M-3 与 M-5 样本量口径不一致", "level": "high", "handling": "正文采用M-3并标注冲突"}
  ],
  "summary": {"sections": 7, "n_materials": 12, "n_citations": 9, "word_count": 5400}
}
```

## 5. 数字门槛

| 门槛 | 值 | 不达标 |
|---|---|---|
| 章节齐全（任务要求） | 100% | 缺项 → partial 并标 gap |
| 数值/样本量来源标注率 | 100% | <90% → partial |
| 悬空 [M-n]/[R-n] | 0 | 必须修复 |
| 引用字段编造 | 0 条 | 发现即删标 missing-field |
| 摘要-结果数值一致 | 100% | 不一致必须修复 |
| 趋势→因果改写 | 0 处 | 检查到即降级表述 |

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 材料缺图注 | 图位置留占位+todo-review 标注，不虚构图注 |
| 图表与正文数值冲突 | 两值并列标注，标 conflict，manual_review |
| 文献取不到全文 | 只用材料内条目信息，缺字段标 missing-field |
| 引用格式不认识 | 按材料原样保留+标注，推测格式记入 anomalies |
| 材料超长 | 按 outline 所需证据定向抽取，索引记录策略 |
| 任务要求的章节材料完全不支持 | 该节写 gap 说明，不硬写 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 字段全覆盖
- [ ] 每条数值有 [M-n]，每条引用有 [R-n] 且双向对账 0 差异
- [ ] 摘要 vs 结果数值一致；图注与图面一致
- [ ] 无编造文献字段；missing-field 全部标注
- [ ] conflict / gap / 推断句进入 todo-review.md
- [ ] consistency.json 全 pass 或已修复说明
- [ ] status 与实际一致

## 8. 效率约束

- 64 请求/900 秒：Step0-2 合并 2 次调用；成稿分 2-3 批；先落最小 result.json 再充实。
- ≤50 文件、单文件 ≤500KB、总量 ≤2MB。

## 9. 最小示例（示意输出，非正式案例结果）

输入：实验记录 csv + 2 张图 + 5 条文献条目。
material-index 12 条（M-1..M-12，M-4/M-7 口径冲突已标）→ outline 六节预算 → 成稿（"两组基线均衡[M-3]…差异显著(p=0.03)[M-3]"，引用[R-1..R-5]）→ check_paper.py 悬空=0、摘要数值一致 → references.md 5 条（R-3 缺 DOI 标 missing-field）→ result.json status=completed + todo-review 3 条。
