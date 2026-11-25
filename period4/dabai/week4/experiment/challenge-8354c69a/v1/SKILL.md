---
name: result-interpretation-anomaly-analysis
description: |
  把一轮实验数据（表格读数/曲线trace/图谱读数/多批次）解释成五段可检查结论：
  结果趋势、异常点、可能原因、复核步骤、后续实验建议。
  方法主线：先读原始数据建立基线（对照/重复）→ scripts/robust_stats.py 真实算术判读
  （稳健Z分数 median/MAD、IQR围栏、控制限、线性趋势与残差）→ 异常归因树
  （方法/仪器/样本/统计四分支逐条排除）→ 每个异常假设配可执行验证实验 →
  结论与原始数据逐条对账（每条结论回指 文件:行/列/阈值）。
  单位/方法/阈值歧义如实保留并标 ambiguity；不虚构测量值、原因与重复数。
---

# 实验结果解释与异常分析 Skill

## 1. 用途与适用范围

- 输入：实验产出数据（CSV/表格读数、曲线 trace、多批次多通道数据、设备日志）+ 方案材料（对照设置、参数、批次信息）。
- 输出：五段结构化解释（趋势/异常点/原因候选/复核步骤/后续实验），落盘 `/app/output/result.json`，每条结论可回指原始数据。
- 适用：实验完成后对读数/曲线/图谱的判读与异常分析。不适用：新方案设计、论文写作、统计方法学研究、无原始数据的纯机理 speculation。
- 核心原则：**趋势是算出来的不是复述的；异常有阈值与偏离量；原因按证据强度排序且带排除证据；复核步骤第二个人能照做；结论逐条对账到数据行。**

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id`（原样）、任务、`output_contract` 全字段（提取到 `/app/work/00_contract_fields.json`）、数据文件清单。
2. 逐个实际读数据文件（不按文件名猜）：
   - 表格：列名、单位、行数、对照组列、批次/通道/孔位维度；
   - 曲线 trace：采样间隔、每条 trace 的样本标识；
   - 日志：时间戳、事件类型。
3. 建 `/app/work/00_data_inventory.json`：
   ```json
   {"files": [{"path": "...", "kind": "table|trace|log", "rows": 0, "columns": [{"name": "...", "unit": "...", "role": "measure|control|batch|id|time"}], "issues": ["单位未标注","无对照列"]}],
    "controls": [{"file": "...", "locator": "列/行", "n": 0}],
    "ambiguities": ["threshold来源不明", "unit不一致：°C vs K"],
    "gaps": ["缺少批次B数据"]}
   ```
4. **单位/方法/阈值歧义如实保留在 ambiguities，不擅自消歧**；判读所用阈值在 result 中显式列出并标注来源。

验收断言：每个数据文件有 kind/rows/列角色标注；对照存在或 gap 记录；歧义入 ambiguities。

## 3. 工作流程（6步流水线）

### Step 1 数据加载与基线计算（脚本）
运行 `python3 scripts/robust_stats.py --data data.csv --roles roles.json --mode baseline`：
- 按对照组/重复组计算基线：median、MAD、IQR 围栏（Q1-1.5IQR, Q3+1.5IQR）、对照控制限（对照均值±3σ，n≥3 才算，否则标 insufficient_replicates）。
- 分组维度（批次/通道/孔位/时间点）逐组统计。
- 输出基线表 → `/app/work/10_baseline.json`，后续判读全部引用此表数字。

### Step 2 趋势判读（脚本+人工）
- 单指标：`--mode trend` 算线性斜率、R²、分段拐点（残差符号变化）、平台期（连续 k 点斜率≈0，k 可配）。
- 多指标：分别判读后列相互关系（同向/反向/滞后），不猜因果。
- 每条趋势结论格式：`{claim, statistic: {slope, r2, n, window}, vs_baseline: "对照区间[x,y]外", data_ref: "file:col:rows"}`。
- **趋势方向必须与脚本统计量一致；脚本说无显著趋势就不能写"明显上升"。**

### Step 3 异常点定位（脚本）
- `--mode anomalies`：稳健 Z（|0.6745(x−median)/MAD| > 3.5）∪ IQR 围栏外 ∪ 控制限外，三规则并集，输出：
  `{object: "batch2/ch5/wellA3", value, metric_z, rule_triggered, deviation: "超控制限23%", data_ref: "file:row:col"}`。
- 异常必须定位到具体对象维度（样本/批次/通道/孔位/时间点），输出异常程度（偏离量数字）与判定阈值。
- 无异常 → 明确写"在阈值 X 下未检出异常"，附阈值与检出能力说明。

### Step 4 异常归因树（核心）
对每个异常沿四分支生成候选原因，**每条候选必须列支持证据、排除证据、状态**：
```json
{"branch": "method|instrument|sample|statistics", "hypothesis": "批次2试剂降解",
 "support": ["batch2 对照读数整体偏低(10_baseline.json:ctrl_batch2 median=0.21 vs 0.35)"],
 "against": ["batch1 同试剂正常 → 指向批次特异而非试剂本身"],
 "reframe_risk": "相关≠因果：批次2恰逢换操作员",
 "status": "candidate|supported|excluded|untestable",
 "verification": {"action": "用 batch2 留存样重测对照3次", "expected_if_true": "复现低值", "expected_if_false": "读数回正常区间", "cost": "3孔×20min", "data_gap": "无留存样则untestable"}}
