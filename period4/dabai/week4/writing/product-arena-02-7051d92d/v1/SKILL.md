---
name: academic-language-polish
description: |
  学术语言润色 Skill：对给定稿件执行"最小编辑"润色，消除语法/句法/搭配/标点硬错误，
  统一术语与语域，严守限定强度与语义保真。核心交付物是"润色后全文＋逐句改动对照表
  （原句/改句/修改类型/理由/位置）＋术语表"，全部修改可回溯到原文位置，不编造事实。
---

# 学术语言润色（最小编辑 + 逐处可复核）

## 1. 用途与适用范围

- 适用：期刊论文、学位论文、基金申请书、英文摘要、审稿回复等学术文本的润色。
- 方法主线：**分句级最小编辑**。只改有明确错误或明确文体问题的句子；不做整段重写。
- 硬约束：不改变原意与限定强度；不新增材料外事实；每处修改都有记录。
- 不适用：内容性重写、翻译、降重。遇到这类请求在 result.json 里标 `out_of_scope` 并说明。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：记录 `case_id`（原样保留）、任务说明、材料路径、`output_contract` 全部字段。
2. 读 `/input/task.md`（如存在）：确认指定章节、目标文体、格式约束。
3. 盘点材料文件，逐个真实读取（PDF/MD/TXT/DOCX 均读实际内容，不凭标签猜内容）。
4. 材料缺失或任务无法执行 → 先落 `status=failed` 的 result.json，说明缺什么，不虚构。

## 3. 工作流程

### Step 1 术语表先行
- 扫全稿提取核心概念的中英文写法、缩写、首现形式，产出 `term_table`（术语/变体/统一写法/依据）。
- 术语表内部冲突（同一概念多种写法且无法判断）→ 标 `needs_confirmation`，选多数用法并记录。

### Step 2 分句与定位
- 把指定章节拆成句子，编号 `S<章节>-<序号>`（如 `S2-05`），作为所有记录的定位锚。

### Step 3 逐句诊断（六类检查，每句全过一遍）
| 类型 | 检查项 |
|---|---|
| 语法 | 主谓一致、时态语态、冠词介词、单复数、悬垂修饰 |
| 标点 | 中英标点混用、逗号粘连、长句该切分而未切 |
| 术语 | 与术语表不符、缩写未先全称、跨章节漂移 |
| 语域 | 口语化/宣传化/绝对化表述、人称误用、目标文体违例 |
| 语义 | 限定词强度（"证明/表明/提示"）、因果vs相关、否定范围、量词 |
| 格式 | 数字与单位写法、引用编号指向、图表引用对得上 |

### Step 4 最小编辑改写
- 改动原则：**只改必须改的词**；能改词不改短语，能改短语不改整句。
- 禁改清单：数据、单位、引用编号、图表指向、作者主张的限定强度。
- 改后回读：把改句与原句并排比对，若信息量/限定强度有偏移，回退到更小改动。

### Step 5 产出改动对照表
每处修改一条记录：`{id, locus, original, revised, change_type, reason, confidence}`。
`change_type ∈ {grammar, punctuation, terminology, register, semantics_guard, format}`。
理由必须写到"第三方能否据此判断该不该改"的程度（写规则依据，不写"更通顺"了事）。

### Step 6 语义保真自检
- 核对每句：改前改后的命题是否一致；限定词（may/might/suggest/证明）强度未变。
- 数字、单位、`[引用号]`、`图/表 X` 与原文逐一比对，不一致即回退或标注。

## 4. 输出契约（/app/output/result.json）

以 case.json 的 `output_contract` 为准，本 skill 保证以下字段存在且落实（若 contract 另有字段，逐字段补充）：

```json
{
  "case_id": "原样保留",
  "status": "complete | partial | failed",
  "polished_text": "润色后完整文本（可编辑、按原文结构）",
  "changes": [
    {"id": "C001", "locus": "S2-05", "original": "原文句子片段",
     "revised": "修改后片段", "change_type": "grammar",
     "reason": "具体规则与依据", "confidence": "high"}
  ],
  "term_table": [{"term": "", "variants": [], "unified": "", "basis": ""}],
  "sources": [{"claim_or_number": "", "origin": "材料路径+位置"}],
  "unverified": [{"item": "", "reason": "材料不足/冲突/需作者确认"}],
  "change_records": {"total": 0, "by_type": {}, "unresolved_flags": 0},
  "uncertainty": "整体不确定性说明"
}
```

