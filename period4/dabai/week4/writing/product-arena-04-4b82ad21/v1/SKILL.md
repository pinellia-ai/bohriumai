---
name: intro-related-work-writer
description: |
  引言与相关工作写作 Skill：从给定论文材料起草/改写引言，四部分结构（研究背景、
  相关工作分组比较、研究空白推导、贡献条目）。核心机制是"引用-论断绑定"：
  每条引用绑定到具体论断与位置，空白由已引文献缺口推导，贡献与正文证据对齐，
  不编造文献、不夸大适用范围。
---

# 引言与相关工作写作（四段式 + 引用论断绑定）

## 1. 用途与适用范围

- 适用：期刊/会议/学位论文引言与相关工作章节的起草与改写。
- 方法主线：**四部分结构**（背景 → 相关工作 → 空白 → 贡献），每部分有独立验收标准；
  所有他人工作转述与引用**绑定到具体论断**，可逐条复核。
- 硬约束：转述忠于原文；空白必须有已引文献依据；作者判断与文献结论明确区分；不编造文献。
- 不适用：结果/方法章节写作（标 out_of_scope）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id` 原样、任务说明、材料路径、`output_contract` 全字段。
2. 读 `/input/task.md`（如有）：目标期刊格式、引用格式（顺序编码/著者-出版年）、篇幅约束。
3. 盘点并真实读取材料：本文稿/实验摘要、参考文献全文或摘要、文献库。转述他人工作**必须以其原文为据**，凭标签猜内容禁止。
4. 文献库为空或不足以支撑某段 → 该段先落占位与 `needs_literature` 标记，不编造。

## 3. 工作流程

### Step 1 材料要素抽取
- 从本文材料抽取：研究对象、方法路线、主要结果、可用图表清单（表 `self_evidence`）。
- 从每篇参考文献抽取：问题设定、方法路线、结论、局限（表 `related_map`），每条带原文位置引用（篇名+章节/页/摘要句）。

### Step 2 相关工作分组
- 按**方法路线或问题设定**分组（不用时间顺序罗列），每组内同一维度比较：问题设定/方法/数据与评价/局限。
- 每条转述格式：`{ref, group, claim, evidence_locus, caveats}`；转述与原文不符处禁止。
- 组间比较落在维度差异上，写清各工作取舍。

### Step 3 研究空白推导
- 空白只能从 `related_map` 的共同限制、未覆盖场景或冲突结论推出，形成推导链：
  `gap = (文献A局限@位置 + 文献B未覆盖@位置 [+ 冲突]) → 本文如何填补`。
- 每个空白登记 `gap_chain`；推导不了的空白不写；作者判断句标注"作者判断"。

### Step 4 贡献条目
- 每条贡献压缩为可核对条目，绑定到 self_evidence（方法/图表/实验结果）：
  `contribution → evidence(表/图/章节/实验) `。
- 贡献超出 self_evidence 支持范围 → 削弱表述或删除，记入 `weak_claims`。

### Step 5 成稿
- 按四部分组装引言，段落间承接（背景指向问题 → 相关工作指向空白 → 空白指向贡献）。
- 每条引用落到具体论断句内（不挂段末），引用格式按目标规范。
- 背景**禁止空转铺垫**（"近年来受到广泛关注"式无信息句）；必须指向具体问题与技术约束。

### Step 6 对账自检（跑 scripts/claim_cite_check.py）
- 每条引用有 locus + claim；每个 gap 有 chain；每条贡献有 evidence。
- 引用元数据（作者/年份/来源）与文献库逐条核对。

## 4. 输出契约（/app/output/result.json）

以 case.json 的 `output_contract` 为准，本 skill 保证：

```json
{
  "case_id": "原样保留",
  "status": "complete | partial | failed",
  "draft_text": "引言成稿（含四个部分，可编辑）",
  "related_map": [{"ref":"","group":"","claim":"","evidence_locus":"","caveats":""}],
  "gap_chain": [{"gap":"","supports":["文献@位置"],"fill":"本文对应关系"}],
  "contributions": [{"item":"","evidence":"","locus":""}],
  "citation_binding": [{"citation":"","locus":"","claim_snippet":"","metadata_verified":true}],
  "self_evidence": [{"element":"","locus_or_chart":""}],
  "unverified": [{"item":"","reason":""}],
  "weak_claims": [],
  "sources": [], "uncertainty": ""
}
```

### 触发与调用方式
- 触发条件："写引言""整理相关工作""补引用""核对贡献"等指令。
- 调用：读 case.json → Step1 要素抽取 → Step2-3 分组与空白推导 → Step4 贡献 → Step5 成稿 → Step6 对账（脚本实跑）→ result.json 落 /app/output。
- 脚本调用：`python3 scripts/claim_cite_check.py <result.json>`，校验引用绑定/空白链/贡献-证据三重闭合，问题存在退出码 1。

### 四部分写作要点
- 背景：第一段必须出现具体问题域与技术约束；检测空转铺垫句（"近年来受到广泛关注""具有重要意义"且无后续具体指向）并重写。
- 相关工作：每组 2-5 篇，组内同维度比较；逐篇转述不超过原文含义，caveats 引原文表述。
- 空白：推导链中每个 supports 都指向具体文献位置；"作者判断"句式显式写出。
- 贡献：3-5 条为常见合理区间；每条一句话＋证据指针；与摘要/结论中的表述保持一致。

## 5. 数字门槛

- 四部分齐全且承接；无引用空挂（每条引用绑定 claim）。
- related_map 每条有 evidence_locus；gap_chain 每条 supports ≥1 且带位置。
- contributions 与 self_evidence 100% 对应；未对应条目进 weak_claims 并说明。
- 引用元数据核对未通过的引用不得使用。达不到标 partial。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 文献库为空/不足 | 相应段落落 needs_literature 占位，status=partial，不编造 |
| 引用查不到原文 | 转述标 unverified，只保留元数据引用，不写结论转述 |
| 目标期刊格式未知 | 默认顺序编码制并在 uncertainty 说明 |
| 语言切换（中/英） | 按任务要求输出对应语言，术语表保持一致 |
| 材料冲突（两文献结论相反） | 如实写入冲突，作为空白来源之一，不裁决 |
| 空白缺乏依据 | 不写该空白；如任务强制要求，标 unverified 并说明 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 字段全覆盖
- [ ] 四部分齐全：背景具体、分组比较、空白有链、贡献有据
- [ ] 每条引用绑定 locus+claim，元数据核对通过
- [ ] 相关工作转述均带原文位置
- [ ] 无空转铺垫句；无未支撑的强断言
- [ ] 脚本实跑通过；未编造文献与数据

## 8. 效率约束

预算 64 请求 / 900 秒。先落 draft_text 最小版，再补 binding/gap/contribution 表。
≤50 文件、≤2MB、无符号链接。

## 9. 最小示例（示意输出，非正式案例结果）

gap_chain 示例：
```json
{"gap": "现有方法均假设标签完整，未处理标注噪声场景",
 "supports": ["Smith2020 §5 指出其方法依赖完整标注",
              "Lee2021 摘要：仅在干净数据集评测"],
 "fill": "本文第3节引入噪声鲁棒损失函数直接对应该假设"}
