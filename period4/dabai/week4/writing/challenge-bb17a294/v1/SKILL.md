---
name: academic-translation-bilingual
description: |
  学术翻译与双语写作 Skill。整篇翻译/双语对照交付：术语锁定表先行（抽取术语/缩写/上下位词，译法全篇锁定到摘要正文图表题注附录），原文段号↔译段号逐段对照（句段一一对应可双语修改），数字保真校验（数值/单位/量级/年份/统计口径原样落地，处理万/亿 vs million/billion），语义边界守卫（否定范围/限定语/因果强度/引用归属保真）。离线运行：术语依据与数字核对必须带原文位置（文件/页/段），原文没有的意思不增译，原文有的限定不省译。
---

# 学术翻译与双语写作（术语表先行 → 逐段对照 → 数字保真 → 边界守卫）

## 1. 用途与适用范围

- 用途：把给定原文整篇译出（纯译文/双语对照/带修订标记三种形态按任务要求），可直接进入作者修改流程。
- 适用：中↔英学术文本；覆盖章节、图表题注、公式说明、脚注、参考文献条目。
- 四大考察点：术语稳、数字实、对得齐、边界清（前人弱项 59.0，本 skill 对应加严门槛）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id` 原样保留、任务说明、原文路径、output_contract 全字段。
2. 读 `/input/task.md`：确认**输出形态**（纯译文/双语对照/带修订标记）、目标语言、领域、引用格式。
3. 读原文真实全文（PDF 用 pdf-text 工具），盘点章节/图表/公式/脚注/参考文献清单——这是完整性对账基准。
4. 先落盘最小 `result.json`（status=partial 占位）。

## 3. 工作流程（七步流水线）

### Step 1 术语锁定表（产出 `term_lock.md`，先行）
从原文抽取领域术语/缩写/上下位词，逐条：`原文术语 | 锁定译法 | 学科惯用依据 | 首次出现位置 | 规则（首次展开、图表题注同锁）`。同一英文词在不同学科译法不同时，按原文领域选并用【】在表中注明依据；全文、图表题注、附录一个说法。**术语表先行于翻译正文。**

### Step 2 数字资产盘点（产出 `numbers.json`）
抽取原文全部数字：数值/单位/量级/范围/年份/百分数/样本量/统计量/公式符号，逐条记录位置。中英文数量级换算规则固定：1万=10^4、1亿=10^8，million=10^6、billion=10^9，换算仅在目标语言习惯要求时进行并记录换算式；有效位数不变。

### Step 3 结构对账表（并入 para_mapping.md 首段）
`原文段号 | 译文段号 | 类型（标题/段落/图题/表题/脚注/参考文献条目）`，全文段号一一映射；公式、表格、题注、脚注、参考文献条目**保留原位原编号**。

### Step 4 逐段翻译（产出 `translation.md` 或双语对照稿）
- 双语形态：`P-001 原文 | P-001 译文` 逐段对照，段落顺序不变，可逐段修改不破坏结构。
- 风格：学术语域，避免逐字直译的冗长生硬，但**不改成宣传口吻或口语**；句式重组允许，语义单元不删。
- 边界守卫（对照检查）：否定范围不位移（not only/not 全句辖域）、模糊限制语（may/suggest/approximately）逐个保留、因果强度不变（associate≠cause）、增译/省译逐处记入 change_log。

### Step 5 数字保真校验
跑 `scripts/check_translation.py`（§6）：numbers.json 与译文数字集比对，单位与量级逐一核对；漏译/改值/单位错配 = FAIL。

### Step 6 引用与边界自查
引用标记（作者-年份/编号/上标/方括号差异按目标格式转换）、et al. 处理、参考文献条目逐条保留；语义边界四查（否定/限定/因果/归属）逐段过一遍并记录。

### Step 7 汇总 result.json

## 4. 输出契约（result.json 逐字段）

```json
{
  "case_id": "<原样保留>",
  "status": "success | partial | failed",
  "deliverable": {
    "translation_file": "/app/output/translation_bilingual.md",
    "output_form": "bilingual",
    "term_lock": "term_lock.md",
    "para_mapping": "para_mapping.md",
    "numbers_audit": "numbers.json"
  },
  "facts_sources": [
    {"item": "n=240, 95%CI [1.2, 3.4]", "source_location": "source.pdf p.5 §3.2", "translation_location": "P-007", "action": "kept_verbatim"}
  ],
  "term_locks": [
    {"term": "gradient descent", "locked_as": "梯度下降", "first_seen": "p.2 para.1", "applies_to": ["正文", "图1题注", "附录A"]}
  ],
  "changes": [
    {"location": "P-004", "type": "omission", "detail": "省译重复的 'as mentioned above'", "reason": "冗余，语义无损", "semantic_shift": false}
  ],
  "boundary_checks": [
    {"location": "P-012", "type": "hedging", "original": "may contribute to", "translation": "可能有助于", "strength_preserved": true}
  ],
  "uncertainty": [{"item": "术语 'domain' 的译法", "issue": "领域惯用存在'域/论域'两派", "resolution": "依原文领域取'域'", "needs_human_confirm": false}],
  "gaps": ["原文图3仅位图无矢量源，题注已译，图内文字不可编辑"],
  "limits": ["公式以 LaTeX 原样保留，未重排"],
  "reproduce": "按 README 步骤可复现"
}
```

硬性要求：`facts_sources` 覆盖全部数字与统计口径；`term_locks` 覆盖全部锁定术语并注明适用范围；`changes` 含全部增译/省译且标 semantic_shift；`boundary_checks` 覆盖四类边界。

## 5. 数字门槛（达不到如实标 partial）

- 段号对齐：para_mapping 覆盖 100% 原文段号（含图表题注/脚注/参考文献条目），缺号=FAIL。
- 数字保真：numbers.json 逐条在译文可指认（脚本比对），漏/改=FAIL。
- 术语唯一：锁定术语在译文只允许表内形式（脚本抽取比对），多形式=FAIL。
- 边界保真：原文限定语清单逐条在译文有对应表达，缺失=FAIL。

## 6. 校验脚本

捆绑 `scripts/check_translation.py`（纯标准库）：输入 `numbers.json`（原文数字+位置）+ `translated_numbers.json`（译文数字）+ `term_check.json`（术语→译文出现形式），输出 NUM-OK/NUM-MISS/NUM-ALTER、TERM-OK/TERM-MULTI 报告。先最小样例实跑再正式使用。

## 7. 异常处理表

| 异常 | 处置 |
|---|---|
| 公式/表格无法转写 | LaTeX/原样保留原位，limits 注明 |
| 术语表冲突 | 依原文领域锁定一种，term_lock 记录依据，uncertainty 标注 |
| 超长文本 | 按章节分块，段号全局编号不重置，逐块过 Step 5 |
| 语向不支持/编码错误 | status=failed 或 partial，gaps 写明原因，不猜译 |
| 引用格式异常 | 按任务目标格式转换并在 change_log 记录，文献条目内容不改 |
| 原文含明显笔误 | 译文按笔误直译并加译注 [sic/原文如此]，不擅自更正 |

## 8. 效率约束

预算 64 请求 / 900 秒：Step 0-2 前 10 请求；分块翻译每块 ≤10 段；先落最小 result.json。≤50 文件 / 2MB。

## 9. 最小示例（示意，非正式案例结果）

输入：英文摘要+正文 8 段（含 "approximately 1.2 million participants"）。
示意输出：term_lock 12 条；双语对照 8 段（P-001..P-008）；数字保真 15 条全 OK（"约 120 万参与者"，换算式记录）；result.json status=success，boundary_checks 含 2 条 hedging。

## 10. 命令序列

```
1. cat /input/case.json → 最小 result.json
2. 原文盘点 → term_lock.md（先行）→ numbers.json
3. para_mapping.md 段号骨架
4. 逐段翻译（双语对照）→ translation.md
5. python3 scripts/check_translation.py numbers.json translated_numbers.json term_check.json
6. 引用与边界四查 → result.json 定稿
```

## 11. 自查清单（交前全过）

- [ ] YAML frontmatter 可解析
- [ ] 术语表先行且译法全篇唯一（含图表题注/附录）
- [ ] 原文段号↔译段号 100% 对照
- [ ] 数字 100% 回溯原文位置，换算有记录
- [ ] 增译/省译逐处记录且标 semantic_shift
- [ ] result.json 全字段落实（facts_sources/term_locks/changes/boundary_checks/uncertainty/gaps/limits）
- [ ] 脚本 ast.parse + 最小实跑通过
- [ ] ≤50 文件 / 2MB
