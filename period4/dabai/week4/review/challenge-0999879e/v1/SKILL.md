---
name: paper-quality-audit
description: |
  论文质量审查：对固定论文/科研材料做结构完整性、事实一致性、引用支持、方法、统计、论证链与规范的全景审查，
  交付逐条可交办、可回查原文的问题清单（位置+原文摘录+类型+严重度+依据+修改建议），而非整篇评语。
  真实执行流水线：先落盘最小 result.json 再逐步充实；每条结论指到原文具体位置；
  无法确认的条目标 pending 复核，绝不凭空补结论、绝不虚构数据或文献。
---

# 论文质量审查 — 逐条对账执行版 Skill（v1）

## 1. 用途与适用范围

- 适用：给定一篇论文或科研材料（PDF/docx/txt/md/HTML），按检查项逐条审查，产出结构固定的问题清单，覆盖事实核验、引用支持、方法设计、统计报告、论证链、学术规范六类，以及整体结构与可发表性。
- 不适用（超出边界，不做也不报）：论文润色改写、语言翻译、查重比对、投稿排版、代写审稿结论、投稿决策。
- 产物形态：`result.json` + `findings.json`（逐条问题）+ `evidence.csv`（证据对账）+ `coverage.json`（检查项覆盖）+ `structure_check.csv`（结构盘点）+ `run_log.md`（执行留痕）。每条结论可指回原文位置，供第三方独立复核。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：提取 `case_id`（**原样保留，禁止改写**）与 `output_contract` 全部字段——result.json 必须逐字段落实；若 output_contract 有本节未列字段，以 case.json 为准补齐。
2. 读 `/input/task.md`：确认本次审查的动作动词（审查哪些面、报告什么语言）与交付要求；与本文冲突时以 task.md 为准并在 run_log.md 记录。
3. `ls -la /input/` 盘点材料：记录每个文件名、类型、大小。**只依据实际文件执行，不依据文件名/领域标签猜测内容。**
4. 材料缺失或为空 → result.json 写 `status=failed`、`failure_reason`，不虚构。部分缺失 → 正常部分照跑，缺失面标 `unchecked`。

## 3. 工作流程（六步流水线，每步留痕）

### Step 1 材料装载与定位器（→ /app/work/locators.json, /app/work/paragraphs.csv）

- 文本抽取顺序：`.txt/.md` 直接读；`.pdf` 先 `pdftotext -layout`（若可用），失败则尝试 Python pdf 库，再失败则按页记录"无法解析"并继续处理可解析部分；`.docx` 用 python-docx 或解压读 `word/document.xml`；HTML 剥标签。
- 将全文切成段落单元，生成稳定定位器：每段记 `para_id`（P001…）、所属章节、页码（如可得）、首句前 20 字。**所有后续定位一律用该 locator，不用模糊的"某节"。**
- 验收断言：paragraphs.csv 段落数 >0；locators.json 每条有 file+locator；抽取失败面记入 run_log.md。

### Step 2 结构盘点（→ structure_check.csv）

- 逐项检查：章节齐备性（题名/摘要/关键词/引言/方法/结果/讨论/结论/参考文献——按材料实际体裁裁剪）、层级合理性、摘要与正文对应、结论是否回应引言问题、图表编号与引用是否一致。
- 每行：{check_item, result: present|missing|inconsistent|na, location, note}。识别"结构看着完整但关键部分缺位"（如方法节只有一句带过）。
- 验收断言：行数 ≥ 8；每行有 location 或显式标 na。

### Step 3 六类检查项逐条扫描（→ findings.json, evidence.csv）

对下表逐类扫描，每类都要走完（没有问题也要在 coverage.json 记"checked, 0 findings"）：

| 类别 | 必查点 |
|---|---|
| fact_verification 事实核验 | 数据在摘要/正文/表格/图注中是否一致；术语与定义前后是否统一；正文事实性陈述内部是否自洽 |
| citation_support 引用支持 | 每处引用：正文论断与所引文献主张是否对应；识别"引用存在但不支持结论"、结论超出引文范围的过度推断 |
| method_design 方法设计 | 对照设置、样本量与抽样方式、随机化/盲法说明、评价指标选择是否有依据 |
| statistical_reporting 统计报告 | 显著性报告（精确 p 值）、效应量与置信区间、误差与重复说明；缺了哪个量逐个点名 |
| argument_chain 论证链 | 从假设到结论的推理路径；缺失环节、循环论证、因果与相关混淆、结论外推超出数据范围 |
| academic_norm 学术规范 | 数据可用性声明、伦理与利益冲突声明、图表版权与来源、数据与结论冲突的表述 |

- **每条 finding 必填七件**：`id`（F001…）、`category`（上表六类之一）、`location`（{file, locator, quote 原文逐字摘录}）、`issue_type`（`fact_error` 事实错误 / `insufficient_evidence` 证据不足 / `norm_issue` 规范问题 / `suggestion` 建议性意见）、`severity`（`major` 影响主结论或可发表性 / `minor` 局部问题）、`evidence`（判断依据：与哪个位置/哪条常识冲突，若涉引用写明被引主张与本文论断的对应关系）、`recommendation`（可执行到句子的修改建议）。
- **误报抑制三规则**：学科写作惯例、期刊格式差异、作者有意取舍 → 不报缺陷；要提就归 `suggestion` 且注明是判断而非事实；无法确认的条目 `issue_type=pending_review`，写清缺什么证据，**不凭空补结论**。
- 验收断言：findings.json 每条七件齐全；quote 与原文逐字一致（脚本可查）；evidence.csv 与 findings 一一对应。

