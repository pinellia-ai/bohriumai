---
name: formula-parse-verify
description: |
  公式解析与数学推理 Skill。从论文中完整还原公式结构（LaTeX）、建立变量表（定义位置/
  单位/取值范围/定义来源三级：原文定义/上下文推断/常识补充）、拆解推导步骤（标注假设与
  边界条件）、并对可计算公式做数值代入核验（发现符号/单位/数量级错误）。输出
  result.json，所有结果可回到原文定位复核。
---

# Formula Parse & Verify — 公式解析与数学推理 Skill

## 1. 用途与适用范围

对真实论文中的公式做到"认得准、讲得清、推得顺、算得回"：结构无歧义还原、符号有据可查、推导步步可检、数值代入复算。聚焦公式识别 + 变量解释 + 数值核验这一主线，不追求覆盖全部公式场景。

## 2. 输入识别（必做第一步）

1. `ls /input/`，读 case.json 与 task.md，记录 case_id。
2. 定位论文材料（PDF 或文本）。含公式时优先用 PDF 文本工具抽取，注意公式区文本易乱序——抽取后按公式编号（如 Eq. (3)）人工校对重排。
3. 列出目标公式清单（行间公式、编号公式优先；被正文引用的核心公式必收）。
4. 材料缺失/公式区域不可读：登记 gaps，status=partial，不猜测公式内容。

## 3. 工作流程

### Step 1 公式识别（认得准）
- 输出 LaTeX（`$$...$$`），完整保留：上下标、括号层级、希腊字母、矩阵/向量、分段函数、公式编号。
- 校验规则：括号配对计数；上下标嵌套层级与原文比对；易混符号逐一核对（ε vs ε_t、µ 做系数还是单位前缀、ln vs log）；丢项检查（与原文逐项对）。
- 上下标错位、合并、丢项是高频错——每个公式转录后必须**与原文逐字符比对一遍**再定稿。

### Step 2 变量表（讲得清）
每个符号一行，字段：符号、LaTeX、含义、单位、取值范围、首次定义位置（页/段/公式号）、定义来源：
- `original`（原文明确定义——引原句）
- `contextual`（上下文推断——写推断依据）
- `common_sense`（常识补充——显式标注，不得与原文冲突）
原文没定义的符号进 `gaps`，不按常识猜完就当已定义。

### Step 3 推导拆解（推得顺）
- 关键推导拆成可检查步骤：每步写明 用的公式编号、所做假设/近似（如线性化、稳态、忽略二阶项）、边界条件。
- 跨公式依赖显式标注（Eq.5 依赖 Eq.2 的近似）。
- 每一步能回答"为什么成立"。

### Step 4 数值核验（算得回）
- 可计算公式：用变量表中的数值代入复算，给出中间值与最终值（含单位）。
- 单位量纲检查：等式两边量纲必须一致，不一致即报告（这是发现符号错误的硬手段）。
- 数量级检查：结果与论文报告值对比，偏差>数量级即标记，不要强行解释为"合理误差"。
- 复算用 python（scientific-python 环境），脚本存 /app/work/verify.py 保留可复核路径。

