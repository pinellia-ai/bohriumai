---
name: methods-stats-audit
description: |
  研究方法与统计审查：对固定论文走完"研究设计—变量定义—统计方法—样本量—结果报告"五个检查面，
  交付可交给作者逐条回复的审查单（定位、缺陷类型、严重度、依据、修改建议）。
  关键区分："方法本身有缺陷(method_flaw)"与"方法可接受但报告不全(reporting_gap)"严格分开；
  每条意见落到稿件具体位置（file+locator+逐字quote），无法确认标 pending，不凭空补结论。
---

# 研究方法与统计审查 — 五面对账执行版 Skill（v1）

## 1. 用途与适用范围

- 适用：对论文/科研材料完成研究设计、变量定义、统计方法、样本量与检验效能、结果报告五面审查，产出一份能交给作者逐条回复的审查单。
- 不适用：文献检索与综述、全文翻译、语言润色、代写审稿结论、投稿决策、原始数据重分析。
- 判断做对的三问：每条意见能否落回稿件原文具体位置；严重度是否与缺陷性质匹配（不一律"重大缺陷"）；复核人能否按记录独立重跑得到同一份审查单。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id` 原样保留；`output_contract` 全字段逐条落实，冲突以 case.json 为准。
2. 读 `/input/task.md`：确认审查范围、报告语言、是否限定章节。
3. `ls -la /input/` 盘点材料；缺失 → status=failed + failure_reason；统计输出、表格若单独成文件，登记到 sources。

## 3. 工作流程（七步流水线）

### Step 1 材料装载与定位器（→ /app/work/paragraphs.csv, tables.csv）

- `python3 scripts/make_locators.py /input/<材料> --outdir /app/work` 生成段落定位器 P001…。
- 表格单独登记 tables.csv：{table_id, locator, caption 逐字, 列名清单}，供结果报告核对。
- 验收：段落数 >0；失败面记 run_log.md。

### Step 2 研究设计画像（→ design_profile.json）

- 先客观登记再判断：{design_type 观察性/RCT/准实验/横断面/队列等, research_question, primary_endpoint, control_setting, grouping, blinding, randomization}——每项取自原文具体段落并记 locator；原文未写 → 记 `not_reported`，**不猜设计**。
- 验收：每项有 locator 或显式 not_reported。

### Step 3 五检查面逐条扫描（→ findings.json）

| facet | 必查点 |
|---|---|
| research_design | 设计类型与研究问题是否匹配；对照设置、分组方式、盲法与偏倚控制是否成立；主要终点与假设是否事先明确 |
| variable_definition | 暴露/结局/协变量/分组变量的定义、测量、编码是否一致；分类切点、单位换算、缺失值处理有无依据；变量类型与统计模型是否匹配 |
| statistical_method | 检验方法与数据结构、分布假设、样本独立性是否匹配；多重比较、重复测量、交互项、敏感性分析是否正确处理 |
| sample_size_power | 样本量估算依据、效应量来源、alpha 与把握度是否报告且合理；实际入组与估算量、失访与剔除的处理 |
| results_report | 效应量与置信区间、精确 p 值、统计量与自由度；图表与正文数值一致；是否满足对应报告规范要求 |

- **每条 finding 八件**：`id`、`category`（六类之一，见 §4）、`facet`（上表五面之一）、`location{file,locator,quote}`、`flaw_class`、`severity`、`evidence`、`recommendation`。
- **flaw_class 二分（本题核心区分）**：
  - `method_flaw` 方法本身有缺陷：做法存在且错误（如对独立样本用配对检验、切点无依据）。
  - `reporting_gap` 报告不全：做法可能可接受但未交代（如未说明随机化方式、未报精确 p 值）。
  - 混淆二者即验收失败；原文根本没写的统计要素一律 reporting_gap。
- severity 三级：`major`（动摇主结论/方法硬伤）、`minor`（局部或可修正）、`suggestion`（锦上添花）。判 major 必须在 evidence 写明"影响主结论的路径"。
- 验收：每条八件齐全；quote 逐字；`python3 scripts/audit_check.py` 退出码 0。

### Step 4 图表-正文数值对账（→ numbers_check.csv）

- 逐个表格/图注与正文陈述对照：样本量、百分比、p 值、CI 端点。每行 {table_id, item, in_table, in_text, match, locator}。
- 验收：tables.csv 每表至少核对 2 项或标 na（图无法读取时记 pending）。

### Step 5 报告规范映射（→ checklist_map.csv）

- 按稿件体裁选对应报告规范条目（RCT→CONSORT 式条目、观察性→STROBE 式条目、无明确体裁→通用统计报告条目）逐条映射：{item, status: met|missing|na, locator}。
- **只映射条目名与状态，不虚构规范条款原文**；条目集内置于 scripts/standards_items.json，来源在 README 注明。

### Step 6 覆盖对账（→ coverage.json）

- 双维覆盖：五 facet 各记 {checked, items_scanned, findings_count, pending_count, na}；六类 category（事实核验、引用支持、方法设计、统计报告、论证链、学术规范）各记 checked/findings_count。
- 验收：五 facet + 六类全部出现，无 null。

### Step 7 result.json + run_log.md

- Step 2 完成后落盘最小 result.json（status=partial），七步走完充实。
- run_log.md 逐记录时间/命令/输入/输出/计数。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "status": "success | partial | failed",
  "deliverables": {"design_profile": "design_profile.json", "findings": "findings.json", "numbers_check": "numbers_check.csv", "checklist_map": "checklist_map.csv", "coverage": "coverage.json", "run_log": "run_log.md"},
  "review_report": {"findings_total": 0, "by_severity": {"major": 0, "minor": 0, "suggestion": 0, "pending_review": 0}, "by_flaw_class": {"method_flaw": 0, "reporting_gap": 0}, "top_issues": []},
  "evidence_and_boundary": {"quotation_policy": "quote 逐字", "pending_review": [], "unchecked": []},
  "coverage": {"research_design": 0, "variable_definition": 0, "statistical_method": 0, "sample_size_power": 0, "results_report": 0, "fact_verification": 0, "citation_support": 0, "method_design": 0, "statistical_reporting": 0, "argument_chain": 0, "academic_norm": 0},
  "sources": [], "uncertainty_notes": [], "change_log": []
}
```

