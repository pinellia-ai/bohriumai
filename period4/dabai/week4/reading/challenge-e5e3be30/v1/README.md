# README — challenge-e5e3be30 文献证据溯源与事实核验 (v1)

## 交付标准清单（从题面提取）

- 接口（组织方修订 v2）：读 `/input/claims-to-verify.json` 的实际待核验论断（它们是问题，不是权威事实）。复合论断拆解后对完整原文语境做蕴含判定，四级：`supported / partially_supported / contradicted / insufficient_evidence`。保留比较对象（comparator）、否定词（negation）、显著性（significance）与条件限定（conditions）。**无依据外推不是被实验否定；来源冲突需双方定位 + qualified verdict。**
- 四关注：拆得开（不漏不重）/ 找得到（最小充分证据精确到段落/句子）/ 判得准（"部分支持/不支持"与"主题相关"区分开）/ 说得清（冲突、限制、无法确定明确写出）。
- 前人教训（PLAYBOOK §3）：引用核验题每条核验必须带原文位置引用，此前曾因无定位引用得 6 分，重写后 66 分。
- 输出：`/app/output/result.json`，完整链条 论断→证据片段→原文定位→支持度→判定理由，逐链可独立复核。

## 文件

- `SKILL.md` — 五步流水线（论断拆解→证据检索→四级蕴含判定→冲突与限制→校验落盘），判定规则含 comparator/negation/significance/conditions 四保留项
- `scripts/validate_verdicts.py` — claim 覆盖/枚举/quote 子串匹配/contradicted 必须有引文+理由校验，带 `--selftest`

## 自测记录（2026-11-25）

- [x] YAML frontmatter 可解析
- [x] output_contract 全字段覆盖（claims[].subjudgments[].verdict/evidence/rationale、limitations、conflicts、searched_scope 等）
- [x] validate_verdicts.py ast.parse 通过；`--selftest` 实跑（含 supported/partially_supported/contradicted/insufficient_evidence 四级各例，quote 语料子串匹配）0 error
- [x] 无虚构：不含题面外接口
- [x] 资源限额：4 文件 / <35KB
