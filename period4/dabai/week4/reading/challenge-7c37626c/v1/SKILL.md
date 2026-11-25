---
name: formula-parsing-math-verification
description: |
  公式解析与数学推理 Skill：从论文（含 publisher/source XML 与 MathML 公式节点）还原
  公式的结构化 LaTeX、符号表、分步推导与数值核验。方法主线：公式清点（source-formulas.xml
  的实际公式节点与来源 ID）→ 认得准（上下标/括号层级/希腊字母/单位逐项还原）→ 讲得清
  （符号表：定义位置/取值范围/单位，区分原文定义与推断）→ 推得顺（分步推导+假设与边界
  条件）→ 算得回（数值代入复算，可发现符号/单位/数量级错误）。真实缺失如实报
  partial/insufficient_evidence，不反推公式、不把未知填 0，不编造。
---

# 公式解析与数学推理 Skill（formula-parsing-math-verification）

## 1. 用途与适用范围

- 用途：输入论文材料（含 MathML 公式节点）与任务问题，输出公式目录、结构化 LaTeX、符号表、推导步骤与数值核验结论，全部回到原文定位。
- 适用：`artifacts/publisher-source.xml`（原始出版商 XML）与 `artifacts/source-formulas.xml`（其中实际公式节点的派生子集，保留 MathML 分式/上下标/来源 ID）。
- 真实缺失分支：若案例（如 C02 类快照）没有公式表示、逐条预测或可复算原始数据——**保留这一缺失**：可以核对明确指标与条件；需要缺失对象的推导/复算必须报告 `partial` 或 `insufficient_evidence`。不得反推公式或把未知填 0。
- 四个关注点：认得准 / 讲得清 / 推得顺 / 算得回。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：case_id、任务说明、问题清单、材料清单、output_contract 全字段。
2. 盘点材料：
   - `artifacts/publisher-source.xml` 存在 → 记录文档结构与公式总数。
   - `artifacts/source-formulas.xml` 存在 → 这是公式工单：逐节点登记公式 ID 与 MathML 结构。
   - 两者都无公式表示 → 走缺失分支（§3 Step 6），不虚构。
3. 材料缺失 → status=failed，不虚构。
4. 建目录 `/app/work/`、`/app/output/`。

## 3. 工作流程（6 步流水线）

### Step 1 公式清点（产出 work/formula-inventory.json）
- 从 source-formulas.xml 逐节点提取：formula_id、MathML 树、所在上下文（章节/段落/公式编号）。
- 行间公式与行内公式分开登记；矩阵/分段函数标注结构类型。
- 验收断言：公式节点数与 XML 中实际节点数一致，无遗漏无虚构。

### Step 2 认得准：结构还原（产出 work/formulas.json）
- MathML → LaTeX：分式（\frac）、上下标（^/_）、希腊字母、括号层级、单位逐项对应；不错位、不合并、不丢项。
- 还原后逐项自检：上下标层数一致、括号配对、希腊字母表对照（\alpha..\omega）。
- 验收断言：每个 formula_id 有 latex 与 mathml 双表达；无法确定的结构标 uncertain 并说明歧义点，不猜。

### Step 3 讲得清：符号表（产出 work/symbol-table.json）
- 每个符号一行：符号、含义、单位、取值范围、**首次定义位置（paragraph_id/公式 ID）**、定义来源分级：
  - `defined`：原文明确给出定义；
  - `inferred`：由上下文推断（注明推断依据）；
  - `common`：常识补充（必须显式标注，不得混入原文定义）。
- 验收断言：公式中出现的每个符号都有符号表行；无定义的标 no-definition-in-source。

### Step 4 推得顺：分步推导（产出 work/derivations.json）
- 把关键推导拆成可检查的步骤：每步给 输入公式/依赖（跨公式引用 formula_id）/所用假设与近似/边界条件/得到的结果式。
- 每步须能回答"这一步为什么成立"；假设（如忽略某项、稳态近似）显式标出。
- 材料未给出推导过程时：如实登记"原文未给推导"，可标注为原文未报告，不得倒装成原文结论。

### Step 5 算得回：数值代入核验（scripts/numeric_check.py）
```bash
python3 /skills/weekly-skill/scripts/numeric_check.py --spec work/verify-spec.json
```
- verify-spec：{"formula_id","expression":"a*b/(c+d)","variables":{"a":{"value":1.2,"unit":"m"},"c":{"value":0,"unit":"s"}},"expect":"~3.2e2","unit":"m/s"}
- 脚本用 AST 白名单求值（+ - * / ** ()、math 函数白名单），先查除零/量纲常识（单位不一致告警），输出中间值与最终值；与论文报告值比数量级（差 ≥3 个数量级 → 报告 mismatch 供人工复核）。
- 代入无解（缺变量值/除零/负数开方）→ 记 unverifiable，不硬算。

