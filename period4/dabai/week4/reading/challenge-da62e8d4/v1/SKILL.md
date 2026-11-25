---
name: reproduction-verification-attribution
description: |
  论文复现与方法验证 Skill（本版子场景：参数/代码/指标验算与差异归因）：读运行包内两份
  候选数值方法，核对原始来源、实际环境与事前容差；把论文/附录/代码默认值的参数冲突对齐成
  可执行参数表（取值依据三级：论文明确给出/从代码推断/自行设定），运行后与论文指标按
  事前容差对比，差异归因到环境/数据/实现/论文描述不足，输出 reproduced / partially_reproduced /
  not_reproduced 分级结论。组织方合成试验不是原作者代码或物理实验；缺失原始数据/仓库如实
  保留并登记，不虚构，不把未知填 0，所有结论带原文/材料定位。
---

# 复现验算与差异归因 Skill（reproduction-verification-attribution）

## 1. 用途与适用范围

- 用途：给定论文材料与运行包（含两份候选数值方法实现），完成：参数复原表 → 实际环境记录 → 按论文参数运行 → 指标对比（事前容差）→ 差异归因 → 分级复现结论。
- 适用：运行包内可执行的数值方法脚本；论文正文/附录中可定位的参数与指标。
- 边界（本版明确）：组织方合成试验不是原作者代码、物理实验或全量复现；**缺失原始数据/仓库必须显式登记，不默默跳过**。
- 四关注：找得齐（材料定位到具体版本）、跑得对（按论文复原而非默认值）、对得上（偏差落在事前容差内）、讲得清（归因可核验）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：case_id、任务说明、材料清单（论文正文/附录、运行包、事前容差声明）、output_contract。
2. 盘点运行包：两份候选数值方法（脚本/配置/README）逐份登记路径、入口、依赖、随机种子支持。
3. 找事前容差：容差必须在运行**之前**从材料中显式读出并写死（如 "±5% or ±0.01 absolute"）；材料未声明容差 → tolerance_basis="not declared"，登记并在结论降级。禁止先看结果再定容差。
4. 缺失项（原始数据/仓库/评价脚本）逐项登记到 missing_items，不虚构。
5. 建目录 `/app/work/`（过程）、`/app/output/`（result.json）。

## 3. 工作流程（6 步流水线）

### Step 1 材料定位表（产出 work/material-checklist.json）
- 从论文正文/附录/运行包抽取必需材料：代码、数据、参数、依赖、许可证，各登记：来源（论文段落/附录节/包路径）、版本、缺失状态。
- 验收断言：每个材料项有来源定位或显式 missing。

### Step 2 参数复原表（产出 work/parameter-table.json）
- 对齐论文正文、附录与代码默认值中的同一参数；冲突时三方并列，**不得静默采用任何一方**。
- 每个关键参数记录取值依据三级：
  - `paper_explicit`：论文明确给出（定位 paragraph_id/附录节）；
  - `code_inferred`：从代码/配置推断（定位文件+行）；
  - `self_set`：论文与代码均未给，自行设定（必须说明理由，标记为复现者选择）。
- 实际运行取值 = paper_explicit 优先；无则 code_inferred；最后才 self_set。
- 验收断言：每个关键参数三级依据之一，冲突三方保留原值与出处。

### Step 3 环境记录（产出 work/environment.json）
- 记录 Python 版本、依赖及版本、硬件要点、随机种子、关键系统设置（按实际环境）。
- 与论文声明不一致之处（如论文说 Python 3.10 实际 3.12）逐项登记 environment_deviations。

### Step 4 运行两份候选方法
- 按参数表设定（非默认值）运行两份候选数值方法；保存命令行、stdout 日志、输出指标到 work/run-<method>.json。
- 运行失败 → 保留错误日志，status 登记 failed-run，进入归因而非跳过。

### Step 5 指标对比与差异归因（scripts/tolerance_check.py）
```bash
python3 /skills/weekly-skill/scripts/tolerance_check.py --spec work/compare-spec.json
```
- compare-spec：{"comparisons":[{"metric":"rmse","reproduced":0.412,"reported":"0.41","source":"Table 2, p05","tolerance":{"type":"relative","value":0.05}}]}
- 脚本计算绝对/相对偏差，对照事前容差，判定 within_tolerance / out_of_tolerance，输出可复算的中间值。
- 归因条目：每条 out_of_tolerance 差异归因到 environment / data / implementation / paper_description_insufficient / candidate_method_mismatch 之一，附证据（日志行、参数表行、论文定位）。无法归因如实写 cannot-attribute。

### Step 6 分级结论与落盘（/app/output/result.json）
- 先落骨架（case_id + status + 参数表占位），再充实。
- 结论分级：`reproduced`（全部关键指标 within 容差）/ `partially_reproduced`（部分 within，逐条列出哪些）/ `not_reproduced`（全部 out）+ 依据。

