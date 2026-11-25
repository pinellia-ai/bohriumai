---
name: systematic-screening-audit
description: |
  系统性文献检索与纳排筛选：在组织方提供的离线语料快照上完成「检索协议」任务，输出可追溯的候选集、
  排序/筛选依据和遗漏说明。主线：检索协议 → 去重（合并依据）→ 逐条纳排（理由码+依据片段）→ 双人独立判断 → 分歧仲裁 → 流程审计计数闭合 → 人工终审。
  真实执行流水线：查询规划→执行→覆盖评估→收敛，每轮记录{查询式,匹配字段,命中数,命中ID}，
  每条结果带 source(语料文件+字段)+relevance_basis(原文摘录)。绝不联网、不编造文献、不声称全球覆盖；
  材料缺失/无法判断/运行失败分别如实说明。
---

# 系统性文献检索与纳排筛选 — 离线语料检索执行版 Skill（v1）

## 1. 用途与适用范围

- 适用：围绕科研问题，在组织方提供的固定离线语料（9 篇真实署名文献快照 / 多源导出 / 材料文件）上执行「系统性文献检索与纳排筛选」，
  交付：候选集 + 逐条来源与相关性依据 + 筛选/排序/追踪依据 + 遗漏与状态说明，全部可独立复核。
- 方法主线：检索协议 → 去重（合并依据）→ 逐条纳排（理由码+依据片段）→ 双人独立判断 → 分歧仲裁 → 流程审计计数闭合 → 人工终审。
- 不适用（超出边界，不做也不报）：不替代研究者作最终科学判断；不负责全文精读后的质量评价/数据提取/统计分析；固定研究问题+全部记录全筛，不声称全球召回
- 产物形态：result.json（主交付）+ workdir 过程产物（见 §1.1），每条结论可指回语料位置。

### 1.1 运行时产物清单（全部由 scripts 真实生成，非手写）

| 产物 | 生成者 | 内容 |
|---|---|---|
| records.jsonl / load_log.json | run_search.py | 语料全部记录（record_id+source+归一字段）/ 装载降级日志 |
| search_log.jsonl | run_search.py | 每轮 {round_id, subquestion, query, expanded_query, fields, hit_count, hit_ids, ts} |
| candidates.jsonl | run_search.py | 去重合并后候选：fields/source/best_score/hit_rounds/relevance_basis/dedupe |
| query_plan.json | Agent 按本题拆解规则编写 | 研究问题拆解与逐轮查询式（本题核心输入） |
| criteria.json / criteria_B.json | Agent 显式化 | 两套独立纳排判据（双人双标载体） |
| screening_A/B.jsonl | screen.py | 两轮独立逐条判定（理由码+证据片段） |
| arbitration.json | arbitrate.py | 一致项/分歧项（类型+双方证据）/终审建议/审计计数闭合断言 |
| result.json | build_result.py | 主交付：contract 字段映射 + sources/status/uncertainty/change_log |

### 1.2 相对基础 Agent 的增益点（定性，可由产物对账）

- 双人独立判断+分歧仲裁（不平均不掩盖），分歧类型逐条记录
- 审计计数链脚本断言闭合：total=agree+disagree=included+pending+excluded
- 标准漂移防护：标准变更必须改 criteria 并全量重跑

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：提取 `case_id`（**原样保留，禁止改写**）与 `output_contract` 全部字段——result.json 必须逐字段落实；若 output_contract 有本节未列字段，以 case.json 为准补齐。
2. 读 `/input/task.md`：确认本次任务的动作动词与交付要求；与本文冲突时以 task.md 为准并在 run_log 记录。
3. `ls -la /input/` 盘点材料：记录每个文件名、类型、大小。**只依据实际文件内容执行，不依据文件名/领域标签猜测内容。**
4. 材料缺失或为空 → result.json 写 `status=failed` + `failure_reason`，不虚构。部分缺失 → 正常部分照跑，缺失面标 unchecked。
5. 语料即全部事实边界：检索、覆盖、'新'的判定都只相对这份快照；不声称实时联网或全球覆盖。

## 3. 工作流程（流水线，每步留痕）

### Step 1 语料装载与记录抽取（→ /app/work/records.jsonl + load_log.json）

