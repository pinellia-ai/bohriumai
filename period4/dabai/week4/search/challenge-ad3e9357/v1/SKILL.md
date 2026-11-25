---
name: patent-tech-search
description: |
  专利与技术文献检索：在组织方提供的离线语料快照上完成「检索范围界定」任务，输出可追溯的候选集、
  排序/筛选依据和遗漏说明。主线：检索范围界定 → 专利号规范化 → 同族归并（简单族/扩展族口径）→ IPC/CPC 分类号解析 → 法律状态核验口径（来源+查询日期+滞后声明）→ 授权边界与风险分级。
  真实执行流水线：查询规划→执行→覆盖评估→收敛，每轮记录{查询式,匹配字段,命中数,命中ID}，
  每条结果带 source(语料文件+字段)+relevance_basis(原文摘录)。绝不联网、不编造文献、不声称全球覆盖；
  材料缺失/无法判断/运行失败分别如实说明。
---

# 专利与技术文献检索 — 离线语料检索执行版 Skill（v1）

## 1. 用途与适用范围

- 适用：围绕科研问题，在组织方提供的固定离线语料（9 篇真实署名文献快照 / 多源导出 / 材料文件）上执行「专利与技术文献检索」，
  交付：候选集 + 逐条来源与相关性依据 + 筛选/排序/追踪依据 + 遗漏与状态说明，全部可独立复核。
- 方法主线：检索范围界定 → 专利号规范化 → 同族归并（简单族/扩展族口径）→ IPC/CPC 分类号解析 → 法律状态核验口径（来源+查询日期+滞后声明）→ 授权边界与风险分级。
- 不适用（超出边界，不做也不报）：不做专利撰写、侵权判定、自由实施分析或价值评估，不替代专利律师/法律意见；不绕过付费墙、不上传受限数据；结论只来自授权来源文件并标注库名
- 产物形态：result.json（主交付）+ workdir 过程产物（见 §1.1），每条结论可指回语料位置。

### 1.1 运行时产物清单（全部由 scripts 真实生成，非手写）

| 产物 | 生成者 | 内容 |
|---|---|---|
| records.jsonl / load_log.json | run_search.py | 语料全部记录（record_id+source+归一字段）/ 装载降级日志 |
| search_log.jsonl | run_search.py | 每轮 {round_id, subquestion, query, expanded_query, fields, hit_count, hit_ids, ts} |
| candidates.jsonl | run_search.py | 去重合并后候选：fields/source/best_score/hit_rounds/relevance_basis/dedupe |
| query_plan.json | Agent 按本题拆解规则编写 | 研究问题拆解与逐轮查询式（本题核心输入） |
| patents.json | patent_check.py | 号码规范化对照/族归并（口径+依据）/IPC-CPC 解析/法律状态口径/risk_flags |
| result.json | build_result.py | 主交付：contract 字段映射 + sources/status/uncertainty/change_log |

### 1.2 相对基础 Agent 的增益点（定性，可由产物对账）

- 专利号规范化到 国家+序号+种类代码，公开号/授权号不混用
- 族归并分简单族/扩展族并声明口径，缺优先权字段标 unknown_scope 不猜
- 法律状态只用语料内登记值+来源+查询日期+滞后声明，二手数据不用官方口吻

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

### Step 2 专利检索式与技术文献分轨（→ /app/work/query_plan.json）

- 技术主题检索式 = 关键词 + 分类号（IPC/CPC）+ 申请人 + 引证关系组合；每条检索式写明目标字段与口径，可解释（为何用这个分类号/这个词）。
- **专利文献与技术文献分轨**：patent_number/classification/legal_status 等字段的记录走专利轨（Step 4 解析），纯文献记录走普通文献轨（Step 3 检索），两轨在 result 中分开呈现，不混编。

### Step 4 专利字段解析与核验（→ /app/work/patents.json）

