---
name: outcome-translator-multi-audience
description: |
  科研成果转化写作 Skill。受众适配（解释深度/术语密度/类比方式按读者调整）、内容取舍
  （必须保留/可压缩/可删除分级，压缩不删证据）、科学事实保真（数值/单位/口径/样本量与
  源文一致，不确定性规范表达）、术语表跨文体锁定、论断强度与证据匹配（相关不写因果）。
  输出转化稿 + 保留优先级表 + 术语表。
---

# Outcome Translator — 科研成果转化写作 Skill

## 1. 用途与适用范围

同一成果在不同读者面前**可读且不失准确**：读得懂（无未展开缩写/行话挡路）、留得住（删冗余不删证据）、说得准（论断强度匹配证据）。支持论文→科普、技术报告→申报材料等文体转换。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、源成果材料、目标读者与文体要求。
2. 读者画像：知识背景/阅读目的/信息需求 → 定解释深度、术语密度、类比策略、篇幅。
3. 建立源文事实清单：数值/单位/口径/样本量/限定条件/图表引用——保真的对账基准。

## 3. 工作流程

### Step 1 内容取舍分级（留得住）
- 三级：`must_keep`（关键结论/限定条件/样本信息/指标口径/图表引用）/ `compressible`（方法细节可概述）/ `droppable`（冗余背景）。
- **压缩不删证据**：每条 must_keep 在成稿中有落点。

### Step 2 受众适配改写（读得懂）
- 缩写首次展开、术语换通俗说法或加一句话解释、公式文字化；类比服务于理解且不失准确。
- 不把科普写成营销：语气与证据强度一致。

### Step 3 事实保真（说得准）
- 数值/单位/比较基准/样本量/统计口径与源文一致（逐个对账）。
- 论断强度匹配：相关≠因果、单样本≠共识；不确定性规范表达（"在 X 条件下""初步显示"）。

### Step 4 术语表锁定
- `{源术语, 转化文体表述, 首现处理}`——同一概念全文与多种产出说法统一；缩写首展开规则。

### Step 5 文体转换边界
- 结构要素按目标文体重组（科普：钩子→主线→结论→边界；申报：目标→方案→预期）。
- 简化表达与必须保留限定语的结论分级标注。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "outcome_translation",
  "status": "success | partial | failed",
  "audience_profile": {"background":"...","depth":"...","analogy_strategy":"..."},
  "retention_table": [{"item":"关键结论 42%","priority":"must_keep","landed_in":"成稿§2","locator":"源文Fig.3"},
                       {"item":"方法细节","priority":"compressible","landed_in":"成稿一句话"}],
  "fact_audit": [{"fact":"42%","source_loc":"源文Table1","in_output":"§2","match":true}],
  "strength_audit": [{"loc":"§3","original":"相关","output_written":"相关","ok":true}],
  "term_table": [{"src":"pyroptosis","out":"细胞焦亡（程序性细胞死亡的一种）","first_use":"§1"}],
  "output_files": {"draft":"converted.md","editable":true},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：fact_audit 全对账；retention_table 的 must_keep 全部 landed；strength_audit 无升级；term_table 锁定执行。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 目标读者信息缺失 | 按文体惯例画像 + uncertainty 声明 |
| 类比失准风险 | 弃用类比改直白解释 |
| 预算不足 | 取舍表+核心转化稿先行（partial） |

## 6. 自查清单

1. [ ] 读者画像驱动解释深度？
2. [ ] must_keep 全部落稿？删的是冗余不是证据？
3. [ ] 数值/口径逐个对账？论断强度无升级？
4. [ ] 术语全文统一？缩写首展开？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。事实清单与取舍表先行；转化稿按块生成即落盘；对账脚本化。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 交付量化对账：fact_audit.csv（事实/源文定位/成稿位置/match）逐条；retention_table 三级分级计数；strength_audit 无升级断言。