- `python3 scripts/run_search.py --input /input --workdir /app/work --query-plan /app/work/query_plan.json` 之前，先确认 query_plan.json 已生成（Step 2）。
- 脚本自动扫描 /input 全部材料（json/jsonl/csv/tsv/txt/md），抽取文献记录：每条带 `record_id`（R0001…）、`source{file, field/jsonpath}`、归一字段（title/authors/year/doi/venue/abstract/type/language/keywords/references…）。
- 装载降级：jsonl 坏行、不支持的扩展名、解析错误都记入 load_log.json，不中断；txt/md 按段落切分。
- 验收断言：records.jsonl 条数 = load_log 各文件 records 之和；每条有 source。

### Step 2 检索协议（→ /app/work/query_plan.json 协议头）

- 协议先于检索：写清数据库（语料来源文件）、检索式、限定字段、时间范围、语种限制、检索日期，以及检索式与纳入标准的对应关系（每条检索式映射到 I 判据）。
- 验收断言：query_plan.json 带 protocol 块（fields/date/language/检索日期）；检索式与 criteria.json 的 include 判据一一对应可指认。

### Step 4 逐条纳排与双标（→ /app/work/screening_A.jsonl + screening_B.jsonl）

- `python3 scripts/screen.py --candidates /app/work/candidates.jsonl --criteria /app/work/criteria.json --workdir /app/work` 先跑 A 判据；再以**独立第二套判据**（criteria_B.json：可由第二视角判据或对边界条目更严的版本构成）复跑得 screening_B.jsonl。
- 每条记录：decision(included/excluded/pending) + 理由码 + 支撑片段（evidence_quote 原文摘录）。边界情形（仅摘要、语种不符、对象部分重叠）按 criteria 的约定走 pending，不硬判。
- 去重：预印本与正式版合并为一条，merge_basis 保留两种形态；标题相似但 DOI/年份不同的两条研究不误合并。

### Step 5 分歧仲裁与流程审计（→ /app/work/arbitration.json）

- `python3 scripts/arbitrate.py --a /app/work/screening_A.jsonl --b /app/work/screening_B.jsonl --workdir /app/work`
- 分歧不平均、不掩盖：存在任一 included → pending 待人工终审；双方均非 included → 取更保守；分歧类型（include-vs-exclude 等）逐条记录双方理由码与证据。
- 审计计数链（脚本内断言校验闭合）：total_unique = agree + disagree = final_included + final_pending + final_excluded；每步输入/输出条数写进 result.change_log，回答"从 N 条到 M 条"的全链路。
- 人工最终确认：模型输出全部标为待复核建议；纳入/排除终审由研究者确认后回写。标准途中不得口头修改——标准变更必须改 criteria.json 并重跑全量（防标准漂移）。
- 验收断言：arbitration.json 的 audit_counts 闭合（脚本断言保证）；每条分歧带双方证据。

### Step 6 最小 result.json 先落盘，再充实

- **进入检索前**：`python3 scripts/build_result.py --input /input --workdir /app/work --out /app/output/result.json --partial` 落盘 partial 骨架（保证任何中断都有可评分产物）。
- 全部步骤完成后：去掉 --partial 重跑，覆盖为完整版；退出码必须为 0（contract 校验通过）。
- 每步把 时间/命令/输入/输出/计数 追加到 /app/work/run_log.md。

### 执行顺序与请求预算分配（64 请求 / 900 秒内）

| 阶段 | 动作 | 请求消耗 |
|---|---|---|
| 0-1 | 读 case.json/task.md、盘点材料、跑装载脚本 | 1-2 |
| 2 | 规划：拆解/检索式/判据（写 query_plan/criteria 等文件） | 2-4 |
| 3-5 | 跑检索与本题定制脚本（纯脚本，零请求） | 0 |
| 6 | 结论性判断与逐条依据核对、充实 result.json | 2-6 |
| 余量 | 异常处置、复核、修正重跑 | 保留 ≥4 |

### 禁止事项（伪答案清单，出现即失分）

- 禁止：声称实时联网检索、全球数据库覆盖、'已检索 PubMed/Web of Science 全库'。
- 禁止：编造不存在的文献/DOI/作者；语料外的记录一律不进候选集。
- 禁止：用检索结果自身当覆盖率分母；把'没找到'写成'不相关'。
- 禁止：排除理由只写'不相关'；必须指认理由码与依据片段。
- 禁止：把题面/材料里的合成重复、冲突意见当成待办事实（input fixtures ≠ 预期答案）。
- 禁止：整篇复述摘要冒充评价/依据；依据必须是指向原文位置的短句摘录。

## 4. 输出契约

result.json 顶层字段（以 case.json `output_contract` 为最高优先；build_result.py 会自动把 contract 字段映射到产物，未映射字段如实标注，绝不虚构）：