```
citation_binding 示例：
```json
{"citation": "Smith2020", "locus": "引言-S4", "claim_snippet": "依赖完整标注限制了其在医疗数据上的适用性", "metadata_verified": true}
```
### 最小 result.json 完整示意（示意，非正式案例结果）
```json
{"case_id": "示例占位", "status": "complete",
 "draft_text": "1. 引言 …… 1.1 研究背景 …… 1.2 相关工作 …… 1.3 研究空白 …… 1.4 本文贡献 ……",
 "related_map": [{"ref": "Smith2020", "group": "完整标注路线",
   "claim": "其方法依赖完整标注", "evidence_locus": "Smith2020 §5",
   "caveats": "作者自述局限"}],
 "gap_chain": [{"gap": "标注噪声场景未被覆盖",
   "supports": ["Smith2020 §5", "Lee2021 摘要"], "fill": "本文第3节"}],
 "contributions": [{"item": "噪声鲁棒损失函数", "evidence": "方法第3节+表2", "locus": "引言-S12"}],
 "citation_binding": [{"citation": "Lee2021", "locus": "引言-S9",
   "claim_snippet": "仅在干净数据集评测", "metadata_verified": true}],
 "self_evidence": [{"element": "表2 主结果", "locus_or_chart": "材料 result.md 第8行"}],
 "unverified": [{"item": "Lee2021 结论转述", "reason": "仅获摘要未获全文"}],
 "weak_claims": [], "sources": [], "uncertainty": "引用格式默认顺序编码制"}
```