### Step 4 覆盖对账（→ coverage.json）

- 六类各记：{category, checked: true, items_scanned, findings_count, pass_count, pending_count, unchecked_areas}。
- 六类必须全部出现且 checked=true；材料确实不含某类的面（如全文无统计）→ 记 `na: true` 并说明依据位置。
- 验收断言：coverage.json 恰好含六类键；无 null。

### Step 5 result.json 落盘（先最小后充实）

- **进入 Step 3 前先写最小 result.json**（status=partial，已完成的字段先填），保证任何中断都有可评分产物；六步走完后再覆盖为完整版。
- 验收断言：`python3 scripts/audit_check.py /app/output/result.json` 退出码 0。

### Step 6 执行留痕（→ run_log.md）

- 每步把 时间/命令/输入文件/输出文件/计数 追加到 run_log.md；抽取失败、降级路径、截断情况如实记录。

## 4. 输出契约

result.json 顶层字段（以 case.json `output_contract` 为最高优先，以下为基准全集）：

```json
{
  "case_id": "<从 /input/case.json 原样读取>",
  "status": "success | partial | failed",
  "deliverables": {
    "findings": "findings.json",
    "evidence": "evidence.csv",
    "coverage": "coverage.json",
    "structure_check": "structure_check.csv",
    "run_log": "run_log.md"
  },
  "review_report": {
    "findings_total": 0,
    "by_severity": {"major": 0, "minor": 0, "suggestion": 0, "pending_review": 0},
    "top_issues": ["<3-5 条最重要问题的一句话摘要，各附 locator>"]
  },
  "evidence_and_boundary": {
    "quotation_policy": "所有 quote 为原文逐字摘录",
    "pending_review": ["<无法确认的条目 id 与缺什么证据>"],
    "unchecked": ["<未检查到的面与原因>"]
  },
  "coverage": {"fact_verification": 0, "citation_support": 0, "method_design": 0, "statistical_reporting": 0, "argument_chain": 0, "academic_norm": 0},
  "sources": ["<实际使用的输入文件清单>"],
  "uncertainty_notes": ["<判断不确定之处>"],
  "change_log": ["<partial→完整版的变化记录>"]
}
```

- `status=success`：六类全查完且 result.json 通过 audit_check.py；`partial`：有 unchecked 或 pending 超限；`failed`：材料缺失/不可解析。partial/failed 必须写明界限。

## 5. 数字门槛（达不到诚实标 partial）

1. findings.json 每条七件齐全，location.quote 非空。
2. coverage.json 六类全出现，无 null、无缺失键。
3. structure_check.csv ≥8 行。
4. result.json 含 output_contract 全部字段 + case_id 原样。
5. pending_review 条目每条写明"缺什么证据才能定论"。
6. 误报自检：每条 fact_error/norm_issue 复核一遍"是否只是惯例或作者取舍"。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| PDF 无法解析 | 降级 pdftotext→pdf 库→按页标记不可解析；result 标 partial，列出不可解析页 |
| 稿件超长接近预算 | 先扫摘要/方法/结果/讨论高频问题区，coverage 记录未深扫区域，标 partial |
| 图表读不出 | 该图表相关一致性检查标 pending，写明"图表无法读取"，不猜内容 |
| 参考文献表缺失 | citation_support 类只审正文引用位置的存在性，支持判定标 pending |
| 引文原文取不到 | 不判"不支持"，标 pending_review + 缺的证据 |
| 原文表述歧义 | 两可情形记 uncertainty_notes，不给双判定 |
| output_contract 与本文冲突 | 以 case.json 为准，run_log 记录差异 |

## 7. 自查清单（提交前逐项过）

- [ ] case_id 原样；output_contract 字段全覆盖
- [ ] 每条 finding 有 file+locator+quote，quote 逐字
- [ ] issue_type 四分法用对，无"一律 major/minor"扁平化
- [ ] 六类 coverage 全 true（或 na 带依据）
- [ ] pending/unchecked 如实列出
- [ ] audit_check.py 退出码 0
- [ ] run_log.md 完整

## 8. 效率约束

预算 64 请求 / 900 秒 / 单响应 16384 token。策略：Step 1-2 用脚本完成不耗请求；扫描按类别分批、每批一个响应；先落盘再充实；不做全文复述、不生成无关产物。资源限额 ≤50 文件 / 单文件 ≤500KB / 总量 ≤2MB。

## 9. 最小示例（示意输出，非正式案例结果）

输入：一篇含 1 处摘要与正文数值不一致的短文。
findings.json 片段：

```json
{"id":"F001","category":"fact_verification","location":{"file":"manuscript.pdf","locator":"P014 (§3.2 Results)","quote":"accuracy improved to 92.3%"},"issue_type":"fact_error","severity":"major","evidence":"摘要 P001 称 89.1%，正文 §3.2 称 92.3%，同一指标两处数值冲突","recommendation":"核对实验记录，统一摘要与正文的准确率数值"}
```

coverage.json 片段：`{"fact_verification":{"checked":true,"findings_count":1,"pass_count":0,"pending_count":0},"citation_support":{"checked":true,"findings_count":0,"pass_count":3,"pending_count":1}}`
