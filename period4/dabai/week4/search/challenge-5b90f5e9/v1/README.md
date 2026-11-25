# challenge-5b90f5e9 系统性文献检索与纳排筛选 — v1 交付说明

## 交付标准清单（从题面提取）

### output_contract / 产出字段（result.json 必须逐字段落实，以 case.json 为最高优先）
- `case_id`：从 /input/case.json 原样读取，不得改写
- `status`：success | partial | failed，含诚实状态与界限说明
- 检索结果：候选文献、排序/筛选结果、元数据和来源定位；结果与检索范围、相关性依据和缺失项一致
- 证据记录：查询、筛选、排序或追踪依据；他人可按记录复核每条结果
- 状态说明：空结果、冲突、权限或接口异常；不补造文献，明确已完成和未完成部分
- `sources` / `uncertainty_notes` / `change_log`：来源、不确定性与变化记录

### 硬性要求（题面 §1 四条 + Harbor 运行契约）
1. 明确研究问题和检索范围（不声称全球覆盖/实时联网）
2. 设计或改进检索、筛选、排序或追踪流程（本题主线：检索协议 → 去重（合并依据）→ 逐条纳排（理由码+依据片段）→ 双人独立判断 → 分歧仲裁 → 流程审计计数闭合 → 人工终审）
3. 对每条结果保留来源和相关性依据（source=语料文件+字段；relevance_basis=原文摘录）
4. 对无结果、冲突、缺失元数据和权限问题明确说明
5. 输入 /input/case.json + task.md；过程 /app/work；产物 /app/output；先落盘最小 result.json
6. 预算 64 请求 / 900 秒 / 16384 token；资源 ≤50 文件 / 单文件 500KB / 总 2MB
7. 不提交预制答案；skill 为通用流程
8. 提交目录根路径放 GITHUB_URL.txt

### 题面突破方向映射（本题覆盖）
- 检索协议 → 去重（合并依据）→ 逐条纳排（理由码+依据片段）→ 双人独立判断 → 分歧仲裁 → 流程审计计数闭合 → 人工终审
- 固定案例为离线快照（组织方修订：9 篇真实署名文献/真实查询输入/全记录筛选；不声称实时联网与全球召回）

## scripts 清单（Python3 标准库，无第三方依赖）

- `scripts/searchlib.py`
- `scripts/run_search.py`
- `scripts/build_result.py`
- `scripts/screen.py`
- `scripts/arbitrate.py`

## 自测记录（2026-11-24，按 PLAYBOOK §4，合成语料 13 记录实跑）

| 项 | 结果 |
|---|---|
| YAML frontmatter 可解析 | PASS name=systematic-screening-audit |
| SKILL.md 行数 150-400 | PASS (173 行) |
| scripts ast.parse 全过 | PASS (5 个) |
| build_result --partial 实跑 | PASS (rc=0) result.json written; contract OK; status=partial |
| run_search 实跑 | PASS (rc=0) rounds=2 queries=3 corpus=13 candidates=9 |
| screen 实跑 | PASS (rc=0) total=9 included=2 pending=3 excluded=4 ties=0 |
| screen B 判据 实跑 | PASS (rc=0) total=9 included=0 pending=4 excluded=5 ties=0 |
| arbitrate 实跑 | PASS (rc=0) agree=6 disagree=3 final: inc=0 pend=4 exc=5 |
| arbitrate 实跑 | PASS (rc=0) agree=6 disagree=3 final: inc=0 pend=4 exc=5 |
| build_result 完整版 + contract 校验 | PASS (rc=0) result.json written; contract OK; status=success |
| 资源限额 ≤50 文件 / 2MB | PASS (7 文件, 61KB) |
| 无虚构（仅标准库+题面内路径/字段） | PASS（scripts 仅 import 标准库；示例标注为示意输出） |
| OVERALL | PASS |

整体结论：全部通过（合成语料上全部通过；正式案例结果以平台实际运行为准）

## 使用方法

1. Agent 按 SKILL.md §2 Step 0 读 /input/case.json 与 task.md，盘点 /input/
2. 生成 /app/work/query_plan.json（检索协议（字段/时间窗/语种/检索日期）写入 query_plan.json 协议头）
3. 先落盘 partial：`python3 scripts/build_result.py --input /input --workdir /app/work --out /app/output/result.json --partial`
4. `python3 scripts/screen.py ... --criteria criteria.json --workdir /app/work`（A 判据）后以 criteria_B.json 复跑至独立工作目录
5. `python3 scripts/arbitrate.py --a /app/work/screening_A.jsonl --b /app/work/screening_B.jsonl --workdir /app/work`
6. 完成后去掉 --partial 重跑 build_result.py，退出码 0（contract 全覆盖）方可交付

## 已知限制
- 只在组织方离线语料快照上检索；无实时联网、无全球召回声明
- 语料外文献一律不进候选集；引用边只来自语料内 references 字段
- 自测基于合成语料（13 条记录），验证的是流水线行为与口径，不代表正式案例数值
