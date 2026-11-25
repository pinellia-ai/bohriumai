---
name: norm-compliance-audit
description: |
  学术规范与合规检查：对固定材料按学术诚信、引用规范、隐私与数据合规、版权与许可、伦理审查、
  投稿要求六个风险面逐项检查。每条判定必须绑定可核对依据（规范条款/期刊指南条目/数据授权范围），
  依据取不到标 needs_review 不判违规；报不出具体条目的泛泛提醒与把风格差异判成不端的大面积误报同样禁止。
---

# 学术规范与合规检查 — 依据绑定执行版 Skill（v1）

## 1. 用途与适用范围

- 适用：投稿/结题/发布前把一份材料按学术规范过一遍，产出逐条合规问题清单：原文定位 + 判定 + 绑定依据 + 严重度 + 可执行建议。
- 不适用：论文写作润色、代写与代投稿、数据重新分析、实验方案设计、法务或伦理委员会正式意见。
- 做对三问：报出的问题成立并能指回原文位置；每条判定有可核对依据；他人能在同一材料上复跑出基本一致结论。**漏报与误报同等扣分。**

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id` 原样保留；`output_contract` 全字段逐条落实，冲突以 case.json 为准。
2. 读 `/input/task.md`：确认目标期刊/会议（如有）、检查范围、报告语言。目标期刊作者指南若在输入材料中，登记指南名称与版本/日期；**不在输入中的指南不虚构**。
3. `ls -la /input/` 盘点材料；缺失 → status=failed + failure_reason。

## 3. 工作流程（七步流水线）

### Step 1 材料装载与定位器（→ /app/work/paragraphs.csv, locators.json）

- `python3 scripts/make_locators.py /input/<材料> --outdir /app/work` 生成段落定位器 P001…。
- 单独登记声明区（声明/致谢/基金/伦理/利益冲突/数据可用性段，逐字摘录到 declarations.csv）。
- 验收：段落数 >0；失败面记 run_log.md。

### Step 2 依据源登记（→ basis_registry.json，本题核心前置）

- 盘点输入中全部可作为判定依据的材料：目标期刊作者指南条目、许可声明、数据授权说明、伦理批件信息、基金号。
- 每条依据 {basis_id, type: journal_guide|license|consent|policy|other, source_locator, 逐字摘录或条目名}。
- **依据源为空时不阻断检查**：仍可核对材料内部一致性，凡需外部条款的判定一律 needs_review。
- 验收：registry 每条有 source_locator；无依据面记录说明。

### Step 3 六风险面逐条扫描（→ findings.json）

| 风险面 | 必查点 |
|---|---|
| academic_integrity | 数据与图像复用迹象（同一图/数据两处不同结论）、重复发表迹象、致谢与基金信息不一致、利益冲突声明缺失 |
| citation_norm | 被引文献元数据与正文陈述是否一致（年份/作者/题名对不上）、引而不证、张冠李戴、格式不统一 |
| privacy_data | 可识别个人信息（姓名/病历号/照片/坐标）、受限数据与未公开数据的授权依据、脱敏建议 |
| copyright_license | 第三方图片/表格/代码/数据集的来源标注、许可类型与复用条件，指出需授权或替换的位置 |
| ethics_review | 涉人研究是否说明知情同意、伦理批件编号与适用范围；动物实验规范；风险与获益表述与设计一致性 |
| submission_requirements | 若有目标期刊指南：拆成条目逐条映射稿件（字数/图表数/结构/必需声明），报告缺失项、超限项、格式冲突，注明指南版本与日期 |

- **每条 finding 九件**：`id`、`category`（上表六面之一）、`location{file,locator,quote}`、`issue_type`（fact_error/insufficient_evidence/norm_issue/suggestion/pending_review）、`severity`（major=合规风险实质存在/将影响投稿或伦理合规；minor=局部规范问题；suggestion=可选优化）、`basis_ref`（绑定的 basis_id + 依据原文摘录；依据取不到 → 必须标 `needs_review:true` 且 severity 降为待复核，**不得凭记忆引用条款编号**）、`evidence`、`recommendation`（可执行：脱敏怎么改、补什么声明、替换哪个图）。
- **误报抑制**：风格差异、学科惯例、个人表述习惯不判违规；"建议检查参考文献格式"这类无定位无依据的泛泛提醒禁止出现；不编造期刊要求、条款或文献元数据。
- 验收：每条九件齐全；`python3 scripts/audit_check.py` 退出码 0。

### Step 4 声明区对账（→ declarations_check.csv）

- 逐项核对：利益冲突声明 / 数据可用性声明 / 伦理批件与知情同意 / 基金与致谢一致性 / 作者贡献与署名。每行 {item, status: present|missing|inconsistent, locator, quote, note}。
- missing 不自动判 major：按材料语境与 basis_registry 判，无依据时 needs_review。

### Step 5 投稿条目映射（→ submission_map.csv，仅当有指南）

- 每条指南条目 {guide_item(逐字), status: met|missing|violation|na, manuscript_locator, note}；无指南时跳过并在 coverage 标 na。

### Step 6 覆盖对账（→ coverage.json）

- 六风险面各记 {checked, items_scanned, findings_count, pass_count, pending_count, na}；六类通用检查项（事实核验、引用支持、方法设计、统计报告、论证链、学术规范）各记 checked/findings_count。
- 验收：两套键全部出现，无 null。

### Step 7 result.json + run_log.md

- Step 2 完成后落盘最小 result.json（partial）；七步走完充实。
- run_log.md 逐记录时间/命令/输入/输出/计数/降级。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "status": "success | partial | failed",
  "deliverables": {"basis_registry": "basis_registry.json", "declarations_check": "declarations_check.csv", "submission_map": "submission_map.csv", "findings": "findings.json", "coverage": "coverage.json", "run_log": "run_log.md"},
  "review_report": {"findings_total": 0, "by_severity": {"major": 0, "minor": 0, "suggestion": 0, "pending_review": 0}, "by_basis": {"bound": 0, "needs_review": 0}, "top_issues": []},
  "evidence_and_boundary": {"quotation_policy": "quote 逐字；依据摘录逐字", "pending_review": [], "unchecked": []},
  "coverage": {"academic_integrity": 0, "citation_norm": 0, "privacy_data": 0, "copyright_license": 0, "ethics_review": 0, "submission_requirements": 0, "fact_verification": 0, "citation_support": 0, "method_design": 0, "statistical_reporting": 0, "argument_chain": 0, "academic_norm": 0},
  "sources": [], "uncertainty_notes": [], "change_log": []
}
```

