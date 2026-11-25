---
name: evidence-verification-claims
description: |
  文献证据溯源与事实核验 Skill：读 /input/claims-to-verify.json 的待核验论断（它们是问题
  不是权威事实），把复合论断拆成事实/比较/因果/范围子判断，逐条定位最小充分证据（章节+
  段落+逐字引文），按四级支持度判定 supported / partially_supported / contradicted /
  insufficient_evidence。判定必须在完整原文语境下做蕴含检查：保留比较对象、否定词、显著性
  与条件限定；"主题相关"不等于"支持"；无依据的外推不是被实验否定（contradicted 需原文
  明确相反陈述）；来源冲突并列双方定位给出 qualified verdict。不编造，逐链可复核。
---

# 证据溯源与事实核验 Skill（evidence-verification-claims）

## 1. 用途与适用范围

- 用途：输入论文材料与待核验论断清单，输出论断拆解 → 证据卡片（定位+逐字引文）→ 四级支持度判定 → 判定理由的完整链条，供他人独立复核。
- 适用：带段落定位的文本材料；论断清单形式（claims-to-verify.json）。
- 四关注：拆得开（复合论断拆子判断不漏不重）、找得到（最小充分证据精确到段落/句子）、判得准（四级判定与原文表述相符，"部分支持/不支持"与"主题相关"区分开）、说得清（冲突、样本限制、无法确定的内容明确写出）。
- 核心原则：**论断是问题，不是事实；主题相关≠支持；无依据外推≠被否定。**

## 2. 输入识别（Step 0，必做）

1. 读 `/input/claims-to-verify.json`：逐条登记 claim_id 与论断文本。文件缺失 → status=failed，不虚构论断。
2. 读 `/input/case.json`：case_id、材料清单、output_contract。
3. 盘点材料：段落总数、表格、图注、参考文献著录；登记各来源定位键。材料缺失 → failed。
4. 建目录 `/app/work/`、`/app/output/`。

## 3. 工作流程（5 步流水线）

### Step 1 论断拆解（产出 work/claim-split.json）
- 把每条论断拆成可独立核验的子判断，类型标注：`fact`（事实）、`comparison`（比较，含比较对象与方向）、`causal`（因果）、`scope`（范围/条件限定）。
- 复合句逐个谓词拆：一条论断含两个事实+一个因果 → 三条子判断，不漏不重。
- 每条子判断登记所需证据类型（数值/统计量/原文陈述）。
- 验收断言：每条 claim 至少 1 条子判断；子判断并集还原原论断。

### Step 2 证据检索（产出 work/evidence-search.json）
- 为每条子判断检索最小充分证据：候选段落 → 完整语境通读（上下文至少前后各一段，表格看整表）→ 选出最小充分集合。
- 登记检索过哪些章节；无证据 → 记录检索范围，进 Step 4 的 insufficient_evidence。
- 验收断言：证据片段逐字存在于所标位置（quote 子串匹配）。

### Step 3 蕴含判定（逐子判断，四级）
- `supported`：原文明确支持全部要素（事实、方向、量级、条件）。
- `partially_supported`：支持核心但原文限定更窄/量级不同/条件不完全满足。
- `contradicted`：原文有明确相反陈述（方向相反或数值相反）；**无依据外推不算 contradicted**。
- `insufficient_evidence`：检索后无证据或证据不充分。
- 判定规则（防误支持）：
  - 保留比较对象（"高于 X"≠"高于 Y"）、否定词（not/no）、显著性（p 值/误差范围）、条件限定（在某条件下成立≠普遍成立）。
  - 只主题相关但谓词/方向/条件不符 → 不是 supported。
  - 摘要与正文不一致 → 双方定位并列，qualified verdict。
- 验收断言：四级枚举合法；每条判定有判定理由文本。

### Step 4 冲突与限制（产出 work/conflicts.json）
- 来源冲突：不同段落/来源给出相反或不同表述 → 并列双方 paragraph_id + 原话，verdict 标 qualified（如 partially_supported + conflict noted）。
- 样本与范围限制、适用条件、无法由原文确定的部分逐条写进 limitations，不被一句结论掩盖。

### Step 5 汇总落盘（scripts/validate_verdicts.py）
```bash
python3 /skills/weekly-skill/scripts/validate_verdicts.py --result /app/output/result.json --claims /input/claims-to-verify.json
```
校验：claim 全覆盖；verdict 枚举；supported/contradicted 的 quote 子串匹配；contradicted 必须有反方向原文引文。先落骨架再充实。

## 4. 输出契约（result.json 逐字段）