```json
{
  "case_id": "<从 /input/case.json 原样读取>",
  "status": "success | partial | failed",
  "research_question": "<本次科研问题>",
  "query_log": "<search_log.jsonl：每轮 {round_id, subquestion, query, expanded_query, fields, hit_count, hit_ids}>",
  "candidates": "<candidates.jsonl：去重合并后的候选，每条含 fields/source/best_score/hit_rounds/relevance_basis/dedupe>",
  "ranking": "<排序结果（included/pending/excluded + counts + tie_notes）>",
  "screening": "<逐条筛选记录（如适用）>",
  "coverage": "<覆盖率与漏检归因（如适用）>",
  "evidence": "<证据记录：逐轮查询记录 + 每条候选的 relevance_basis 与去重依据，可按 query→hit_ids→record_id→source→quote 复核>",
  "sources": ["<实际使用的语料文件清单>"],
  "status_notes": {"empty_results": false, "note": "<空结果/冲突/权限/接口异常的处置说明>"},
  "uncertainty_notes": ["<判断不确定之处>"],
  "change_log": ["<partial→完整版变化记录>"],
  "search_summary": {"rounds": 0, "corpus_records": 0, "candidates_after_dedupe": 0}
}
```

- `status=success`：候选集/筛选/追踪完成且 contract 校验通过；`partial`：有 unchecked/未收敛/缺口；`failed`：材料缺失或不可解析。
- 检索结果、证据记录、状态说明三块与题面对应：他人可按 evidence 复核每条结果；不补造文献。

## 5. 数字门槛（达不到诚实标 partial）

1. 纳排标准逐条可判定（理由码+must_terms），排除理由禁用"不相关"一词，必须指认 E 码与证据片段。
2. 候选集全部条目都有 screening 记录；每条判断有 reason_code + evidence_quote。
3. 双标独立：A/B 两套判据文件分开；分歧逐条记录，无按单人意见直接定稿。
4. 审计计数闭合（脚本断言）；标准漂移防护=标准变更即全量重跑并记录。
5. result.json 通过 contract 校验，case_id 原样。

## 6. 异常处理表


| 情况 | 处置 |
|---|---|
| /input/case.json 缺失或 output_contract 缺失 | result.json 写 status=failed + failure_reason，不虚构 |
| 材料文件全部缺失/为空 | status=failed；部分缺失则正常部分照跑，缺失面标 unchecked |
| 语料为空（0 条记录） | 如实报告空结果与已尝试查询式；不补造文献 |
| 脚本执行异常 | load_log/run_log 记录错误与降级路径；先落盘 partial result 再修 |
| output_contract 与本文冲突 | 以 case.json 为准，run_log 记录差异 |
| 两位标注者判据冲突（材料即如此） | 判据冲突条目全部转 pending 升级人工；输入 fixtures 与预期输出分离如实标注 |
| 只有单份判据可用 | A=B 时双标退化为一致性自检，status_notes 声明 |
| 记录仅摘要无全文 | 按摘要判定+标注'仅摘要'，边界条目转 pending |

## 7. 自查清单（提交前逐项过）

- [ ] case_id 原样；output_contract 字段全覆盖（build_result.py exit 0）
- [ ] 每条结果有 source(file+field) + relevance_basis 原文摘录
- [ ] search_log 每轮 {查询式, 匹配字段, 命中数, 命中ID} 齐全
- [ ] 空结果/冲突/缺失元数据如实说明，无虚构文献
- [ ] 先落盘 partial，再充实完整版
- [ ] run_log.md 完整
- [ ] arbitration.json audit_counts 闭合（脚本断言）；分歧逐条带双方证据

## 8. 效率约束

预算 64 请求 / 900 秒 / 单响应 16384 token。策略：Step 1 语料装载与全部数值对账用 scripts 完成（不耗模型请求）；检索规划与结论性判断分批响应；先落盘 partial 再充实；不做全文复述、不生成无关产物。资源限额 ≤50 文件 / 单文件 ≤500KB / 总量 ≤2MB。

## 9. 最小示例（示意输出，非正式案例结果）

arbitration.json 示意：
```json
{"audit_counts": {"total_unique": 9, "agree": 8, "disagree": 1,
  "final_included": 1, "final_pending": 4, "final_excluded": 4},
 "disagree": [{"record_id": "R0003", "disagreement_type": "included-vs-excluded",
   "a_decision": "included", "b_decision": "excluded",
   "suggested": "pending"}]}
```
（示意输出，非正式案例结果）