以 case.json `output_contract` 为最高优先补齐。

## 5. 数字门槛

1. findings 每条九件齐全，quote 非空（validator 强制）。
2. 无 basis_ref 的违规判定 = 验收失败；needs_review 条目写明"缺什么依据可定论"。
3. 六风险面 coverage 全出现；有指南时 submission_map 条目全覆盖。
4. declarations_check ≥5 行或材料无声明区的说明。
5. 无泛泛提醒（validator 拦截无 locator 的条目）。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 材料缺页/无法解析 | 降级链记录；对应面标 unchecked；result=partial |
| 引用信息不全 | citation_norm 相关条目 needs_review，不判张冠李戴 |
| 目标期刊指南缺失 | submission_requirements 标 na；不虚构期刊要求 |
| 材料涉及受限数据 | 只做脱敏建议，不复制扩散敏感内容；建议本身写进 recommendation |
| 依据条款取不到 | needs_review + 写明缺什么，severity=pending_review |
| 表述歧义 | uncertainty_notes 记录，不出双判定 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 全覆盖
- [ ] 每条 finding 有 file+locator+quote+basis_ref
- [ ] 无编造条款/期刊要求/文献元数据
- [ ] 风格差异未被误判为违规；无泛泛提醒
- [ ] 六面 coverage 齐；audit_check.py 退出码 0
- [ ] run_log.md 完整

## 8. 效率约束

Step 1/4/5 脚本化；六面分批扫描；单响应一类事务；先落盘后充实。≤50 文件 / 500KB / 2MB。

## 9. 最小示例（示意输出，非正式案例结果）

findings.json 片段：

```json
{"id":"F001","category":"privacy_data","location":{"file":"table2.pdf","locator":"P019","quote":"Patient #A-1023, male, 47yo, diagnosed 2019-03-12"},"issue_type":"norm_issue","severity":"major","basis_ref":"basis_registry.json:B001","needs_review":false,"evidence":"表2含可组合识别信息（编号+年龄+确诊月份），对照指南条目 G-privacy-2","recommendation":"删除编号或改用不可逆编码，并在方法注明脱敏方式"}
```

declarations_check.csv 片段：`item,status,locator,quote,note` + `data_availability,missing,,,全文未检索到数据可用性声明; 指南要求则补`
