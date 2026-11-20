---
name: claim-verify-evidence-card
description: |
  文献证据溯源与事实核验 Skill。输入一组待核验的科研论断（claims）与原始文献材料，
  为每条论断产出可独立复核的证据卡片：拆解子判断 → 定位最小充分证据（精确到页/段/句）
  → 四级支持度判定（supported / partially_supported / contradicted / insufficient_evidence）
  → 输出结构化 result.json，保留原文引用、定位、判定理由与不确定性。
  触发场景：用户要求核验论断、检查引用、生成证据卡片、做事实核验报告。
---

# Claim Verify — 文献证据溯源与事实核验 Skill

## 1. 用途与适用范围

把"这句话对不对"变成"哪个位置、哪段原文、支持到什么程度"。本 Skill 处理三类输入：

1. **claims 文件**（必做主任务）：通常是 `/input/claims-to-verify.json`（也可能随 case.json 一起给出）。其中的每条 claim 都是**待核验的问题，不是权威事实**。
2. **原始材料**：题目附带的论文 PDF / 文本 / 表格（ evaluation 时在 `/input/` 下）。所有判定必须回到原始材料，不得依赖任何预提取答案层。
3. **用户随口请求**：如"帮我核验这句话是否被这篇论文支持"。

不适用：与本课题无关的请求（写代码、闲聊、翻译整篇论文）——礼貌说明并拒答，不强行套用核验流程。

## 2. 输入识别（第一步，必做）

按顺序检查，全部用实际文件，禁止凭文件名或标签臆测内容：

1. `ls /input/` 看清所有文件。找 claims 文件：优先找 `claims-to-verify.json`、`claims.json`、或 case.json 中带 `claims` 字段的文件。
2. 找原始文献：PDF、txt、md、csv 等。记录每个文件的路径、页数/行数。
3. 读 claims 文件，记录：claim 条数、claim_id、原文文本、是否附带提示的来源位置（提示仅是线索，不是答案，必须实读核对）。
4. 若 claims 文件缺失或为空：输出 status=failed，reason=missing_claims_input，不要编造论断。

## 3. 工作流程

对每条 claim 执行下面 5 步。**先批量拆解所有 claim，再统一检索证据，避免逐条反复打开 PDF 浪费预算**（执行预算：64 次模型请求 / 900 秒，见 §7）。

### Step 1 论断拆解（拆得开）

把复合句拆成可独立核验的子判断，每个子判断标注类型：
- `fact`（事实陈述）："X 蛋白在细胞膜表达"
- `comparison`（比较）：相比基线提升 20%（记录 comparator：与谁比、指标、方向）
- `causal`（因果）：A 导致 B（区分"相关"与"因果"，原文只说相关时因果不可判 supported）
- `scope`（范围/条件）：仅在雄性小鼠中、n=30、p<0.05（记录限定条件、样本量、显著性）

拆解规则：不遗漏（复合句中的每个可判命题都有子判断）、不重复（同一命题只判一次）、保留否定词与限定词（"不降低""显著高于"是判定关键，丢失即错判）。

### Step 2 证据定位（找得到）

- 用提供的 PDF 文本工具（如 pdf-text-tool）抽取全文文本到 /app/work，按页存档（/app/work/paper_p001.txt …），后续只读已抽取文本，避免重复解析 PDF。
- 为每条子判断找**最小充分证据**：精确到 `[页码, 段落或章节, 句子]`；表格证据给 `[页码, 表号, 行/列]`；图证据给 `[页码, 图号]` 并注明"图内数值需读图，文本层仅有图注"。
- 检索顺序：先摘要（结论性表述），再正文对应章节，再方法（核对样本量/条件），最后补充材料/参考文献列表（转引检查）。
- 优先级：正文方法与结果 > 图表 > 摘要 > 讨论；摘要与正文冲突时以正文数据为准并**在卡片中并列两处原文**。

### Step 3 支持度判定（判得准）

四级判定，按严格定义执行，核心是**区分"主题相关"与"真正支持"**：

