---
name: proposal-writer
description: |
  开题报告与研究计划书写作 Skill：从课题指南、前期数据、文献等固定材料出发，
  按"研究背景-问题定义-目标-技术路线-阶段计划-风险-预期成果"七要素生成
  开题方案，先大纲后成稿，论断-证据-引用逐一绑定来源，预算周期/经费/数据/
  人员约束校验，材料外内容标 unverifiable，全程留痕可复核。离线运行，
  不编造文献与数据。
---

# 开题报告与研究计划书 Skill

## 1. 用途与适用范围

- 用途：把课题指南、前期数据、文献摘要、组内讨论等材料写成一份七要素齐全、与给定周期/经费/数据/人员条件相容的开题报告或研究计划书。
- 适用：硕博开题、基金申请书主体（研究方案部分）、院内立项报告；Markdown 与 docx 交付。
- 不适用：没有给出任何研究材料的纯空想选题（返回 status=failed）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：记录 `case_id`（原样保留）、`output_contract` 全部字段、材料清单与路径。
2. 读 `/input/task.md`：任务说明、体裁、受众、周期/经费/数据/人员约束、字数要求。
3. 逐个打开材料文件（docx/pdf/md/csv 均用实际文件内容，不凭文件名猜内容）。
4. 建立 `/app/work/inventory.md` 材料清单：每份材料一行 → 路径 | 类型 | 可提取的关键约束（周期、经费上限、已有数据、硬性指标）。
5. 材料缺失或无法读取 → 仍产出 result.json，`status=failed`，`missing_inputs` 列明缺失项，不虚构。

## 3. 工作流程（6 步流水线）

### Step 1 约束抽取 → /app/work/constraints.json
- 从材料抽取硬约束：周期（起止/总时长）、经费上限、数据可得性、人员、必须使用的平台/设备、伦理要求。
- 每条约束带 `source`（材料路径+定位：页码/段落）。
- 验收：每条约束可回溯；无来源的约束不得进入。

### Step 2 缺口陈述 → /app/work/gap.md
- 把材料整理成"已知—未知—待验证"三栏：已知（带材料出处）｜未知（研究缺口）｜待验证（可证伪的问题）。
- 研究问题收敛为 1-3 个，每个必须：具体（有对象/变量）、可证伪（有判定标准）、指向缺口（引用 Step 2 已知项）。
- 验收：每个研究问题能指回至少 1 条"未知"或"待验证"条目；写不出则降级为 partial 并标注。

### Step 3 大纲先行 → /app/work/outline.md
- 固定七要素骨架：1 研究背景与意义 / 2 研究问题与目标 / 3 技术路线 / 4 阶段计划 / 5 风险与备选 / 6 预期成果与考核 / 7 参考文献。
- 每节写：论证任务、需要的证据（指向材料）、字数预算。字数预算总和 = 任务要求字数（无要求则默认 6000±10%）。
- 目标-路线-验证-成果对齐表：每个研究问题一行，四列分别为目标、技术路线步骤、验证方式（指标/样本/对照/时间点）、预期成果。不允许空格。
- 验收：七节齐全；对齐表无空格；字数预算总和达标。

### Step 4 逐节成稿 → /app/work/proposal.md
- 按大纲逐节写，论断句末带 `[来源: 材料路径#定位]`；引用文献带 `[Ref-编号]`，与参考文献表一一对应。
- 技术路线拆成有输入/输出/前后依赖的步骤，标注关键路径与可并行项；阶段计划落到季度或月份，里程碑配任务量。
- 风险按 数据获取/方法可行性/进度/伦理合规 分类，每条含：触发信号、影响范围、备选方案、决策时点。
- 预期成果必须给可考核方式（指标阈值+依据）。
- 验收：正文每节字数落在预算 ±30% 内；无来源论断数为 0（脚本核对）。

### Step 5 计划可行性校验 → scripts/check_proposal.py
- 运行 `python3 scripts/check_proposal.py /app/work/proposal.md /app/work/constraints.json`，核对：
  - 阶段计划时间跨度 ≤ 给定周期；
  - 七要素标题齐全；
  - `[来源: ...]` 与 `[Ref-n]` 格式合法、无悬空引用（正文引用了不存在的 Ref）；
  - 预算金额合计 ≤ 经费上限（若材料给出）。
- 输出 `checks.json`；任何 fail 项回 Step 4 修复后再跑，最多 2 轮。

