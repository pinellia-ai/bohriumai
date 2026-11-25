---
name: citation-trace
description: |
  引文追踪与关联文献发现：在组织方提供的离线语料快照上完成「种子定位」任务，输出可追溯的候选集、
  排序/筛选依据和遗漏说明。主线：种子定位 → 后向参考文献（方法/数据出处）→ 前向施引（后续改进与批评）→ 关联发现 → 路径解释 → 身份去重合并。
  真实执行流水线：查询规划→执行→覆盖评估→收敛，每轮记录{查询式,匹配字段,命中数,命中ID}，
  每条结果带 source(语料文件+字段)+relevance_basis(原文摘录)。绝不联网、不编造文献、不声称全球覆盖；
  材料缺失/无法判断/运行失败分别如实说明。
---

# 引文追踪与关联文献发现 — 离线语料检索执行版 Skill（v1）

## 1. 用途与适用范围

- 适用：围绕科研问题，在组织方提供的固定离线语料（9 篇真实署名文献快照 / 多源导出 / 材料文件）上执行「引文追踪与关联文献发现」，
  交付：候选集 + 逐条来源与相关性依据 + 筛选/排序/追踪依据 + 遗漏与状态说明，全部可独立复核。
- 方法主线：种子定位 → 后向参考文献（方法/数据出处）→ 前向施引（后续改进与批评）→ 关联发现 → 路径解释 → 身份去重合并。
- 不适用（超出边界，不做也不报）：不负责普通关键词检索的泛化召回、全文阅读、引文内容理解或未经授权的数据抓取；引用边只来自语料内 references 字段，不做语义虚构推荐
- 产物形态：result.json（主交付）+ workdir 过程产物（见 §1.1），每条结论可指回语料位置。

### 1.1 运行时产物清单（全部由 scripts 真实生成，非手写）

| 产物 | 生成者 | 内容 |
|---|---|---|
| records.jsonl / load_log.json | run_search.py | 语料全部记录（record_id+source+归一字段）/ 装载降级日志 |
| search_log.jsonl | run_search.py | 每轮 {round_id, subquestion, query, expanded_query, fields, hit_count, hit_ids, ts} |
| candidates.jsonl | run_search.py | 去重合并后候选：fields/source/best_score/hit_rounds/relevance_basis/dedupe |
| query_plan.json | Agent 按本题拆解规则编写 | 研究问题拆解与逐轮查询式（本题核心输入） |
| citation_graph.json | trace_citations.py | 种子/节点/引用边（direction+raw_ref+source_file+in_corpus）/路径/合并身份 |
| result.json | build_result.py | 主交付：contract 字段映射 + sources/status/uncertainty/change_log |

### 1.2 相对基础 Agent 的增益点（定性，可由产物对账）

- 前向+后向双层扩展替代单层参考文献抓取
- 每条引用边带 raw_ref 语境线索与 source_file，可逐边回查
- 身份合并保留预印本/正式版合并证据，综述清单干净可收

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

### Step 4 引文图追踪（→ /app/work/citation_graph.json）

- `python3 scripts/trace_citations.py --input /input --workdir /app/work --seeds "种子标题;种子DOI"`
- 种子定位：DOI 精确 → 标题近似（Jaccard≥0.85）；种子不存在于语料时如实报告，不猜种子内容。
- 扩展规则（多层级，非只取一层）：后向=读 references 字段逐条解析；前向=扫全语料找引用种子的施引记录；深度默认 2，超出预算减层并记录。分支剪枝：与种子去重键相同的分支合并；同名不同文（标题近似但 DOI/年份不同且语料可区分）不合并、单独成节点。
- 每条边必带：direction（forward/backward）+ raw_ref（引用语境线索：原始引文串前 200 字）+ source_file（哪份材料的哪个字段）+ in_corpus；in_corpus=false 的原始引文**保留 raw、不给编造 record_id**。
- 关联发现：共被引/耦合等关联信号仅以语料内可验证的引用边+去重合并证据为准；每个关联节点写一句"依据哪条边/哪个合并组"。
- 路径解释：paths 数组逐跳标注方向与 evidence_raw，区分直接引用与间接可达。
- 验收断言：citation_graph.json 有 node_count>0（种子命中时）；每条边四件齐全；merged_identities 每组合并证据可回查。

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

1. 种子定位方法逐条记录（doi_exact / title_fuzzy / not_found）。
2. 引用边 100% 带 direction+raw_ref+source_file+in_corpus，无编造 target。
3. 新预印本无前向引用记录时如实标注"语料内无施引记录"，不虚构引用。
4. 去重合并：预印本/会议版/期刊版合并保留 merge_basis（DOI 差异、年份差异、标题近似度）。
5. result.json 通过 contract 校验，case_id 原样。

## 6. 异常处理表


| 情况 | 处置 |
|---|---|
| /input/case.json 缺失或 output_contract 缺失 | result.json 写 status=failed + failure_reason，不虚构 |
| 材料文件全部缺失/为空 | status=failed；部分缺失则正常部分照跑，缺失面标 unchecked |
| 语料为空（0 条记录） | 如实报告空结果与已尝试查询式；不补造文献 |
| 脚本执行异常 | load_log/run_log 记录错误与降级路径；先落盘 partial result 再修 |
| output_contract 与本文冲突 | 以 case.json 为准，run_log 记录差异 |
| 种子未命中语料 | 报告 not_found + 已尝试的匹配方式，不猜种子元数据 |
| references 字段缺失 | 该方向追踪标 unavailable + 缺失字段位置；不凭空构造引用 |
| 引文串无法解析出标题/DOI | 边保留 raw_ref 原文并标 in_corpus=false |

## 7. 自查清单（提交前逐项过）

- [ ] case_id 原样；output_contract 字段全覆盖（build_result.py exit 0）
- [ ] 每条结果有 source(file+field) + relevance_basis 原文摘录
- [ ] search_log 每轮 {查询式, 匹配字段, 命中数, 命中ID} 齐全
- [ ] 空结果/冲突/缺失元数据如实说明，无虚构文献
- [ ] 先落盘 partial，再充实完整版
- [ ] run_log.md 完整
- [ ] 种子定位方法逐条记录；in_corpus=false 的边保留 raw 不编造 record_id

## 8. 效率约束

预算 64 请求 / 900 秒 / 单响应 16384 token。策略：Step 1 语料装载与全部数值对账用 scripts 完成（不耗模型请求）；检索规划与结论性判断分批响应；先落盘 partial 再充实；不做全文复述、不生成无关产物。资源限额 ≤50 文件 / 单文件 ≤500KB / 总量 ≤2MB。

## 9. 最小示例（示意输出，非正式案例结果）

citation_graph.json 示意：
```json
{"edges_sample": [{"from": "R0006", "to": "R0001", "direction": "backward",
  "raw_ref": "Pyroptosis in septic shock: gasdermin D pores drive inflammation; 10.1016/...",
  "in_corpus": true, "source_file": "seed_paper.json"}],
 "paths": [{"seed": "R0006", "target": "R0001", "direct": true,
  "hops": [{"from": "R0006", "to": "R0001", "direction": "backward", "evidence_raw": "Pyroptosis..."}]}]}
```
（示意输出，非正式案例结果）
