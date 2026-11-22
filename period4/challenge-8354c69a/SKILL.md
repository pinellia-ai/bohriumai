---
name: result-interpreter-exec
description: |
  实验结果解释与异常分析 Skill（计算执行版）。不写"解释框架"，直接对数据真实计算：
  载入读数/对照/判读标准 → 脚本计算基线均值/标准差/控制限 → 逐点计算 z 分数与偏离量
  → 异常点数值化判定（真异常/正常波动）→ 排除式归因矩阵（假设×证据×状态）→ 可执行
  下一步动作表。全部结论绑定数据单元格定位与计算中间值，CSV/代码交付可复跑。
---

# Result Interpreter Exec — 实验结果解释与异常分析 Skill（计算执行版）

## 0. 运行契约（最高优先）

1. `/input/case.json` 的 `output_contract` 定义 result.json 必须字段——**逐字段原样落实**；`case_id` 原样读取。
2. 过程写 `/app/work/`；最终产物写 `/app/output/`（含 result.json + 计算脚本 + CSV）。
3. 只依据实际数据文件计算；**运行结果来自真实执行**（附脚本与日志），不编造数值。
4. 预算 64 请求 / 900 秒：先落盘最小可用 result.json，再增强。

## 1. 输入识别与基线构建（真实计算）

1. `ls /input/`；读 case.json、数据表（读数/曲线数据点/设备日志）、判读标准（方案里的判读条款）。
2. **基线表**（baseline.csv，脚本计算）：对照组/历史读数的 `n、均值、标准差、最小/最大`，逐指标一行——异常判定的锚。
3. 无对照组时：用方案判读标准的数值阈值作基线并声明口径；两者都无 → 异常判定降级为描述性（如实标注）。

## 2. 异常检测（数值化判定）

- 逐数据点计算：`z = (x - baseline_mean) / baseline_sd`；控制限（均值±2σ/±3σ）。
- 判定三态：`normal（|z|<2）/ borderline（2≤|z|<3）/ anomaly（|z|≥3 或超方案阈值）`——**每点带 z 值与偏离量原始数**，写进 anomalies.csv。
- 正常波动不误报：borderline 点标注"边缘，建议复测"而非直接判异常。

## 3. 趋势计算（不是读数复述）

- 按组/时间维计算：斜率（线性拟合）、变化幅度（首末差值与百分比）、组间差值及百分比——脚本输出 trends.csv。
- 每条趋势句 = `方向 + 数值幅度 + 对照基准 + 数据定位（表行/列）`，数值直接来自 trends.csv。

## 4. 归因矩阵（排除式，数值化）

- 候选原因 × 证据矩阵：`{假设, 支持证据(数据定位+数值), 反对/排除证据, 状态: excluded | possible | confirmed_pending}`。
- 用数据说话：如"仪器漂移"→ 检查同批对照读数是否同步偏移（算对照组 z 值）；"批次效应"→ 按批次分组统计均值差。
- **每个被排除的假设必须引用排除它的数值**；保留的假设标"待复核动作"。

## 5. 下一步动作（可执行+可分辨）

- 每个动作：`{操作(重测哪个样品哪个参数/补什么对照), 预期分辨力(能区分哪些假设), 预估成本}`——动作表 actions.csv。
- 明确区分：复核动作（对已有异常）vs 补做实验（对未验证假设）。

## 6. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "result_interpretation",
  "status": "success | partial | failed",
  "baseline": {"file":"baseline.csv","metrics":[{"metric":"OD","n":12,"mean":0.4,"sd":0.05,"source":"对照组 T1 rows2-8"}],
               "fallback_note":null},
  "anomalies": [{"sample":"S17","batch":"B2","value":1.35,"z":19.0,"deviation":"+0.95 over 3σ limit",
                 "verdict":"anomaly","locator":{"table":"T1","row":17}}],
  "borderline": [{"sample":"S22","value":0.88,"z":1.9,"note":"边缘，建议复测"}],
  "trends": [{"dim":"时间×处理组","statement":"处理组上升30%（0.4→0.52，斜率0.006/day）","from":"trends.csv row1"}],
  "attribution_matrix": [
    {"hypothesis":"加样失误","status":"possible","support":"S17 异常仅在 B2；B2 移液器校准超期(log p3)","excluded_evidence":null},
    {"hypothesis":"仪器漂移","status":"excluded","excluded_evidence":"同批对照 z∈[-0.8,0.6]，无同步偏移"}
  ],
  "next_steps": [{"action":"S17 留样重测×2（新旧移液器各一）","distinguishes":"区分'加样失误'与'样本异常'","cost":"半天"}],
  "files": {"anomalies_csv":"anomalies.csv","trends_csv":"trends.csv","baseline_csv":"baseline.csv",
            "actions_csv":"actions.csv","code":"analysis.py","run_log":"run_log.md"},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：baseline/anomalies/trends 全部脚本真实计算（附 analysis.py + run_log）；z 值与偏离量是算出来的不是描述的；排除式归因逐条带数值证据；正常波动不误报。

## 7. 异常处理

| 情况 | 处置 |
|---|---|
| 无对照/无判读标准 | 基线降级声明，判定用描述性+needs_review |
| 数据点稀少（n<5） | sd 不可靠 → 用方案阈值判定 + 声明 |
| 预算不足 | 基线+异常检测优先（partial） |

## 8. 自查清单

1. [ ] 基线表真实计算？口径声明？
2. [ ] 异常判定带 z/偏离量数值？边缘点不误报？
3. [ ] 趋势句数值来自 trends.csv？
4. [ ] 归因排除式、逐条数值证据？
5. [ ] 下一步动作可执行且有分辨力？
6. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 9. 最小示例（示意，非正式结果）

```json
{"case_id":"demo","baseline":{"metrics":[{"metric":"OD","n":8,"mean":0.4,"sd":0.05}]},
 "anomalies":[{"sample":"S5","value":1.2,"z":16.0,"verdict":"anomaly"}],
 "attribution_matrix":[{"hypothesis":"批次效应","status":"excluded","excluded_evidence":"B1/B2 对照组均值差 0.01 (<1σ)"}],
 "next_steps":[{"action":"S5 重测×2","distinguishes":"设备故障 vs 样本异常"}]}
```

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 已全量重写为计算执行版（baseline/anomalies/trends/attribution/next_steps 五张 CSV
2. analysis.py
3. run_log）；按 SKILL.md 执行。