## 4. 输出契约（result.json 逐字段）

| 字段 | 要求 |
|---|---|
| `case_id` | 与输入一致 |
| `status` | `success` / `partial`（存在 failed-run 或缺失项）/ `failed` |
| `material_checklist[]` | 材料项、来源定位、版本、missing 状态 |
| `parameter_table[]` | 参数、paper 值/出处、code 值/出处、used 值、basis（paper_explicit/code_inferred/self_set）、conflict 说明 |
| `environment` | 实际环境快照 + environment_deviations[] |
| `runs[]` | 两份候选方法各一条：method_id、命令、seed、输出指标、日志路径 |
| `comparison[]` | metric、reproduced、reported（+论文定位）、tolerance（事前声明+定位）、deviation、verdict（within_tolerance/out_of_tolerance/unverifiable） |
| `attribution[]` | 每条差异：cause 枚举、证据定位、可选修复建议 |
| `conclusion` | reproduced / partially_reproduced / not_reproduced + 依据条目 |
| `missing_items[]` | 原始数据/仓库等缺失项（显式保留） |
| `uncertainty[]` / `change_log[]` | 不确定项与修订记录 |

示例（示意，非正式案例结果）：
```json
{"case_id":"demo-rep","status":"partial",
 "parameter_table":[
  {"parameter":"learning_rate","paper_value":"0.01","paper_loc":"p05",
   "code_value":"0.001","code_loc":"config.yaml:8","used_value":0.01,
   "basis":"paper_explicit","conflict":"论文 0.01 vs 代码默认 0.001，按论文取"},
  {"parameter":"random_seed","paper_value":null,"code_value":null,
   "used_value":42,"basis":"self_set","conflict":null}],
 "environment":{"python":"3.12.1","deps":["numpy 2.1"],"seed":42,
   "environment_deviations":["论文未声明 Python 版本"]},
 "runs":[{"method_id":"candidate-A","command":"python methodA.py --lr 0.01","seed":42,
   "metrics":{"rmse":0.412},"log":"work/run-A.log"}],
 "comparison":[{"metric":"rmse","reproduced":0.412,"reported":"0.41","reported_loc":"Table 2, p05",
   "tolerance":{"type":"relative","value":0.05,"declared_at":"task.md §tolerance"},
   "deviation":"0.49%","verdict":"within_tolerance"}],
 "attribution":[],
 "conclusion":{"level":"partially_reproduced","basis":"candidate-A 的 rmse 在容差内；candidate-B 运行失败见 runs"},
 "missing_items":["原始训练数据未随包提供，按合成数据运行"],
 "uncertainty":[],"change_log":[]}
```

## 5. 数字门槛

- 参数表覆盖：任务指定的全部关键参数 100% 入表，三级依据之一，冲突不静默。
- 容差先行：compare-spec 的 tolerance 必须有 declared_at 定位；无声明容差的对比不得出 within 结论，只能标 unverifiable。
- 对比可复算：comparison 每条 deviation 可由 reproduced/reported 复算。
- 归因全覆盖：每条 out_of_tolerance 必有 attribution 条目；cannot-attribute 也是合法归因但需说明尝试过什么。
- 缺失显式：missing_items 不为空时不允许结论为无保留的 reproduced。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 运行包缺两份候选之一 | runs 登记 missing，结论降 partial |
| 原始数据缺失 | missing_items 显式登记；合成/替代数据运行须注明，结论不冒充全量复现 |
| 无事前容差声明 | tolerance_basis=not declared，对比标 unverifiable |
| 依赖冲突无法安装 | environment 登记，status=partial，不虚构成功运行 |
| 运行报错 | 保留日志，failed-run 进入归因 |
| 两候选方法结果不同 | comparison 按 method_id 分列，差异归因到 candidate_method_mismatch 或实现差异 |
| 论文描述不足无法复原参数 | basis=self_set + 理由；差异归因 paper_description_insufficient |
| 仓库不可访问 | missing_items 登记，不猜仓库内容 |

## 7. 自查清单

- [ ] case_id 原样保留
- [ ] 材料定位表逐项有出处或 missing
- [ ] 参数表三级依据、冲突三方保留
- [ ] 容差在运行前读出并有 declared_at
- [ ] 两候选方法均有 runs 记录（或显式 missing）
- [ ] comparison 偏差可复算、verdict 对照事前容差
- [ ] out_of_tolerance 全部有归因
- [ ] missing_items 显式，结论分级如实
- [ ] tolerance_check.py 校验通过

## 8. 效率约束

预算内：参数表与环境一次成型；两方法顺序运行、日志即存即用；先落骨架再充实；失败项定点修复不重跑全流程。

## 9. 最小示例

见 §4 示意 JSON（标明为示例）。流程：材料定位 → 参数表 → 环境 → 运行 → 容差对比 → 归因 → 分级结论。