以 case.json `output_contract` 为最高优先补齐。

## 5. 数字门槛

1. design_profile 每项有 locator 或 not_reported。
2. findings 每条八件齐全，quote 非空（validator 强制）。
3. flaw_class 二分不混淆：原文未写的统计要素不得判 method_flaw。
4. 五 facet + 六类 coverage 全出现。
5. major 判定必附"影响主结论的路径"。
6. numbers_check 每表 ≥2 项或 na+原因。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 稿件缺方法节/缺页 | 对应 facet 标 unchecked，result=partial，列出缺什么 |
| 统计输出缺失 | results_report 相关条目 reporting_gap，不猜数值 |
| 图表无法解析 | numbers_check 该表 pending；不猜内容 |
| 扫描件识别失败 | 降级链如实记录，可解析部分照跑 |
| 体裁不明 | 用通用统计报告条目并在 run_log 注明 |
| 材料不足以判断 | finding=pending_review 写缺什么证据 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 全覆盖
- [ ] 五 facet 全走完，六类 coverage 齐
- [ ] 每条 finding 有 file+locator+quote，flaw_class 用对
- [ ] 无"一律 major"；major 有影响路径
- [ ] audit_check.py 退出码 0
- [ ] run_log.md 完整

## 8. 效率约束

Step 1/4/5 脚本化；扫描按 facet 分批；先落盘后充实；不复述全文。≤50 文件 / 500KB / 2MB。

## 9. 最小示例（示意输出，非正式案例结果）

findings.json 片段：

```json
{"id":"F001","category":"statistical_reporting","facet":"statistical_method","location":{"file":"manuscript.pdf","locator":"P018 (§2.4)","quote":"A paired t-test was used to compare the two independent groups"},"issue_type":"fact_error","severity":"major","flaw_class":"method_flaw","evidence":"两组为独立受试者（P014 称 random assignment），配对检验误用；影响主结论的路径：主结局p值与检验方法直接绑定","recommendation":"改用两独立样本 t 检验（或 Wilcoxon 秩和检验）并重算"}
```

coverage.json 片段：`{"research_design":{"checked":true,"findings_count":0},"variable_definition":{"checked":true,"findings_count":0},"statistical_method":{"checked":true,"findings_count":1},"sample_size_power":{"checked":true,"na":false},"results_report":{"checked":true,"pending_count":1}}`