| 字段 | 要求 |
|---|---|
| `case_id` | 与输入一致 |
| `status` | `success` / `partial` / `failed` |
| `claims[]` | 每条论断一项 |
| `claims[].claim_id` / `text` | 与输入一致 |
| `claims[].subjudgments[]` | sub_id、text、type（fact/comparison/causal/scope）、required_evidence |
| `claims[].subjudgments[].verdict` | `supported` / `partially_supported` / `contradicted` / `insufficient_evidence` |
| `claims[].subjudgments[].evidence[]` | 最小充分证据：paragraph_id（或 表/图 定位）+ 逐字 quote |
| `claims[].subjudgments[].rationale` | 判定理由（为何是这个等级） |
| `claims[].verdict` | 汇总判定（全部子判断 supported → supported；含 contradicted → contradicted 或 qualified；混合 → partially_supported） |
| `claims[].limitations[]` | 样本/范围/适用条件限制、无法确定的部分 |
| `claims[].conflicts[]` | 冲突双方定位与原话并列 |
| `searched_scope` | 每条论断检索过的章节/来源 |
| `uncertainty[]` / `change_log[]` | 不确定项与修订记录 |

示例（示意，非正式案例结果）：
```json
{"case_id":"demo-ver","status":"success",
 "claims":[{"claim_id":"c1","text":"催化剂 A 在所有温度下的活性都高于催化剂 B",
   "subjudgments":[
    {"sub_id":"c1-s1","text":"在 300-350 K 内 A 的活性高于 B","type":"comparison",
     "required_evidence":"活性数值+温度条件",
     "verdict":"supported",
     "evidence":[{"paragraph_id":"p12","quote":"at all tested temperatures (300-350 K), catalyst A showed higher activity than B (94.2% vs 87.5% conversion at 320 K)"}],
     "rationale":"原文在实测温度区间内明确支持比较方向与量级"},
    {"sub_id":"c1-s2","text":"在所有温度（无范围限制）下 A 高于 B","type":"scope",
     "required_evidence":"超出实测范围的陈述",
     "verdict":"insufficient_evidence","evidence":[],
     "rationale":"原文只实测 300-350 K，'所有温度'无依据；外推不被否定，不能标 contradicted"}],
   "verdict":"partially_supported",
   "limitations":["原文仅覆盖 300-350 K，超出范围无法核验"],
   "conflicts":[]}],
 "searched_scope":{"c1":["Abstract","Results p10-p15","Tables"]},
 "uncertainty":[],"change_log":[]}
```

## 5. 数字门槛

- 论断覆盖 100%：claims-to-verify 中每条 claim 都有结果，不静默跳过。
- 证据真实率 100%：每个引用的 quote 在所标位置子串匹配；匹配不过不得提交。
- 拆解完备：复合论断的子判断并集可还原原论断；单谓词论断至少 1 条子判断。
- 判定可复核：每条判定有 rationale + 证据链（论断→证据片段→原文定位→支持度→理由）。
- contradicted 门槛：必须附原文明确相反陈述的引文；无引文的 contradicted 不合格。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| claims-to-verify.json 缺失 | status=failed，不虚构论断 |
| 检索无证据 | insufficient_evidence + searched_scope 说明检索范围 |
| 只找到部分子判断的证据 | 已核验的逐条判，缺的标 insufficient_evidence，claim 汇总 partially_supported |
| 证据主题相关但谓词不符 | 不判 supported，判 partially_supported 或 insufficient_evidence 并说明 |
| 原文明确相反陈述 | contradicted + 反方向引文（引用核验教训：无定位引用=低分） |
| 摘要与正文不一致 | 双方定位并列，qualified verdict，不仲裁 |
| 转引/跨页/图表引用 | 定位到实际承载段落；图表给图/表号+行 |
| 论断含多子判断只核验了一个 | 不许只报结论；逐子判断列出核验状态 |

## 7. 自查清单

- [ ] case_id 原样保留
- [ ] claim 100% 覆盖，子判断不漏不重
- [ ] 每条证据 quote 子串匹配、定位到段落/图表
- [ ] 四级判定与原文语气相符（保留否定/比较对象/显著性/条件）
- [ ] contradicted 均有反方向引文
- [ ] 冲突双方原话并列，未擅自仲裁
- [ ] limitations 写明样本/范围/无法确定项
- [ ] validate_verdicts.py 全项通过

## 8. 效率约束

预算内：拆解与检索按论断批量；证据一次检索成型，重读仅限冲突复核；先落骨架再充实；失败项定点修复。

## 9. 最小示例

见 §4 示意 JSON（标明为示例）。流程：论断拆解 → 证据检索 → 四级判定 → 冲突与限制 → 落盘。
