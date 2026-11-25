---
name: structured-conclusion-data-extraction
description: |
  文献结论与数据提取 Skill：把论文中散落在正文、表格、图注与补充材料里的结论、实验条件、
  关键指标与数值点，按统一字段表还原为可核对、可复用的结构化结果。
  方法主线：读 /input/target-fields.json 的字段清单 → 逐字段回到原文定位 → 逐字抽取并绑定
  单位/统计量/实验条件/比较基线/段落定位 → 按 reported/not_reported/source_conflict/extraction_failed
  四态落盘 → 脚本校验引文与覆盖。全程离线、如实约束：猜的值不是抽取，缺的字段不是零，
  每个字段都能回到 paragraph_id 与逐字 quote，无法判断如实标注，不编造。
---

# 结构化结论与数据抽取 Skill（structured-conclusion-data-extraction）

## 1. 用途与适用范围

- 用途：给定一篇（或多篇）带段落定位的科研论文文本与一份目标字段表，输出逐字段的抽取结果：字段值、单位、统计量、实验条件、比较基线、原文定位与抽取状态。
- 适用：带文本层的论文全文/片段（含表格文字、图注、补充材料文字）；字段表形式的目标清单（`target-fields.json`）。
- 不适用/降级：扫描件无文本层（status=extraction_failed，登记原因）；图片型表格（登记为 unavailable-source，不猜数值）。
- 核心原则：**一个猜出来的值不是抽取；一个缺失的字段不是零；一段字面引文匹配不等于语义正确。**

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：提取 `case_id`（原样保留）、任务说明、材料清单、output_contract 全字段（逐字段抄录到 `/app/work/contract-checklist.md`，缺字段就是缺口）。
2. 读 `/input/target-fields.json`：这是抽取的"工单"。逐条列出全部 `field_id` 与其描述/期望类型，作为唯一抽取范围。文件缺失 → result.json 写 `status="partial"` 并说明字段表缺失，转为按任务说明中的显式字段抽取。
3. 盘点材料：正文段落、表格文字、图注、补充材料、参考文献，逐个登记路径/来源 ID。材料全部缺失 → `status="failed"`，不虚构。
4. 建目录：`/app/work/`（过程产物）、`/app/output/`（最终 result.json）。

## 3. 工作流程（6 步流水线）

### Step 1 字段表展开（产出 work/field-plan.json）
- 对每个 field_id 写一行计划：字段名、去哪些来源找（正文/表格/图注/补充材料）、期望值类型。
- 验收断言：field-plan 的 field_id 集合 == target-fields 的 field_id 集合。

### Step 2 来源通读与索引（产出 work/source-index.json）
- 按来源逐篇通读，登记每个段落/表格/图注的定位键（paragraph_id、表格号-行列、图注号、补充材料节号）。
- 对候选命中区域做关键词索引（字段名同义词、单位符号、统计量词如 mean/SD/p-value/n=%）。
- 验收断言：每份材料至少有一条索引记录；空材料登记 empty。

### Step 3 逐字段抽取（产出 work/field-extracts.json）
每个字段一条记录，规则：
- **值**：逐字取自原文，不改写、不合并、不换算。范围值保留原样（如 "10–20 mg/L"）。
- **单位**：随值绑定；原文无单位 → units=null 并在该字段 uncertainty 注明 "unit not reported"。
- **统计量**：保留 mean±SD、95%CI、p 值、样本量 n 等原文写法。
- **实验条件**：该值成立的前提（样本、设置、数据来源、时间点、比较基线），从同段或紧邻段落的条件句提取；条件与数值必须同源绑定，不允许脱钩单列。
- **比较基线**：comparator（相对谁/相对什么），原文未给 → null。
- **定位**：paragraph_id 必填（表格给 表号+行列，图注给图号）。
- **引文**：quote 为包含该值的**逐字**短引文（≤2 句），保证在源文本中子串可匹配。
- 验收断言：每个 field_id 恰好一条抽取记录。

### Step 4 状态判定（四态，逐字段）
- `reported`：原文明确报告该字段 → 正常填值。
- `not_reported`：通读全部指定来源后确实没有 → status=not_reported，value=null，**不填 0、不用领域常识补**。
- `source_conflict`：多来源（正文 vs 表格 vs 补充材料）给出不同值 → 两条取值+两处定位都保留，status=source_conflict，在 notes 写冲突内容，不仲裁。
- `extraction_failed`：来源存在但无法解析（跨页断裂、合并单元格无法还原、图像表格无文本层）→ 登记具体原因。
- 验收断言：状态枚举合法；not_reported/extraction_failed 必须给出检索过哪些来源的说明。

### Step 5 校验（运行 scripts/validate_extraction.py）
```bash
python3 /skills/weekly-skill/scripts/validate_extraction.py \
  --result /app/output/result.json --fields /input/target-fields.json \
  --source-dir <材料目录> [--source-json /app/work/source-index.json]
```
校验项：① field_id 全覆盖无多余；② status 枚举合法；③ reported 字段 quote 非空且能在来源文本中子串匹配；④ value 与 units 与 quote 同现。失败项修回 Step 3/4 再校验。