### Step 6 交付与留痕 → /app/output/
- `result.json`（§4 全字段）、`proposal.md`、`checks.json`、`references.md`（引用清单）。
- 引用对账：references.md 每条 → 正文引用位置列表；正文每个 [Ref-n] → references.md 条目，双向对齐。
- 产出 `evidence-map.json`：论断 → 来源/引用映射，供评分人逐条复核。

## 4. 输出契约（result.json 逐字段）

以 `/input/case.json` 的 `output_contract` 为准，全部字段必须落实；通用骨架如下：

```json
{
  "case_id": "<原样保留>",
  "status": "completed | partial | failed",
  "deliverables": {
    "proposal_markdown": "/app/output/proposal.md",
    "references": "/app/output/references.md",
    "outline": "/app/work/outline.md",
    "evidence_map": "/app/output/evidence-map.json"
  },
  "fact_source_map": [
    {"claim": "前期数据显示X", "source": "materials/xxx.pdf#p3", "ref_id": "Ref-1"}
  ],
  "version_and_boundaries": {
    "change_records": ["新增2.2节：因指南要求..."],
    "manual_review_items": ["经费明细需财务确认"],
    "material_gaps": ["未提供预实验数据，1.3节缺口陈述降级为推断"],
    "anomalies": []
  },
  "uncertainty": [
    {"item": "样本量估算依赖假设效应量d=0.5", "basis": "材料p4", "level": "medium"}
  ],
  "summary": {"n_research_questions": 2, "n_risks": 5, "n_milestones": 4, "word_count": 6120}
}
```

- `status=partial` 时必须写明哪些要素降级及原因；`failed` 时写明 `missing_inputs`。

## 5. 数字门槛

| 门槛 | 值 | 不达标处理 |
|---|---|---|
| 七要素齐全 | 7/7 | 缺 1 项 → partial |
| 研究问题数 | 1-3 | 0 个 → failed；>3 收敛 |
| 论断来源覆盖率 | 100% 关键论断 | <90% → partial |
| 悬空引用数 | 0 | >0 必须修复 |
| 阶段周期 | ≤ 给定周期 | 超出即改排或标 partial |
| 字数 | 任务要求 ±10%（默认 6000±10%） | 偏差 >30% → partial |
| 风险条目 | ≥4 类各至少 1 条 | 缺类 → 该节 partial |

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 无课题指南/无周期经费信息 | 不臆测；result.json 标 manual_review_items，周期按材料内默认值并标注 |
| 指标不可达（如周期内需完成明显超量的实验） | 保留但降级说明 + 提出分阶段可行替代，标 manual_review |
| 学科规范冲突（两种格式要求矛盾） | 记入 anomalies，采用更严格者，标冲突点 |
| 引用无法获取全文 | 仅引用材料内已有文献条目；材料外文献标 unverifiable，不编造 DOI/年份 |
| 材料互相冲突 | 两说并存、分别标来源，写入 manual_review_items |
| 材料超长（>200页） | 优先抽取：指南约束、前期数据、结论、方法可用部分，inventory.md 记录抽样策略 |

## 7. 自查清单

- [ ] case_id 原样出现在 result.json
- [ ] output_contract 每个字段都有对应值
- [ ] 七要素标题齐全、顺序正确
- [ ] 目标-路线-验证-成果对齐表无空格
- [ ] 每条约束/论断带材料定位；无材料外事实
- [ ] references.md 与正文 [Ref-n] 双向对账为 0 差异
- [ ] checks.json 全 pass（或 fail 项已说明）
- [ ] 周期/经费不超约束，超了已标注
- [ ] status 与实际一致，partial/failed 写明原因

## 8. 效率约束

- 预算 64 请求 / 900 秒：Step 0-3 合并 2-3 次调用完成；成稿按大纲分节批量写，避免一节一调。
- 先落最小 result.json（status+deliverables），再逐步充实，保证中断有可评分产物。
- 文件数 ≤50、单文件 ≤500KB、总量 ≤2MB；不写符号链接。

## 9. 最小示例（示意输出，非正式案例结果）

输入：指南要求"两年周期、经费≤80万"，材料含前期 12 例临床数据。
流程：constraints.json 记录 {period_months:24, budget_max:800000, data:"12例随访"} → gap.md 已知栏含"12例初步安全性(p3)" → outline 七节预算 800/900/1400/900/800/700/500 → 成稿 → check_proposal.py 全 pass → result.json status=completed，fact_source_map 12 条。
