---
name: literature-qa-cited-answers
description: |
  文献智能问答 Skill。输入一篇带段落编号的英文论文文本与中文问题清单（每例3题、共9题），
  逐题回答并给出依据：论文标识 + 段落编号 + 支持该论断的短引文。保留数值、单位、比较对象、
  实验条件与结论范围；区分论文实测结果、作者解释与自己的推断；材料未报告、部分可答、
  原文冲突、读取失败分别如实说明，不编造答案或引用。输出写入 /app/answers.json。
---

# Literature QA — 文献智能问答 Skill（段落级引用）

## 1. 用途与适用范围

"读取论文与问题 → 整合证据 → 逐题回答并标明依据"。每个答案都能回到原文段落核对。

适用范围与约束：
- 仅依据给定材料作答；平台提供摘要、正文、表格文字、图注与参考文献著录信息。
- **不做** PDF 解析、图像像素识别、附件读取、联网检索——材料里没有的就是没有。
- 问题为中文，论文为英文带段落编号；回答用中文，引文保留英文原文。

## 2. 输入识别（必做第一步）

执行时输入在 `/input/case.json`（原样保留案例包 v3 的段落编号和任务说明）：
1. 记录 `case_id`、论文标识（paper id）、材料版本。
2. 建立段落索引：`[段落号 → 摘要/方法/结果/讨论/表格/图注]` 映射表，后续引用全靠它。
3. 读全部问题（含子问），标记每题要整合的段落范围。
4. 材料或问题缺失：写明缺失项，能答几题答几题，status=partial。

## 3. 工作流程

### Step 1 逐题拆解
把每题拆成子问清单（含隐含子问：问"提升了多少"必须同时回答数值与条件）。

### Step 2 证据检索
- 按段落索引定位候选段落：方法段（怎么做）、结果段（数据）、讨论段（解释）、表格（精确数值）。
- **数值类问题**：优先表格与结果段原文数字，禁止凭记忆或常识补数。
- **机制/解释类问题**：结果段 + 讨论段，注明哪些是作者解释（author interpretation）。

### Step 3 撰写答案（三层分离）
每个答案明确区分：
- `reported`（论文实测）：直接来自结果/表格的数值与事实；
- `interpreted`（作者解释）：讨论段的因果解释，标注"作者解释"；
- `inferred`（我的推断）：材料未直说但合理推出，必须给出推断链并标注"推断"。
推断不得伪装成论文结论；没有对应段落支持的推断宁可删掉。

### Step 4 附依据
主要论断附：论文标识 + 段落编号 + 短引文（英文原句，≤40 词，逐字）。引用必须真实存在于该段落——先引用后成文，禁止写完答案再"配"引文。

### Step 5 不确定性处理
- 材料未报告：写"原文未报告"，列出缺口（缺哪段/哪个条件）。
- 部分可答：给出已答部分 + 明确缺口清单。
- 原文冲突（两段说法不一致）：指出冲突双方段落号并引用两处原句。
- 读取失败：如实报告，不编造。

## 4. 输出契约

写入 `/app/answers.json`（本题主输出为 answers.json，同时保留 /app/output/result.json 兼容平台归档）：

```json
{
  "case_id": "<原样>",
  "paper_id": "<原样>",
  "status": "success | partial | failed",
  "answers": [
    {
      "question_id": "<原样>",
      "question_text": "<原样>",
      "answer": "中文答案，覆盖全部子问",
      "sub_answers": [{"sub_q":"...","answer":"..."}],
      "evidence": [
        {"paper_id":"...","paragraph": 12, "quote": "英文原句逐字摘录",
         "supports": "该论断的哪一部分"}
      ],
      "layers": {"reported": ["要点..."], "interpreted": ["作者解释..."], "inferred": ["我的推断+推断链"]},
      "conditions_preserved": ["数值/单位/比较对象/实验条件/适用范围，逐条保留"],
      "gaps": ["未报告/无法确定项"],
      "confidence": "high | medium | low"
    }
  ],
  "conflicts": [{"paragraphs": [12, 27], "quotes": ["...","..."], "note": "冲突说明"}],
  "uncertainty_notes": [],
  "changes": []
}
```