- `polished_text` 与 `changes` 必须一一对应：每处 diff 都有记录，无记录不改动。
- 未确认项宁可标出，不可静默改掉。

### 触发与调用方式
- 触发条件：任务明确要求润色/校对/改写稿件文本；纯内容问答不触发改写。
- 调用：读 case.json → 按第 3 节流水线执行 → result.json 落 /app/output。
- 输入接口：`/input/case.json`（case_id、材料路径、output_contract）、材料文件、可选 task.md。
- 输出接口：`/app/output/result.json`（契约见第 4 节）+ 润色后全文（正文内可直接使用）。

### 逐句过检执行要点
- 分句按句号/问号/叹号及分号切分，公式与引用标记视为句子内部 token 不切断。
- 每句过检结果三态：`clean`（无改动）/`changed`（有改动，入 changes）/`flagged`（疑似问题但不确定，入 unverified）。
- flagged 与 clean 均计数，汇总写入 change_records，保证"100% 逐句过检"可被复核。
- 重复润色幂等：对同一输入二次运行，changes 集合应一致；不一致时以最小改动集为准。

## 5. 数字门槛

- 指定章节 100% 逐句过检（句级计数记录在 change_records）。
- 每条修改有 locus + reason；无 locus 的修改视为违规，必须补记录或回退。
- 语义保真检查（Step 6）零未处理告警，否则 status=partial 并列出待确认项。
- 达不到门槛时诚实标 partial，列出缺口清单。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 超长输入 | 按章节分批处理，全部完成后合并；不截断不跳段 |
| 编码混乱 | 先转 UTF-8 处理，原文异常点记入 unverified |
| 公式/引用混杂 | 公式与引用标记原样保留，只改周边自然语言 |
| 中英混排 | 英文部分按英语规则、中文部分按中文规则，分别过检 |
| 术语表内部冲突 | 取多数用法，标 needs_confirmation |
| 目标文体不明 | 默认按中性学术语体处理，并在 uncertainty 中说明假设 |
| 纯问答请求（非润色） | 不擅自改写，正常回答；仅在明确润色指令时触发本流程 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 字段全覆盖
- [ ] 指定章节逐句过检，无跳段
- [ ] 每处修改有 locus/original/revised/type/reason
- [ ] 数字/单位/引用号/图表指向与原文一致
- [ ] 术语全篇统一，缩写首现已定义
- [ ] 未确认项全部标注，无静默修改
- [ ] result.json 可解析，status 如实

## 8. 效率约束

预算 64 请求 / 900 秒。先落最小 result.json（polished_text+changes），再补 term_table 与 sources。
单文件 ≤500KB，总量 ≤2MB，无符号链接。

## 9. 最小示例（示意输出，非正式案例结果）

输入：`"The results, which was consistent with previous studies, strongly proves our hypothesis."`
输出：
```json
{"id": "C001", "locus": "S3-02",
 "original": "The results, which was consistent with previous studies, strongly proves our hypothesis.",
 "revised": "The results, which were consistent with previous studies, strongly support our hypothesis.",
 "change_type": "grammar",
 "reason": "which 从句主语 results 为复数，was→were；主句主语 results 复数，proves→supports。限定强度 strongly 未改。",
 "confidence": "high"}
```
注意：示例中仅修语法，"strongly" 的强度保留——若作者本意存疑，标入 unverified 而非悄悄削弱。
### 最小 result.json 完整示意（示意，非正式案例结果）
```json
{"case_id": "示例占位", "status": "complete",
 "polished_text": "……（全文）",
 "changes": [{"id": "C001", "locus": "S1-03", "original": "which was",
              "revised": "which were", "change_type": "grammar",
              "reason": "先行词 results 复数", "confidence": "high"}],
 "term_table": [{"term": "深度学习", "variants": ["deep learning", "DL"],
                 "unified": "deep learning (DL)", "basis": "首现全称后用缩写"}],
 "sources": [{"claim_or_number": "准确率 92.3%", "origin": "材料 tables.md 第4行"}],
 "unverified": [{"item": "摘要末句限定词", "reason": "疑似作者口误，待确认"}],
 "change_records": {"total": 6, "by_type": {"grammar": 3, "terminology": 2, "format": 1},
                    "sentences_total": 48, "clean": 40, "changed": 6, "flagged": 2},
 "uncertainty": "目标文体默认按期刊论文处理"}
```