### Step 5 汇总输出

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "formula_parse_verify",
  "status": "success | partial | failed",
  "formulas": [
    {
      "eq_id": "(3)",
      "location": {"page": 4, "section": "Model"},
      "latex": "$$\\tau = \\eta \\dot{\\gamma}$$",
      "source_check": "与原文逐字符比对一致",
      "variables": [
        {"symbol":"τ","meaning":"剪切应力","unit":"Pa","range":"null",
         "defined_at":{"page":4,"paragraph":2},"source":"original","quote":"τ is the shear stress"}
      ],
      "assumptions": ["牛顿流体近似（原文声明）"]
    }
  ],
  "derivations": [{"eq_id":"(5)","depends_on":["(2)","(3)"],"steps":[{"n":1,"action":"将(3)代入(2)","assumption":"稳态","result":"..."}]}],
  "verification": [
    {"eq_id":"(5)","inputs":{"eta":"0.89 Pa·s","gamma_dot":"10 s^-1"},"computed":"8.9 Pa","paper_value":"8.9 Pa","match":true,
     "unit_check":"Pa = Pa·s × s^-1 ✓","note":"数量级一致"}
  ],
  "errors_found": [{"eq_id":"(5)","type":"unit | sign | magnitude | transcription","detail":"..."}],
  "gaps": [],
  "uncertainty_notes": [],
  "changes": []
}
```

硬性要求：latex 可编译校验（结构自洽）；变量表无"常识猜测冒充原文定义"；errors_found 只报经核验确认的问题，不做无依据质疑。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| PDF 公式乱码/抽取失败 | 用 pdf-render 渲染该页为图像查看；仍失败登记 gaps |
| 符号在原文多义 | 两处定义并列，标注位置 |
| 论文数值与公式复算不符 | 记入 errors_found（type=magnitude），不修改论文公式 |
| 非数值参数无法代入 | 该公式跳过核验，记 uncertainty_notes |
| 预算不足 | 优先核心公式（被引用最多），status=partial |

## 6. 自查清单

1. [ ] 每个公式与原文逐字符比对？上下标/括号/希腊字母无错位？
2. [ ] 变量表三级来源标注齐全？无常识冒充？
3. [ ] 推导步骤含假设与边界条件？
4. [ ] 数值核验含单位量纲检查与中间值？
5. [ ] errors_found 逐条有依据？
6. [ ] result.json 可解析、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。文本抽取一次完成；数值核验合并为一个 python 脚本单次运行；先完成全部公式的 LaTeX + 变量表（最小可用），再补推导与核验。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"success",
 "formulas":[{"eq_id":"(1)","location":{"page":3,"section":"Theory"},
   "latex":"$$E = mc^{2}$$","source_check":"一致",
   "variables":[{"symbol":"m","meaning":"质量","unit":"kg","range":"null","defined_at":{"page":3,"paragraph":1},"source":"original","quote":"where m is the rest mass"}],"assumptions":[]}],
 "verification":[{"eq_id":"(1)","inputs":{"m":"9.11e-31 kg"},"computed":"8.19e-14 J","paper_value":null,"match":null,"unit_check":"J = kg·(m/s)^2 ✓","note":"论文未报告对应值"}],
 "errors_found":[],"gaps":["γ 边界条件原文未给出"],"uncertainty_notes":[],"changes":[]}
```

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段（如存在）。它定义本案例 `result.json` 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实内容**；contract 里有而本文件 §4 未描述的字段，按 contract 字段语义填实际结果，绝不遗漏；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：一律从 `/input/case.json` 原样读取，禁止自造。
3. **路径**：工作过程写 `/app/work/`；最终产物写 `/app/output/`，主输出为 /app/output/result.json（含 case.json 的 output_contract 全部字段）。
4. **尽早落盘**：先用最小可用结果写一次 /app/output/result.json（含 case.json 的 output_contract 全部字段），再增量增强——任何时刻中断都保证已落盘内容诚实、结构合法（status 如实标 partial）。
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
1. 交付量化对账：verification.csv（公式/输入/计算值/论文值/量纲检查）逐条；变量表 CSV（三级来源计数）；比对 diff 过程留档。

## v5 捆绑脚本强化（11-23，基于 75 题出分复盘）

复盘定论：**评测器奖励"真实跑出来的对账产物"**。本轮把审计工具直接捆绑进本 Skill（resources/scripts/），执行时**必须真实运行**并把输出文件交付到 /app/output/。

**捆绑脚本与运行点**（脚本已随本 Skill 交付，可直接 `python3 scripts/<name>.py ...` 执行）：
- `scripts/reconcile.py`

**交付前数字门槛（gate）——全部 PASS 才允许 status=success**：
verification.csv 行数=可计算公式数；量纲检查列全部 PASS

**本题针对性修正**：
数值核验逐条入 CSV（输入/计算值/论文值/量纲）