### Step 6 缺失分支与落盘
- C02 类案例（无公式表示/无逐条预测/无可复算数据）：核对明确指标与条件照常做；推导/复算类问题逐条标 `insufficient_evidence`（原因：source contains no formula representation / no reproducible raw data）。
- result.json 先落骨架（case_id+status+公式/问题占位），再充实。

## 4. 输出契约（result.json 逐字段）

| 字段 | 要求 |
|---|---|
| `case_id` | 与输入一致 |
| `status` | `success` / `partial` / `failed`（材料缺失）/ 缺失分支如实降级 |
| `formulas[]` | formula_id、mathml、latex、位置（section/paragraph_id/公式编号）、uncertain 项 |
| `symbols[]` | symbol、meaning、unit、range、defined_at（paragraph_id/formula_id）、definition_source（defined/inferred/common） |
| `derivations[]` | step、input_formulas、dependencies、assumptions、boundary_conditions、result |
| `verifications[]` | formula_id、代入变量与值（含单位）、中间值、计算值、论文报告值、deviation、verdict（consistent/magnitude_mismatch/unverifiable） |
| `answers[]` | 按任务问题的逐题回答，附定位 |
| `not_reported[]` | 原文未报告项（含缺失分支原因） |
| `evidence` | 每个关键结论的 XML 节点/段落定位与原文引文 |
| `uncertainty[]` | 符号歧义、结构不确定、单位缺失等 |
| `change_log[]` | 修订记录 |

示例（示意，非正式案例结果）：
```json
{"case_id":"demo-f01","status":"success",
 "formulas":[{"formula_id":"eq-2","latex":"k = A \\, e^{-E_a/(R T)}","mathml":"<math>...</math>",
              "location":{"section":"3.2","paragraph_id":"p14"},"uncertain":[]}],
 "symbols":[{"symbol":"E_a","meaning":"activation energy","unit":"kJ/mol","range":null,
             "defined_at":"p14","definition_source":"defined"}],
 "derivations":[{"step":1,"input_formulas":["eq-2"],"dependencies":[],
                 "assumptions":"Arrhenius behaviour in 300-350 K",
                 "boundary_conditions":"T in [300,350] K","result":"ln k = ln A - E_a/(R T)"}],
 "verifications":[{"formula_id":"eq-2","inputs":{"A":{"value":1e6,"unit":"s^-1"},"E_a":{"value":50,"unit":"kJ/mol"},"T":{"value":320,"unit":"K"},"R":{"value":8.314,"unit":"J/mol/K"}},
                   "computed":"3.55e-3 s^-1","reported":"3.5e-3 s^-1","deviation":"1.4%",
                   "verdict":"consistent"}],
 "answers":[],"not_reported":[],"evidence":{},"uncertainty":[],"change_log":[]}
```

## 5. 数字门槛

- 公式覆盖 100%：source-formulas.xml 中每个节点都要出现在 formulas[]，缺失即 partial。
- 符号覆盖 100%：公式中每个不同符号必须有符号表行（可为 no-definition-in-source，不可缺行）。
- 推导可检查：每步有假设/依赖标注，缺标注不合格。
- 核验可复算：verifications 的每个数值可由 inputs 复算出来；算不出的标 unverifiable。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 无公式表示（C02 类） | 缺失分支：核对指标条件，推导/复算标 insufficient_evidence，不反推 |
| 公式图像/截断无法还原 | formulas[].uncertain 登记歧义点，status=partial |
| 符号一词多义 | 逐处登记含义，注明歧义，不合并 |
| 单位缺失 | unit=null + uncertainty 登记；代入核验标 unverifiable |
| 代入除零/无解 | unverifiable，不硬算不填 0 |
| 计算值与论文差 ≥3 数量级 | magnitude_mismatch，报给人工复核，不擅自改论文值 |
| publisher XML 与正文公式不一致 | 双方定位并列，status 降 partial |
| 领域标签与实际内容不符 | 以实际输入文件为准，不按标签补造 |

## 7. 自查清单

- [ ] case_id 原样保留
- [ ] 公式节点 100% 清点，MathML/LaTeX 双表达
- [ ] 符号表全覆盖，定义来源三级（defined/inferred/common）未混淆
- [ ] 推导每步有假设/边界/依赖
- [ ] 数值核验可由 spec 复算，中间值齐全
- [ ] 缺失分支如实 partial/insufficient_evidence，未知未填 0
- [ ] numeric_check.py 校验通过
- [ ] uncertainty 与 change_log 完整

## 8. 效率约束

预算内：公式清点与还原一次成型；核验 spec 批量生成、脚本一次跑通；先落骨架再充实；失败项定点修复。

## 9. 最小示例

输入（示意）：source-formulas.xml 含一个节点：`<math><apply><divide/><ci>k</ci><ci>T</ci></apply></math>`（p14，行间）。
输出（示意，标明为示例）：formulas[] 记 latex `k / T`、location p14；symbols[] 记 k、T 两行；若任务要求复算但材料无 k、T 数值 → verifications[] 标 unverifiable（原因：values not reported）。