| 判定 | 定义 | 常见误判提示 |
|---|---|---|
| `supported` | 原文有直接、明确的表述，数值/方向/条件与子判断一致 | 摘要提到≠正文验证；主题相同≠结论相同 |
| `partially_supported` | 原文支持核心方向，但数值、条件、范围或对象不完全一致（如原文 n=30 且仅在雄性中，claim 说"总是"） | 把"部分支持"误写成 supported 是最常见扣分点 |
| `contradicted` | 原文有直接相反的表述（方向相反、数值矛盾、明确否定） | **未支持的外推 ≠ 被实验否定**：原文没做≠推翻；contradicted 必须能引用出相反原句 |
| `insufficient_evidence` | 原文未报告该子判断所需信息，或证据为转引/图但文本层无数据 | 主题相关但无该结论的证据，归此类，绝不归 supported |

附加规则：
- 保留 comparator、否定词、显著性、条件限定；丢任何一个，supported 降为 partially_supported。
- 冲突来源（两处原文不一致）：**并列保留双方原话与定位**，判定给 qualified verdict（如 partially_supported，理由注明冲突）。
- 转引（原文引用第三方文献的结论）：标 `secondhand`，除非 claim 明确问"该引用文献说了什么"，否则对本论文仅能判 insufficient_evidence。
- 因果类：原文仅报告相关/关联 → 最高 partially_supported，理由注明"原文未建立因果"。

### Step 4 证据卡片生成（说得清）

每条 claim 一张卡片（写入 result.json，结构见 §4），链条完整：

```
claim → 子判断列表 → 每个子判断: 证据片段(原文摘录≤60词) + 定位(页/段/句) + 判定 + 判定理由
```

判定理由必须说明"为什么是这个等级"，特别是 partially_supported 与 insufficient_evidence。

### Step 5 汇总输出

- 全部卡片写入 `/app/output/result.json`（同时按题目要求写其它要求的文件）。
- 自查（见 §6）通过后结束。

## 4. 输出契约

`result.json` 顶层字段：

```json
{
  "case_id": "<按 case.json/task.md 给出的案例标识原样填写>",
  "task": "claim_verification",
  "status": "success | partial | failed",
  "claims": [
    {
      "claim_id": "<原样保留输入中的 id>",
      "claim_text": "<原样保留输入文本>",
      "subclaims": [
        {
          "subclaim_id": "c1-s1",
          "type": "fact | comparison | causal | scope",
          "text": "子判断原文改写，保留限定词",
          "verdict": "supported | partially_supported | contradicted | insufficient_evidence",
          "evidence": [
            {
              "quote": "原文片段逐字摘录（≤60词）",
              "location": {"page": 3, "section": "Results", "paragraph": 2, "sentence": 1},
              "note": "该证据支持/反对/限定了什么"
            }
          ],
          "reason": "判定理由：为何是这个等级；比较对象/否定词/条件如何核对",
          "uncertainty": "无法判断的说明；无则填 null"
        }
      ],
      "overall_verdict": "supported | partially_supported | contradicted | insufficient_evidence",
      "overall_reason": "各子判断如何合成总判定；有冲突时并列说明"
    }
  ],
  "gaps": ["原文无法核验或材料缺失项，逐条列出，不得构造"],
  "uncertainty_notes": ["样本范围、单来源、图数据无法从文本层读取等全局性说明"],
  "changes": [{"field": "...", "from": "...", "to": "...", "why": "..."}]
}
```