```
- 排序规则：有数据支持 > 有排除证据的反向强候选 > 可检验但未测 > untestable。
- **每个可检验假设必须带可执行的验证实验（动作+预期真/假结果+成本）；缺数据测不了的如实标 untestable，不编。**
- 相关误当因果风险逐条标注（reframe_risk）。

### Step 5 复核步骤与后续实验
- 复核步骤：第二个人可执行的动作——回查哪个文件的哪个字段、核对哪条设备日志、加做什么对照/重复；每步带预期结果分支。
- 后续实验：依据原因候选与证据缺口给出下一轮改动（补对照/加密采样/调参数范围/扩重复数），每条注明它将排除/支持哪条假设（与 Step 4 的 verification 互相引用）。
- 与原始数据对账：逐条结论生成 reconciliation 表——结论 ↔ 数据位置 ↔ 统计量 ↔ 阈值，任何一条对不上就改结论。

### Step 6 输出 result.json
先落最小骨架再充实。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "status": "success | partial | failed",
  "data_inventory": {"files": [], "ambiguities": [], "gaps": []},
  "trend": [{"claim": "...", "statistic": {"slope": 0, "r2": 0, "n": 0}, "vs_baseline": "...", "data_ref": "file:col:rows"}],
  "anomalies": [{"object": "batch/channel/well/timepoint", "value": 0, "metric_z": 0, "rule": "modified_z>3.5|IQR|control_limit", "deviation": "...", "data_ref": "..."}],
  "thresholds_used": [{"rule": "modified_z>3.5", "source": "Iglewicz-Hoaglin惯例", "ambiguity_note": "案例未给定阈值，采用惯例并披露"}],
  "causes": [{"branch": "...", "hypothesis": "...", "support": [], "against": [], "status": "...", "verification": {...}, "reframe_risk": "..."}],
  "verification_steps": [{"step": "回查 data.csv 第12-18行温度列", "expected": "...", "if_not": "..."}],
  "next_experiments": [{"change": "补批次2阳性对照", "tests_hypothesis": "试剂降解", "cost": "..."}],
  "reconciliation": [{"conclusion_id": "T1/A1/C1", "data_ref": "...", "statistic": "...", "threshold": "...", "match": true}],
  "unexplained": ["未覆盖指标/对照缺失部分/无法解释的偏离"],
  "evidence": [{"claim": "...", "source": "<文件>:<位置>", "quote": "原始数据行"}],
  "uncertainty": [{"item": "...", "type": "ambiguity|insufficient_replicates|missing_control|gap", "impact": "..."}],
  "confirmations_required": ["需实验人员/设备管理员确认事项"],
  "limits": "判读边界：不构成正式统计检验结论/不替代实验人员机理判断"
}
```
- 实验方案块融入 next_experiments 与 verification（含变量/对照/参数/资源/判读标准）；依据与风险=evidence+thresholds_used；确认项=confirmations_required。
- 不虚构湿实验测量值、原因结论与重复数：一切数字来自脚本对真实文件的计算。