### Step 6 落盘（/app/output/result.json）
- 先写最小可用骨架（case_id + status + 各字段四态占位），再逐步充实——任何中断都有可评分产物。

## 4. 输出契约（result.json 逐字段）

| 字段 | 要求 |
|---|---|
| `case_id` | 与 /input/case.json 原样一致 |
| `status` | `success` / `partial` / `failed`（材料全缺失或字段表无法读取） |
| `fields[]` | 每个 field_id 一项，见下 |
| `fields[].field_id` | 与 target-fields.json 一致 |
| `fields[].status` | `reported` / `not_reported` / `source_conflict` / `extraction_failed` |
| `fields[].value` | 逐字值（含范围写法）；无值时 null |
| `fields[].units` | 原文单位；未报告 null |
| `fields[].statistic` | 统计量写法（mean±SD/95%CI/p/n），无则 null |
| `fields[].experimental_condition` | 该值成立条件（样本/设置/来源/时间点），无则 null |
| `fields[].comparator` | 比较基线，无则 null |
| `fields[].source` | 命中来源（body/table/figure/supplement）+ 定位 |
| `fields[].paragraph_id` | 原文段落定位键 |
| `fields[].quote` | 逐字短引文（not_reported 时 null） |
| `fields[].conflicts[]` | source_conflict 时：每个来源的 value+paragraph_id+quote |
| `fields[].notes` | 抽取口径说明/失败原因 |
| `uncertainty[]` | 全局不确定项（单位缺失、条件句缺失、跨页表格等） |
| `change_log[]` | 修订记录（谁改的、改什么、依据） |

示例（示意，非正式案例结果）：
```json
{
  "case_id": "demo-001",
  "status": "success",
  "fields": [
    {"field_id": "removal_efficiency",
     "status": "reported",
     "value": "94.2 ± 1.8",
     "units": "%",
     "statistic": "mean ± SD, n=3",
     "experimental_condition": "pH 7, 25 °C, initial concentration 50 mg/L, contact time 120 min",
     "comparator": "vs. raw biochar without Fe modification",
     "source": "body paragraph",
     "paragraph_id": "p12",
     "quote": "The Fe-modified biochar achieved a removal efficiency of 94.2 ± 1.8% under pH 7.",
     "conflicts": [], "notes": "值与单位逐字取自 p12；条件来自同句与 p11 实验设置段。"}
  ],
  "uncertainty": [],
  "change_log": []
}
```

## 5. 数字门槛

- 覆盖率：fields[] 必须覆盖 100% 的 field_id，不许多也不许少；达不到 → status=partial。
- 引文可核验率：reported 字段的 quote 必须在源文本子串匹配，匹配率 <100% 不得提交。
- 定位粒度：paragraph_id 必填到段落级（表格到表+行列），只给"在第3节"不合格。
- 四态诚实：not_reported 数量不为羞耻，把没有写成有才是失败。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| target-fields.json 缺失 | status=partial，按任务说明显式字段抽取，登记缺口 |
| 材料全部缺失 | status=failed，不虚构 |
| 扫描件/无文本层 | 该字段 extraction_failed，原因=source has no text layer |
| 表格跨页/合并单元格 | 尝试按表头对齐还原；失败则 extraction_failed 并登记断裂位置 |
| 正文与表格数值冲突 | source_conflict，双值双定位，不仲裁 |
| "未报告/ND/not detected" | 不是 0：value 保留原文写法，notes 注明语义 |
| 数值出现在多处且一致 | 取一处定位 + notes 注明 also reported at X |
| 材料含错误领域标签 | 以实际输入文件内容为准，不按标签补造数据 |

## 7. 自查清单

- [ ] case_id 原样保留
- [ ] field_id 100% 覆盖，无多余字段
- [ ] 每个 reported 字段有 paragraph_id + 逐字 quote，且 quote 子串匹配通过
- [ ] 单位、统计量、条件、基线随值绑定，无脱钩
- [ ] not_reported ≠ 0，未用常识补值
- [ ] 冲突双保留，未擅自仲裁
- [ ] validate_extraction.py 全项通过
- [ ] change_log 记录所有修订

## 8. 效率约束

预算 64 请求/900 秒内：Step 2 通读一次成型，不反复重读；抽取按字段批量写；先落骨架再充实；脚本校验一次跑通后仅复跑失败项。

## 9. 最小示例

输入（示意）：
- target-fields.json：`[{"field_id": "bandgap", "type": "scalar", "unit_hint": "eV"}]`
- 材料：`p03: The as-prepared sample showed an optical band gap of 2.31 eV, lower than that of the pristine counterpart (2.55 eV).`

输出（示意，标明为示例）：
```json
{"case_id":"demo-002","status":"success","fields":[
  {"field_id":"bandgap","status":"reported","value":"2.31","units":"eV",
   "statistic":null,
   "experimental_condition":"as-prepared sample, vs. pristine counterpart (2.55 eV)",
   "comparator":"pristine counterpart","source":"body","paragraph_id":"p03",
   "quote":"an optical band gap of 2.31 eV, lower than that of the pristine counterpart (2.55 eV)",
   "conflicts":[],"notes":"同一句内含比较基线，comparator 直接取自原文。"}],
 "uncertainty":[],"change_log":[]}
```
