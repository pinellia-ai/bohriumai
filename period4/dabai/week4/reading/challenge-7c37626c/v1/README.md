# README — challenge-7c37626c 公式解析与数学推理 (v1)

## 交付标准清单（从题面提取）

- 四个关注点：认得准（LaTeX/MathML 结构还原不错位不丢项）、讲得清（符号表含定义位置/取值范围/单位，区分原文定义/推断/常识）、推得顺（分步推导+假设/近似/边界条件+跨公式依赖）、算得回（数值代入复算，发现符号/单位/数量级错误）。
- 输入（组织方修订）：C01/C03 提供 `artifacts/publisher-source.xml`（原始出版商 XML 原样副本）与 `artifacts/source-formulas.xml`（实际公式节点派生子集，保留 MathML 分式/上下标/来源 ID）；公式目录不是线性化答案。
- 真实缺失分支：C02 类快照无公式表示/逐条预测/可复算数据 → 可核对明确指标与条件；需缺失对象的推导/复算报 `partial` 或 `insufficient_evidence`，**不得反推公式或把未知填 0**。
- 输出：`/app/output/result.json`，含 case_id、公式、符号表、推导、核验、证据定位、状态、不确定性、变更记录。

## 文件

- `SKILL.md` — 六步流水线（公式清点→结构还原→符号表→分步推导→数值核验→缺失分支与落盘）
- `scripts/numeric_check.py` — AST 白名单安全求值（禁任意调用），中间值/偏差/数量级检查，除零与非法输入标 unverifiable，带 `--selftest`

## 自测记录（2026-11-25）

- [x] YAML frontmatter 可解析
- [x] output_contract 全字段覆盖（formulas/symbols/derivations/verifications/answers/not_reported/evidence/uncertainty/change_log）
- [x] numeric_check.py ast.parse 通过；`--selftest` 实跑三例：Arrhenius 代入 consistent（deviation 1.4%）、除零 unverifiable、注入调用被拒绝 unverifiable
- [x] 无虚构：不含题面外接口；缺失分支按题面原文保留
- [x] 资源限额：4 文件 / <30KB