## 5. 数字门槛

- 五段（趋势/异常/原因/复核/后续）齐备且非空壳（无异常时第三段写"未检出+阈值"）→ 否则 partial。
- 每条结论 data_ref 可回指；reconciliation 逐条 match。
- 异常三规则并集检出；阈值显式披露（案例未给则用惯例并标 ambiguity_note）。
- 重复数 <3 时趋势/控制限结论降级为 insufficient_replicates 描述性结论。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 数据缺失（整文件/整列缺） | gap 记录，相关结论不下的部分列 unexplained，status=partial |
| 单位不一致（°C vs K） | 统一换算记录换算式；不可靠则剔除并标 ambiguity，不混算 |
| 重复数不足（<3） | 不算控制限，改用稳健单点判读并降级描述，标 insufficient_replicates |
| 对照缺失 | 基线改用全数据 median/MAD（假设数据主体正常），显著标 missing_control，结论降级 |
| 读数超量程/饱和 | 判为 instrument 分支候选，验证=复测稀释/降量程；不在趋势中内插 |
| 结论互相冲突（多指标反向） | 分别陈述，不强行调和，列指标间关系待确认 |
| 文件格式异常/编码错误 | 修复读取后重跑；不可修复部分记 gap，不猜内容 |
| 图谱类数据无法程序解析 | 人工读数输入需双人独立读+差值记录，标 manual_reading |

## 7. 自查清单

- [ ] case_id 原样；output_contract 100% 映射
- [ ] 数据实际读取，列角色/单位标注；歧义保留在 ambiguities
- [ ] 基线/阈值/控制限来自脚本；阈值显式披露来源
- [ ] 趋势结论与统计量一致；异常定位到对象维度+偏离量
- [ ] 归因树四分支走查；每候选带 support/against/status
- [ ] 每个可检验假设带验证实验（动作+真假预期+成本）；untestable 如实标
- [ ] 复核步骤第二个人可执行；后续实验与假设互相引用
- [ ] reconciliation 逐条对账；unexplained 列出未解释部分
- [ ] 不虚构测量值/原因/重复数

## 8. 效率约束（64请求/900秒）

- Step0-1 两次响应；判读计算全部本地脚本（robust_stats.py 一次跑完 baseline+anomalies+trend）；模型响应主要用于归因树推理、复核设计、写结论（≤12次）。
- 大文件：脚本先出汇总统计，模型只读汇总+异常行；>10 万行分段采样并声明。
- 第1次响应后先写 result.json 骨架。

## 9. 最小示例（示意，非正式案例结果）

输入：酶标仪读数 CSV（3批次×2通道×48孔）+ 设备日志。
输出（节选）：基线=对照孔 median 0.35/MAD 0.02（10_baseline.json）；趋势：批1批2通道A 斜率+0.03/hr R²=0.91；异常：well-B7 修改Z=5.2 超控制限41%（data.csv:row=23）；归因树：sample-分支"孔位加样误差"（支持：相邻孔正常、异常单孔孤立）status=supported，验证=重测该孔3次预期回归对照区间；instrument-分支"移液器通道2故障"（against：通道2其余47孔正常）excluded；复核=回查日志 pump_event 行+重测；后续=下轮每板加2列技术重复。reconciliation 4条全 match。示意输出标 status=success。
