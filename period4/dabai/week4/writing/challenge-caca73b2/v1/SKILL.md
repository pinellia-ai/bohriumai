---
name: results-discussion-writing
description: |
  结果与讨论章节写作 Skill。把"数据在手、图表画好"的原始材料写成可投稿的结果段与讨论段：图表数值可靠读入（数值/单位/误差棒/统计量，不猜）、结果段只写观察到的事实、讨论段逐条对应本研究数据或具体文献、因果边界区分相关/预测/因果、局限写到方法样本测量统计层面。离线运行：每个数值回溯到某图/某表/某份统计输出并带位置（文件/页/图表号），材料里没有的数值和文献不编造，缺项如实标 gap。
---

# 结果与讨论章节写作（图表读入 → 数值台账 → 结果/讨论分节 → 证据对照）

## 1. 用途与适用范围

- 用途：把给定数据表/图/图注/统计输出变成可编辑、可提交的结果与讨论章节。
- 适用：实验类、数值分析类论文章节写作；不适合作图本身（图表已给定）。
- 四大考察点：读得准（图表读数正确写进正文）、分得清（结果=事实，讨论=解释）、说得住（表述强度与证据匹配）、核得了（数值回溯、论断对应文献）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id` 原样保留、任务说明、材料路径、output_contract 全字段。
2. 读 `/input/task.md`：目标期刊风格、章节结构要求、是否要求双语/纯中文。
3. 读真实材料：数据表（CSV/表格）、图与图注（pdf-render 工具看图）、统计输出。**图上读数不确定（分辨率/标注不清）时标 uncertain，不猜。**
4. 盘点图表清单：`编号 | 类型 | 内容 | 数据来源 | 误差棒含义 | 可读取数值`。
5. 先落盘最小 `result.json`（status=partial 占位）。

## 3. 工作流程（七步流水线）

### Step 1 数值台账（产出 `numbers_ledger.json`）
从图/表/统计输出抽取每个可用数值：`ledger_id | 数值 | 单位 | 误差范围 | 误差棒含义（SD/SE/CI 依图注） | 来源位置（图表号+面板/行列）`。正文每个数值必须来自台账，台账外数值=编造。

### Step 2 发现清单（并入 results_outline.md）
列出原始发现（含阴性结果与不一致数据，如实交代不回避），每条关联 ledger_id 与图表号，排序按图序或问题主线（依 task.md）。

### Step 3 结果段写作（产出 `results_section.md`）
- 只陈述观察到的事实：方向、幅度、显著性；不解释、不展望。
- 数值写法：与台账逐字一致，有效位数同源；"趋势一致但未达显著""仅在高剂量组出现"一类有边界的写法如实使用。
- 每段引用对应图表（Fig. X / Table Y），段末附 ledger 引用注释。

### Step 4 讨论段写作（产出 `discussion_section.md`）
- 每条论断对应：本研究数据（ledger_id）或具体文献（材料内文献+定位）。堆引用不讲关系的写法禁止。
- 证据对照三式：与文献一致 / 不一致（写出可能原因，标 speculation）/ 补充了文献没覆盖的情形。
- 因果边界：相关/预测/因果三词严格区分；机制推测显式标注"我们推测（speculative）"。
- 局限：写到方法、样本、测量、统计四个层面各至少一句（材料支持什么写什么，材料没有的不虚构局限，也不写空话）。

### Step 5 证据回溯表（产出 `evidence_trace.md`）
`正文位置 | 数值或论断 | 来源（ledger_id/文献+位置）`，核得了的落地文件。

### Step 6 校验
跑 `scripts/check_results.py`（§6）：正文数值↔台账比对、图表引用编号存在性、结果/讨论越界检查（结果段出现解释词报警）。

### Step 7 汇总 result.json

## 4. 输出契约（result.json 逐字段）

```json
{
  "case_id": "<原样保留>",
  "status": "success | partial | failed",
  "deliverable": {
    "results_section": "/app/output/results_section.md",
    "discussion_section": "/app/output/discussion_section.md",
    "numbers_ledger": "numbers_ledger.json",
    "evidence_trace": "evidence_trace.md"
  },
  "facts_sources": [
    {"item": "28.4 ± 1.2 mg/L", "source_location": "Fig.2B 误差棒为SE, Table1 row3", "manuscript_location": "results §2 para.1", "action": "read_from_chart"}
  ],
  "claims": [
    {"claim_id": "D-03", "text": "与 Smith 2020 报告的趋势一致", "support": "文献 smith2020.pdf p.4 + 本研究结果段2", "strength": "supported", "speculative": false}
  ],
  "changes": [
    {"location": "discussion §3", "before": "机制推测写成因果结论", "after": "加'我们推测'限定", "reason": "因果边界守卫"}
  ],
  "uncertainty": [{"item": "Fig.3C 数值", "issue": "图分辨率不足读数不确定", "resolution": "该值未写入正文", "needs_human_confirm": true}],
  "gaps": ["Table 2 统计输出未提供 p 值，结果段只报方向不报显著性"],
  "limits": ["阴性结果（组5无显著差异）已如实写入 results §4"],
  "reproduce": "按 README 步骤可复现"
}
```

硬性要求：`facts_sources` 覆盖正文全部数值；`claims` 覆盖讨论段全部实质性论断；台账外数值=0；uncertainty 记录读数不确定项。

## 5. 数字门槛（达不到如实标 partial）

- 数值保真：正文每个数值在台账可指认（脚本比对），台账外=FAIL。
- 图表引用：正文引用的每个图表号在图表清单中存在，否则 FAIL。
- 分节纪律：结果段出现"表明/说明/由于"等解释词 → 警告并人工移到讨论。
- 论断支撑：讨论段论断 100% 有 support（数据 ledger_id 或文献+位置），无支撑论断=FAIL 或降级为 speculation。

## 6. 校验脚本

捆绑 `scripts/check_results.py`（纯标准库）：输入 `ledger.json`（台账数值）+ `manuscript_numbers.json`（正文数值）+ `figure_refs.json`（清单图表号 vs 正文引用），输出 NUM/FIG/CROSSING 报告。先最小样例实跑再正式使用。

## 7. 异常处理表

| 异常 | 处置 |
|---|---|
| 缺图/缺统计量 | gaps 记录，对应论断降级或略去，不编数值 |
| 单位不明 | uncertainty 标注，正文保留原单位表达，needs_human_confirm |
| 图表读数不清 | 不猜；标 uncertain，该值不写入正文 |
| 引用找不到（文献不在材料内） | 论断降级为"未核实"或删除，不编文献 |
| 结果与讨论内容混合 | 按 §5 分节纪律拆分并在 change_log 记录移动 |
| 阴性结果 | 如实写入结果段，不得为叙事抹掉 |

## 8. 效率约束

预算 64 请求 / 900 秒：Step 0-1 前 10 请求（读图表占大头，pdf-render 按需渲染）；先落最小 result.json。≤50 文件 / 2MB。

## 9. 最小示例（示意，非正式案例结果）

输入：Table1（浓度数据）+ Fig.2（剂量响应）+ 统计输出.txt。
示意输出：ledger 14 条；结果段 3 段（含 1 条阴性结果）；讨论段 2 段（1 处文献对照+1 处推测标注）；evidence_trace 11 行；result.json status=success。

## 10. 命令序列

```
1. cat /input/case.json → 最小 result.json
2. 图表清单+numbers_ledger.json（误差棒含义依图注）
3. 发现清单（含阴性结果）→ results_outline.md
4. results_section.md（只写事实）→ discussion_section.md（数据/文献对照+因果边界）
5. evidence_trace.md
6. python3 scripts/check_results.py ledger.json manuscript_numbers.json figure_refs.json
7. 修 FAIL → result.json 定稿
```

## 11. 自查清单（交前全过）

- [ ] YAML frontmatter 可解析
- [ ] 正文数值 100% 回溯台账/图表位置
- [ ] 结果段只写事实；讨论段论断 100% 有 support
- [ ] 阴性结果与局限如实；机制推测标注 speculative
- [ ] result.json 全字段落实（facts_sources/claims/changes/uncertainty/gaps/limits）
- [ ] 脚本 ast.parse + 最小实跑通过
- [ ] ≤50 文件 / 2MB
