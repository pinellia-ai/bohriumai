---
name: multidb-union-search
description: |
  多数据库联合检索：在组织方提供的离线语料快照上完成「多源查询编排」任务，输出可追溯的候选集、
  排序/筛选依据和遗漏说明。主线：多源查询编排 → 字段标准化（跨库字段映射）→ 跨库去重 → 字段级合并与冲突消解 → 来源回溯 → 覆盖缺口显式化。
  真实执行流水线：查询规划→执行→覆盖评估→收敛，每轮记录{查询式,匹配字段,命中数,命中ID}，
  每条结果带 source(语料文件+字段)+relevance_basis(原文摘录)。绝不联网、不编造文献、不声称全球覆盖；
  材料缺失/无法判断/运行失败分别如实说明。
---

# 多数据库联合检索 — 离线语料检索执行版 Skill（v1）

## 1. 用途与适用范围

- 适用：围绕科研问题，在组织方提供的固定离线语料（9 篇真实署名文献快照 / 多源导出 / 材料文件）上执行「多数据库联合检索」，
  交付：候选集 + 逐条来源与相关性依据 + 筛选/排序/追踪依据 + 遗漏与状态说明，全部可独立复核。
- 方法主线：多源查询编排 → 字段标准化（跨库字段映射）→ 跨库去重 → 字段级合并与冲突消解 → 来源回溯 → 覆盖缺口显式化。
- 不适用（超出边界，不做也不报）：不绕过服务限制、不做单库全文阅读、不把未经授权的数据汇总到未批准服务；语料即组织方提供的多源导出文件
- 产物形态：result.json（主交付）+ workdir 过程产物（见 §1.1），每条结论可指回语料位置。

### 1.1 运行时产物清单（全部由 scripts 真实生成，非手写）

| 产物 | 生成者 | 内容 |
|---|---|---|
| records.jsonl / load_log.json | run_search.py | 语料全部记录（record_id+source+归一字段）/ 装载降级日志 |
| search_log.jsonl | run_search.py | 每轮 {round_id, subquestion, query, expanded_query, fields, hit_count, hit_ids, ts} |
| candidates.jsonl | run_search.py | 去重合并后候选：fields/source/best_score/hit_rounds/relevance_basis/dedupe |
| query_plan.json | Agent 按本题拆解规则编写 | 研究问题拆解与逐轮查询式（本题核心输入） |
| merge_matrix.json | merge_matrix.py | per_source 字段矩阵/跨库重复组+判定依据/合并冲突/覆盖缺口 gaps |
| result.json | build_result.py | 主交付：contract 字段映射 + sources/status/uncertainty/change_log |

### 1.2 相对基础 Agent 的增益点（定性，可由产物对账）

- 跨库字段别名映射统一表示，缺失与未知区分
- 合并规则确定性（来源优先级+值完整度），冲突值保留原值供仲裁
- 覆盖缺口显式列出（gaps），不静默返回不完整结果

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

### Step 2 源盘点与查询编排（→ /app/work/merge_matrix.json 前置部分 + query_plan.json）

- 先盘点语料里的每个来源文件（load_log + records.source.file）：各是什么库导出、各有哪些字段（字段覆盖矩阵）、检索语法差异。**不做"同一条查询机械复制到所有库"**：按各库字段能力定制查询（如某库只有标题字段→短查询；某库有摘要→长查询），分页/限流处理写进 query_plan 备注并在预算内节流。
- 验收断言：query_plan 每轮标注 target_sources；无来源被静默跳过（未查询的来源列 status_notes）。

### Step 5 字段标准化与合并审计（→ /app/work/merge_matrix.json）

- `python3 scripts/merge_matrix.py --records /app/work/records.jsonl --candidates /app/work/candidates.jsonl --workdir /app/work`
- 字段标准化：searchlib.FIELD_ALIASES 做跨库字段映射（authors/authorString/dc:creator→authors 等）；缺失与未知区分——字段缺失记 missing，字段存在但空值记 empty，不混用。
- 跨库去重：DOI 精确 → 标题近似(Jaccard≥0.85)+年份一致；每组重复判定保留 merge_basis（依据哪个标识符/近似度），同名不同文不合并。
- 合并规则（稳定可重复）：字段取值=来源优先级（query_plan.source_priority，缺省按文件名排序）+值完整度；**冲突值不丢弃**，conflicts 逐字段保留 {value, source} 供人工仲裁。
- 覆盖缺口显式化：per_source.missing_fields 与 gaps 数组列出每个库缺失的字段；某库不可用/返回异常→gaps 里写明"该库本次不可用，缺口=..."，不静默返回不完整结果。
- 验收断言：merge_matrix.json 含 per_source（每库记录数+字段矩阵）、cross_source_dup_groups（每组带判定依据）、gaps。

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

1. 每条候选的每个关键字段可追溯到 field_sources（来自哪个库哪个文件）。
2. 跨库重复组 100% 带 merge_basis；合并结果重跑不变（确定性规则）。
3. per_source 字段矩阵齐全；gaps 非空时 result.status_notes 明确说明缺口。
4. 不虚报"全球覆盖"：结论限定在语料快照的库与字段。
5. result.json 通过 contract 校验，case_id 原样。

## 6. 异常处理表


| 情况 | 处置 |
|---|---|
| /input/case.json 缺失或 output_contract 缺失 | result.json 写 status=failed + failure_reason，不虚构 |
| 材料文件全部缺失/为空 | status=failed；部分缺失则正常部分照跑，缺失面标 unchecked |
| 语料为空（0 条记录） | 如实报告空结果与已尝试查询式；不补造文献 |
| 脚本执行异常 | load_log/run_log 记录错误与降级路径；先落盘 partial result 再修 |
| output_contract 与本文冲突 | 以 case.json 为准，run_log 记录差异 |
| 某库文件不可用/损坏 | load_log 记 load_error，gaps 声明缺口，其余库照常，status=partial |
| 同一论文多标识符（DOI/PMID/arXiv 并存） | 全部保留在 fields，去重键取 DOI 优先 |
| 作者名/期刊名写法不一致 | 不强制归一人名；标题近似为去重主依据，冲突保留 |

## 7. 自查清单（提交前逐项过）

- [ ] case_id 原样；output_contract 字段全覆盖（build_result.py exit 0）
- [ ] 每条结果有 source(file+field) + relevance_basis 原文摘录
- [ ] search_log 每轮 {查询式, 匹配字段, 命中数, 命中ID} 齐全
- [ ] 空结果/冲突/缺失元数据如实说明，无虚构文献
- [ ] 先落盘 partial，再充实完整版
- [ ] run_log.md 完整
- [ ] 每库字段矩阵齐全；query_plan 按各库字段能力定制而非机械复制

## 8. 效率约束

预算 64 请求 / 900 秒 / 单响应 16384 token。策略：Step 1 语料装载与全部数值对账用 scripts 完成（不耗模型请求）；检索规划与结论性判断分批响应；先落盘 partial 再充实；不做全文复述、不生成无关产物。资源限额 ≤50 文件 / 单文件 ≤500KB / 总量 ≤2MB。

## 9. 最小示例（示意输出，非正式案例结果）

merge_matrix.json 示意：
```json
{"per_source": {"crossref.json": {"count": 3, "missing": ["language"]},
                "europepmc.jsonl": {"count": 3, "missing": ["doi"]}},
 "cross_source_dup_groups": [{"key": "doi:10.1038/s41590-023-01400-x",
   "record_ids": ["R0001", "R0004", "R0007"],
   "merge_rule": "字段取值=来源优先级+值完整度；冲突保留原值"}]}
```
（示意输出，非正式案例结果）