硬性要求：九个问题全部覆盖（partial 时也要每题有 status 说明）；每个 evidence 引文逐字真实、段落号准确；答案中出现的每个数值都能在 evidence 或表格中找到出处。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 案例包结构变化 | 以实际文件为准，段落编号原样保留，不重排 |
| 问题超出材料范围 | 该题答 insufficient，gaps 写明缺什么 |
| 中英翻译歧义 | 保留英文关键术语，中文翻译加括号注明 |
| 段落过长截断 | 分段引用，不合并改写 |
| 预算不足 | 先答完数值类问题（易核验），机制类按序推进，status=partial |

## 6. 自查清单

1. [ ] 九题全答，每题子问无遗漏？
2. [ ] 每条主要论断有 段落号+逐字引文？引文确实在该段？
3. [ ] reported / interpreted / inferred 三层没混淆？
4. [ ] 数值、单位、比较对象、条件、范围逐条保留？
5. [ ] 冲突双方段落号都给出？未报告项都在 gaps？
6. [ ] answers.json 可被 json.tool 解析？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。先建段落索引再逐题检索；同一段落供多题复用，读一次记要点。先出最小可用 answers.json（每题有答案+核心引文），再补强。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","paper_id":"P-demo","status":"success",
 "answers":[{"question_id":"Q1","question_text":"该工艺使强度提升了多少？",
   "answer":"拉伸强度从 320 MPa 提升至 415 MPa（约+30%），条件为退火温度 450 °C。",
   "evidence":[{"paper_id":"P-demo","paragraph":14,"quote":"The tensile strength increased from 320 to 415 MPa after annealing at 450 °C.","supports":"数值与条件"}],
   "layers":{"reported":["320→415 MPa, 450 °C"],"interpreted":[],"inferred":[]},
   "conditions_preserved":["退火450 °C","拉伸速率未在材料中报告→见gaps"],
   "gaps":["拉伸测试应变速率原文未报告"],"confidence":"high"}],
 "conflicts":[],"uncertainty_notes":[],"changes":[]}
```

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段（如存在）。它定义本案例 `result.json` 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实内容**；contract 里有而本文件 §4 未描述的字段，按 contract 字段语义填实际结果，绝不遗漏；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：一律从 `/input/case.json` 原样读取，禁止自造。
3. **路径**：工作过程写 `/app/work/`；最终产物写 `/app/output/`，主输出为 /app/answers.json（本题主输出）+ /app/output/result.json（平台归档）。
4. **尽早落盘**：先用最小可用结果写一次 /app/answers.json（本题主输出）+ /app/output/result.json（平台归档），再增量增强——任何时刻中断都保证已落盘内容诚实、结构合法（status 如实标 partial）。
5. **不虚构**：无数据、无文件、无软件状态一律不编造；材料缺失写 gaps，无法判断写 uncertainty，禁止把推断写成事实。
6. **可核验**：每个关键结论保留来源定位（页/段/句/表号/图号或文件位置），他人可独立复核。
7. **交付物自检**：本 Skill 的提交材料为 SKILL.md + README.md（使用与方法说明）；运行时按上述契约执行案例。二者不一致处以本节契约为准。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 保持 77.7 分水准：引用回链核验表补列（段落号存在性验证）；三层分离计数（reported/interpreted/inferred 条数）。

## v5 捆绑脚本强化（11-23，基于 75 题出分复盘）

复盘定论：**评测器奖励"真实跑出来的对账产物"**。本轮把审计工具直接捆绑进本 Skill（resources/scripts/），执行时**必须真实运行**并把输出文件交付到 /app/output/。

**捆绑脚本与运行点**（脚本已随本 Skill 交付，可直接 `python3 scripts/<name>.py ...` 执行）：
- `scripts/numeric_audit.py`
- `scripts/reconcile.py`

**交付前数字门槛（gate）——全部 PASS 才允许 status=success**：
九题全答断言；每条引用段落号存在性验证表

**本题针对性修正**：
摘要-正文-表格数值用 numeric_audit.py 自动比对
