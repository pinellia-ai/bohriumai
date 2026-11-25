---
name: research-code-execution
description: |
  科研代码生成与执行。五环节流水线：字段对齐生成分析代码→环境快照（版本+sha256）→run_guard 受控执行（命令行/日志/退出状态留痕）→结果校验（行数对照+数值复算+静默错误检测：缺失当0/重复未去重/无假设检验直接出p）→错误处理（识别/重试/降级/保留失败现场）。不给出"跑通了但算错了"的交付。
---

# 科研代码生成与执行 Skill（research-code-execution）

## 1. 用途与适用范围

- 用途：从数据字典+任务描述生成清洗/统计/可视化代码→在真实数据上跑通→校验数值→留痕交付。
- 铁律：**跑通≠正确**。交付前必须通过静默错误检测；每次执行留命令行+日志+退出状态；失败保留现场不覆盖。

## 2. 输入识别（Step 0，必做）

1. 读 /input/case.json（case_id 原样、output_contract 抄 order.json）；最小 result.json 先落盘。
2. 读数据字典与任务描述；数据快照+sha256。字典缺失→字段语义标 unverified，不硬对齐。
3. 环境快照：`run_guard.py env` 记录 python 版本、包版本（importable 探测）、平台、时间。

## 3. 工作流程

### Step 1 代码生成（约束式）

生成 /app/work/analysis.py 时强制约定：
- 字段引用必须来自数据字典/表头（`FIELDS = {...}` 常量区，逐字段注释语义与单位）；引用不存在列→生成期报错，不运行期崩。
- 缺失处理显式（dropna 或标记，禁止隐式 NaN 传播）；分组统计前去重断言；t 检验前正态性断言（stats_kit 同款选择树）。
- 所有输出写 result JSON，不带随机过程（或 seed 显式）。
- 路径用参数（argv），**禁止硬编码本机路径**。

### Step 2 受控执行

```bash
python3 $SKILL_DIR/scripts/run_guard.py env /app/work/env.json
python3 $SKILL_DIR/scripts/run_guard.py run "python3 /app/work/analysis.py /app/work/data.raw.csv /app/output" /app/work/runs
```

run_guard 记录每次执行：命令行、stdout/stderr、退出码、耗时、env.json 引用 → runs/run_001.json（递增编号，失败现场保留）。超时默认 120s。

### Step 3 结果校验（防静默错误，核心创新点）

```bash
python3 $SKILL_DIR/scripts/verify_results.py /app/work/runs/run_001.json /app/work/data.raw.csv /app/output/result.json
```

断言：
1. **行数对照**：result.json 的 n_rows 与原始 CSV 行数、清洗日志一致。
2. **数值复算**：抽验 result.json 中 mean/median 与独立复算（statistics 库直算）差 <1e-9。
3. **静默错误模式扫描**（扫 analysis.py 源码 AST）：
   - mean/sum 前未 dropna 且列有缺失 → 标 "缺失当0/NaN 传播风险"
   - groupby 无 drop_duplicates 且有重复主键 → "重复未去重"
   - ttest 前无 normality/shapiro 调用 → "未验假设直接出 p"
   - 硬编码路径 / 绝对路径常量 → 报错
4. 任一 FAIL → 回到 Step 1 修代码（最多 2 轮），第 3 轮仍败 → partial + 失败现场。

### Step 4 交付

```json
{
  "case_id": "<原样>", "status": "complete|partial|failed",
  "code": {"analysis_py": "/app/work/analysis.py", "sha256": "...", "field_constant": true},
  "environment": "/app/work/env.json",
  "runs": [{"id": "run_001", "cmd": "...", "exit_code": 0, "seconds": 1.2, "log": "/app/work/runs/run_001.json"}],
  "results": "/app/output/result.json",
  "verification": {"rows_check": "pass", "recompute_check": "pass 3/3", "silent_error_scan": "pass", "tool": "verify_results.py"},
  "uncertainty": [], "change_log": []
}
```

## 4. 输出契约

题面三大交付：分析结果（result.json+图表）/质量与复现证据（代码 sha256+环境+runs+校验报告）/异常说明（失败现场）。output_contract 逐字段落实。

## 5. 数字门槛

- 代码真实跑通（run_001 exit_code=0）；verify_results 三类断言全过；每次执行的命令行+日志+退出状态齐全。
- 数值可独立复算（换脚本直算一致）；同环境重跑结果一致。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 缺列/类型不符 | 生成期 FIELDS 校验拦住；运行期 KeyError → 修代码不瞎猜 |
| 依赖缺失 | env.json 记录缺失包；降级到标准库实现并在 result 注明 |
| 查询为空/数值溢出 | run_guard 捕获非零退出，保留现场，分析原因后再改 |
| 超时 | run_guard 120s 截断（可调），结果标 partial |
| 代码 3 轮跑不通 | partial + 每轮失败日志（不丢失败现场） |

## 7. 自查清单

- [ ] 字段常量区齐、无硬编码路径
- [ ] env.json + run 留痕 + 退出码
- [ ] verify_results 三类断言全过（行数/复算/静默扫描）
- [ ] 失败轮次日志保留
- [ ] result.json 契约全覆盖

## 8. 效率约束

先最小 result；代码一次成型+最多修 2 轮；≤50 文件。

## 9. 最小示例

CSV→analysis.py（FIELDS 常量+显式 dropna+均值输出）→run_guard 受控执行 exit 0→verify_results 行数/复算/AST 静默扫描全过（见 README 自测记录）。


## 附录 A 全流程命令序列（评测时按序执行）

```bash
# Step 0 识别（手动：读 /input/case.json 抄 output_contract 到 order.json）
mkdir -p /app/work /app/output
# Step 1-N 主链路（$SKILL_DIR 为本 skill 安装目录）
ls $SKILL_DIR/scripts/        # 确认脚本齐备
# 各 Step 的具体命令见 §3；校验脚本 FAIL 时按 §6 异常表处置后重跑（≤2 轮）
python3 $SKILL_DIR/scripts/export_check.py --help   # 查看参数
```

## 附录 B 常见失败 ↔ 处置对照

| 失败现象 | 根因 | 处置 |
|---|---|---|
| 校验脚本 exit 1 有 FAIL 项 | 见其输出 detail 字段 | 按 detail 修 spec/数据后重跑 |
| PNG 打开是白图/方框 | 无 CJK 字体 | FIG_CJK_FONT=/path/to/font.ttf 后重跑渲染 |
| result.json 字段缺失 | 跳过 Step 6 模板 | 按 §3 末模板逐字段补齐 |
| 预算接近上限 | 前面步骤耗时过多 | 立即交 partial（status 如实），已产文件照常评分 |
| 材料与预期类型不符 | 题面材料变化 | 按 Step 0 盘点结果走 §6 对应行 |

## 附录 C 与本赛道的边界对照（不做的事，避免越界扣分）

- workorder 类型: `code_execution_task`；spec 文件命名: `analysis_plan.json`。
- 越界内容一律移交相邻课题：统计方法选择、实验方案设计、论文写作、版式美化。
- 科学判断由评测 Judge 做：本 skill 只保证"可编辑源文件+导出合规+来源可核验"三件套的工程质量。
