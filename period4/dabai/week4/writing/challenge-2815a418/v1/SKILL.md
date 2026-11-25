---
name: rebuttal-writer
description: |
  审稿回复与论文修改 Skill：把审稿意见清单+指定版本基线稿件，处理成可直接
  提交的逐条回复信与修订稿。意见按编号/类型/子要求拆解，逐条给出采纳决策，
  每处"已修改"落到修订稿可检索锚点，形成意见-改动-定位台账；需补证据的意见
  生成证据清单并标到位状态；多轮返修维护承诺台账保证版本一致。离线运行，
  只基于给定材料，不冒称真实审稿意见或已补实验。
---

# 审稿回复与论文修改 Skill

## 1. 用途与适用范围

- 用途：输入 = 审稿意见（逐字或摘要）+ 指定版本稿件；输出 = 修改稿（可编辑 markdown/docx）+ 逐条回复信 + 修改定位表 + 未到位证据清单。
- 适用：单轮与多轮返修；意见来自摘要材料时只处理实际给出的条目。
- 边界：不冒称真实审稿人逐字要求、不冒称已补做实验/原作者已改稿/编辑部已接收。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id` 原样保留、`output_contract` 全字段、材料路径。
2. 读 `/input/task.md`：任务边界（如"只修订指定基线"）、回复信格式要求、语气约束。
3. 打开稿件与意见文件，确认版本标识（文件名/日期/哈希），记入台账 `version` 字段。
4. 版本不匹配（意见引用的章节稿件中不存在）→ 记 anomalies，不臆测缺失章节内容。
5. 材料缺失 → result.json `status=failed` + `missing_inputs`，不虚构。

## 3. 工作流程（6 步流水线）

### Step 1 意见拆解 → /app/work/comments.json
- 每条意见：`{id, verbatim, type(方法/数据/写作/格式/伦理), severity(high/med/low), sub_requirements[], relations[]}`。
- 一条意见含多个子要求必须拆开（如"补统计并改图3"= 2 个子要求），各自独立跟踪。
- 验收：意见数与原文件一致；每条 ≥1 个子要求。

### Step 2 回应决策 → /app/work/decisions.md
- 每个子要求给四元组：`决策(采纳/部分采纳/不采纳) | 理由 | 落地动作(具体到章节/段落) | 状态`。
- 不采纳必须给可查证理由（数据不可得/超出范围/审稿人误解——误解需引原文澄清），语气四档：接受/澄清/礼貌反驳/申诉；禁止冒犯、过度承诺、无原则顺从。
- 冲突意见（两位审稿人要求矛盾）→ 记 manual_review_items，采用编辑友好方案并双标。
- 验收：子要求 100% 有决策；"已修改"类决策必须有落地动作。

### Step 3 修订稿 → /app/work/manuscript-revised.md
- 只动需要动的地方：逐处最小编辑，保留作者原意与既有表述。
- 每处改动前后插入锚点标记 `<!--CHG-{n}-->`，改动集中登记 `changes.json`：`{n, comment_id, location(章节/段落/原句锚文本), before, after, reason}`。
- 不可执行改动（如审稿人要求补实验但材料无数据）不得跳过：在修订稿对应位置加 `[TODO-E{n}: 待补实验说明，见 evidence.md]`。
- 验收：每个采纳类决策都有 ≥1 条 change 记录；before 在原稿中可检索到（脚本核对）。

### Step 4 回复信 → /app/work/response-letter.md
- 逐条意见编号回应，格式：审稿人意见原文（缩引）→ 总体回应 → 逐子要求：决策+理由+改动定位（`修订稿 §x.y，锚 CHG-{n}`）。
- 定位三要素齐全：章节号 + 段落序/原句锚文本 + 锚 ID。
- 多轮返修：维护 `commitments.json`（上一轮承诺→本轮落实状态），承诺未兑现的显式说明。
- 验收：意见覆盖率 100%；每处"已修改"有定位且定位在修订稿中可查。

### Step 5 定位对账 → scripts/check_rebuttal.py
- 运行 `python3 scripts/check_rebuttal.py manuscript-revised.md response-letter.md changes.json`
- 核对：① letter 中每个锚 ID 在修订稿中存在；② changes.json 的 before 在原稿中可检索；③ 意见 id 覆盖 = comments.json 全集；④ TODO-E 均在 evidence 清单中。
- fail 项回 Step 3/4 修复，最多 2 轮。

### Step 6 交付 → /app/output/
- `result.json`、`manuscript-revised.md`、`response-letter.md`、`changes.json`、`evidence.md`、`checks.json`。
- evidence.md：需补证据的意见 → 证据项 | 数据出处 | 到位状态(到位/部分/无法补做) | 无法补做时的替代说明。

## 4. 输出契约（result.json 逐字段）

以 `output_contract` 为准，通用骨架：

```json
{
  "case_id": "<原样>",
  "status": "completed | partial | failed",
  "deliverables": {
    "revised_manuscript": "/app/output/manuscript-revised.md",
    "response_letter": "/app/output/response-letter.md",
    "change_log": "/app/output/changes.json",
    "evidence_list": "/app/output/evidence.md"
  },
  "fact_source_map": [
    {"comment_id": "R1.2", "change_id": 3, "location": "§3.2 para2 锚'基线特征'", "basis": "materials/manuscript-baseline.md"}
  ],
  "version_and_boundaries": {
    "manuscript_version": "<输入版本标识>",
    "change_records": ["§3.2 新增基线描述句（回应R1.2）"],
    "manual_review_items": ["R2.1 与 R3.2 要求冲突，采用合并方案待编辑确认"],
    "material_gaps": ["无原始统计数据，R1.3 的重做分析项无法在本演练补做"],
    "anomalies": []
  },
  "uncertainty": [
    {"item": "R1.4 引用的文献在材料中无全文", "level": "high", "handling": "仅按意见转述，未补写"}
  ],
  "summary": {"n_comments": 8, "n_sub_requirements": 13, "n_changes": 11, "n_pending_evidence": 2}
}
```

## 5. 数字门槛

| 门槛 | 值 | 不达标 |
|---|---|---|
| 意见覆盖率（含子要求） | 100% | 缺答 → partial |
| "已修改"声明与锚点对应率 | 100% | >0 失配必须修复 |
| changes.json before 在原稿可检索 | 100% | 失配 → 修定位 |
| 不采纳意见理由充分性 | 每条含可查证依据 | 空话理由 → 重写 |
| 回复信语气违例（冒犯/过度承诺） | 0 | 发现即改 |

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 意见互相冲突 | 两案并陈，给推荐方案，标 manual_review |
| 意见本身有误（审稿人误解） | 引原文澄清，礼貌反驳档，不硬顶 |
| 意见引用稿件不存在的章节 | anomalies 记录 + 回复信说明版本差异 |
| 无法补实验/数据 | evidence.md 标无法补做+原因+替代论证；修订稿留 TODO-E 锚 |
| 稿件缺章节 | 不臆造章节；回复信说明该意见暂无法落实 |
| 多轮返修承诺失效 | commitments.json 标 broken，回复信首段说明 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 字段全覆盖
- [ ] comments/decisions/changes/letter 四者 ID 贯通
- [ ] 每处"已修改"= 锚点+章节+锚文本三要素
- [ ] TODO-E 与 evidence.md 一一对应
- [ ] 冲突/误解/无法补做项均在对应字段显式标注
- [ ] 只改了指定基线，未动材料外内容
- [ ] checks.json 全 pass 或 fail 项已修复说明

## 8. 效率约束

- 64 请求/900 秒：Step1-2 合并 1-2 次调用；修订稿与回复信按意见分批产出；先落最小 result.json。
- ≤50 文件、单文件 ≤500KB、总量 ≤2MB；Office 交付附渲染预览。

## 9. 最小示例（示意输出，非正式案例结果）

输入：意见摘要 R1（3条）+ manuscript-baseline.md。
R1.2"补充基线特征描述" → 决策采纳 → 修订稿 §3.2 增句 `<!--CHG-3-->` → 回复信："已在修订稿 §3.2 第2段（锚：'基线特征'，CHG-3）补充…" → check_rebuttal.py：锚存在/before可检索/覆盖100% → result.json status=completed。