- `python3 scripts/patent_check.py --records /app/work/records.jsonl --workdir /app/work`
- 号码规范化：CN115203333A → 国家代码+序号+种类代码（A=公开/B=授权/U=实用新型…）；公开号与授权号不混用，优先权和申请日不混为一谈（date 字段来源逐条记录）。无法规范化的号码（仅内部ID/格式异常）进 risk_flags，不硬编。
- 同族归并口径：简单族=同国家同 serial（脚本自动+merge_basis）；扩展族（优先权链）需优先权字段——语料缺失时标 unknown_scope，不猜；同标题跨国家局 → title_family_candidates（疑似同族，需优先权佐证，不自动并入）。
- 分类号解析：IPC/CPC 拆到部/大类/小类/小组（如 A61K 31/00）；语料未提供的记录不推测。
- 法律状态核验口径：只报告语料内登记值+来源（source.file）+查询时间；声明可能的滞后；**转载页面/二手聚合数据不作为登记依据**——只有官方著录字段（语料内标注官方来源）才以"官方登记"口吻陈述，否则一律带来源限定语。
- 授权边界与风险分级：每条结论标证据强度（官方著录/语料内二手/字段缺失）；risk_flags 汇总（号码异常/状态缺失/同族口径不明/覆盖不全），并给人工复核建议（官方库复核哪些字段）。
- 验收断言：patents.json 含 normalized（逐条规范化+来源）/families（带口径说明）/classifications/legal_status_audit/risk_flags。

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

1. 每条专利号规范化结果带 raw→normalized 对照与来源；异常号不硬编，进 risk_flags。
2. 族关系口径明确：简单族自动归并带证据；扩展族缺优先权字段时显式 unknown_scope。
3. 法律状态逐条带来源+查询日期+滞后声明；无官方字段不用官方口吻。
4. 风险分级覆盖：字段缺失/状态过期/同族口径不明/库覆盖不全四类至少各自查过（无则记 na）。
5. result.json 通过 contract 校验，case_id 原样。

## 6. 异常处理表


| 情况 | 处置 |
|---|---|
| /input/case.json 缺失或 output_contract 缺失 | result.json 写 status=failed + failure_reason，不虚构 |
| 材料文件全部缺失/为空 | status=failed；部分缺失则正常部分照跑，缺失面标 unchecked |
| 语料为空（0 条记录） | 如实报告空结果与已尝试查询式；不补造文献 |
| 脚本执行异常 | load_log/run_log 记录错误与降级路径；先落盘 partial result 再修 |
| output_contract 与本文冲突 | 以 case.json 为准，run_log 记录差异 |
| 语料无专利记录（纯文献案例） | 专利轨空跑并如实声明，技术文献轨正常执行 |
| 只有二手聚合站数据 | 全部结论带'语料内二手数据'限定语，不称官方著录 |
| 状态字段为旧转载值 | 标注'状态可能滞后'，列人工复核建议 |

## 7. 自查清单（提交前逐项过）

- [ ] case_id 原样；output_contract 字段全覆盖（build_result.py exit 0）
- [ ] 每条结果有 source(file+field) + relevance_basis 原文摘录
- [ ] search_log 每轮 {查询式, 匹配字段, 命中数, 命中ID} 齐全
- [ ] 空结果/冲突/缺失元数据如实说明，无虚构文献
- [ ] 先落盘 partial，再充实完整版
- [ ] run_log.md 完整
- [ ] 异常号码进 risk_flags 未硬编；每条状态带来源与查询时间

## 8. 效率约束

预算 64 请求 / 900 秒 / 单响应 16384 token。策略：Step 1 语料装载与全部数值对账用 scripts 完成（不耗模型请求）；检索规划与结论性判断分批响应；先落盘 partial 再充实；不做全文复述、不生成无关产物。资源限额 ≤50 文件 / 单文件 ≤500KB / 总量 ≤2MB。

## 9. 最小示例（示意输出，非正式案例结果）

patents.json 示意：
```json
{"normalized": [{"record_id": "R0008", "raw_number": "CN115203333A",
  "normalized_number": {"country": "CN", "serial": "115203333", "kind": "A", "kind_meaning": "公开"},
  "classifications": [{"raw": "A61K 31/00", "subclass": "A61K", "group_subgroup": "31/00"}],
  "legal_status": "active", "source": {"file": "patents.json"}}],
 "title_family_candidates": [{"members": ["R0008", "R0009"],
  "note": "同标题跨国家局：疑似同族，需优先权字段佐证（unknown_scope 待人工）"}]}
```
（示意输出，非正式案例结果）