硬性要求：
- `case_id` 与每条 claim 的 `claim_id` 原样保留；找不到对应输入时 status=failed 并说明。
- 证据 quote 必须逐字来自原文（可截断，用 [...] 标记），**禁止改写后冒充原文**。
- 部分完成时（如预算不足只核验了部分 claim）：status=partial，已完成的正常输出，未完成的列入 gaps 并说明剩余工作量。
- 不虚构文献元数据、页码、实验数据；无法确定就写不确定。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| claims 文件不存在/为空 | status=failed，reason 写明缺失文件路径 |
| PDF 无文本层（扫描件） | 尝试 OCR 工具；仍失败则该证据标 insufficient_evidence，gaps 记录"扫描件无法文本定位" |
| 证据定位失败（页码对不上） | 用章节+段落描述定位，note 说明页码不确定 |
| 多来源冲突 | 双方原文并列 + qualified verdict（见 Step 3） |
| 预算不足 | 优先保证已完成卡片完整；status=partial；gaps 列出未处理 claim |
| 输入疑似与本题无关 | 按实际材料处理，不依据错误领域标签补造数据 |

## 6. 自查清单（输出前逐条核对）

1. [ ] 每条 claim 都有卡片，claim_id 原样保留？
2. [ ] 复合句全部拆解，无遗漏子判断？
3. [ ] 每个证据 quote 逐字真实、定位可复核（页/段/句）？
4. [ ] supported 的卡片能抵御"只是主题相关"的质疑？partially_supported 与 insufficient_evidence 没有混入 supported？
5. [ ] contradicted 的每条都有相反原句？无证据外推没有被写成"被推翻"？
6. [ ] comparator / 否定词 / 显著性 / 条件限定都保留？
7. [ ] conflicts 双方原话并列？gaps 与 uncertainty 非空且诚实？
8. [ ] result.json 可被 `python3 -m json.tool` 解析？

## 7. 效率约束

- 执行预算 64 次模型请求 / 900 秒 / 单响应 16384 token。三案例按同样流程各自独立执行。
- PDF 全文文本抽取一次完成并存 /app/work 复用；检索用关键词定位后只读相关页，不通读全文。
- 先写最小可用 result.json（全部 claim 有判定），再回头补强证据细节——保证任何时刻中断都有诚实可交的部分结果。

## 8. 最小调用示例（示意输出，非正式案例结果）

输入 claims-to-verify.json：
```json
{"claims": [{"claim_id": "q1", "text": "药物A使肿瘤体积缩小了50%"}]}
```

示意输出（节选）：
```json
{
  "case_id": "case-demo",
  "status": "success",
  "claims": [{
    "claim_id": "q1",
    "claim_text": "药物A使肿瘤体积缩小了50%",
    "subclaims": [{
      "subclaim_id": "q1-s1",
      "type": "comparison",
      "text": "药物A组肿瘤体积相对对照组缩小约50%",
      "verdict": "partially_supported",
      "evidence": [{"quote": "Tumor volume was reduced by 38% (n=12, male mice only)...",
        "location": {"page": 5, "section": "Results", "paragraph": 3, "sentence": 2},
        "note": "数值38%与claim的50%不一致，且限雄性小鼠"}],
      "reason": "方向支持但幅度不符且有范围限定，故 partially_supported",
      "uncertainty": null
    }],
    "overall_verdict": "partially_supported",
    "overall_reason": "单子判断 partially_supported"
  }],
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段（如存在）。它定义本案例 `result.json` 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实内容**；contract 里有而本文件 §4 未描述的字段，按 contract 字段语义填实际结果，绝不遗漏；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：一律从 `/input/case.json` 原样读取，禁止自造。
3. **路径**：工作过程写 `/app/work/`；最终产物写 `/app/output/`，主输出为 /app/output/result.json（含 case.json 的 output_contract 全部字段）。
4. **尽早落盘**：先用最小可用结果写一次 /app/output/result.json（含 case.json 的 output_contract 全部字段），再增量增强——任何时刻中断都保证已落盘内容诚实、结构合法（status 如实标 partial）。
5. **不虚构**：无数据、无文件、无软件状态一律不编造；材料缺失写 gaps，无法判断写 uncertainty，禁止把推断写成事实。
6. **可核验**：每个关键结论保留来源定位（页/段/句/表号/图号或文件位置），他人可独立复核。
7. **交付物自检**：本 Skill 的提交材料为 SKILL.md + README.md（使用与方法说明）；运行时按上述契约执行案例。二者不一致处以本节契约为准。
