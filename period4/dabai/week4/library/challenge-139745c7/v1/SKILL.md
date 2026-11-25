---
name: sci-file-smart-retrieval
description: |
  科研文件智能检索 Skill：在已入库的本地文件集上完成"跨文件语义检索→章节定位→过滤条件执行→证据回链"的完整交付。
  方法主线：先扫描盘点全部文件并建带页码/章节的段落级索引（同义词与缩写归一），查询时把过滤条件当作硬约束执行、
  条件不满足时如实报告而非放宽，每条命中输出 文件路径+版本标识+页码+段落序号+段落首句+原文片段 的可复核定位。
  全程离线、只依据文件真实内容，不编造页码或命中；材料缺失或不可读时明确记入 status/partial。
---

# 科研文件智能检索（Semantic Locate & Evidence Link）

## 1. 用途与适用范围

- **做**：文件已在库内时，回答"这个体系在哪个项目里做过 / 某个配方写在哪一版 / 哪张图对应哪组数据"这类**定位型问题**：找到文件、落到章节/页/段落、按过滤条件筛、给出可逐字回链的证据。
- **不做**：开放网络文献检索、全文精读与综述写作、存储系统权限建设。
- **验收口径**：问题指向的那一段是否被找到；定位到的位置是否就是原文那一段；他人能否按记录复核到同一段。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：记录 `case_id`（原样保留）、材料目录、任务说明、过滤条件与输出要求（output_contract）。
2. 读同目录 `task.md`，把用户问题拆成：**查询主题**（找什么）+ **过滤条件**（年份/项目编号/文件类型/批次/版本/权限）+ **定位粒度**（文件级/章节级/段落级）。
3. 盘点材料：`python3 scripts/inventory.py <材料根目录> --out /app/work/inventory.json`。
4. 材料目录为空或 case.json 缺失 → `result.json` 写 `status=failed, reason=...`，不虚构。

## 3. 工作流程（六步流水线，每步有落盘产物与验收断言）

### Step 1 盘点（产物 `inventory.json`）
- 遍历材料根目录，记录：相对路径、扩展名、大小、mtime、sha256（≤64MB 文件）、是否可读。
- **版本标识规则**：同目录下 `*_v2/*(1)/*final*/*修订*` 等命名副本 + 内容哈希分组；同哈希=同一文件的副本（记 alias），不同哈希但命名递进=版本链（记 version_of）。
- 验收：`inventory.json` 文件计数 == 实际文件计数（`find | wc -l` 对账）。

### Step 2 建索引（产物 `index.json`；脚本 `build_index.py`）
- 文本抽取：`.txt/.md/.csv/.tsv/.json` 直接读；`.pdf` 用 pypdf 逐页抽文本，**记录物理页号**，尝试从页眉/页脚识别印刷页码偏移；`.docx` 用 python-docx；`.xlsx` 用 openpyxl 逐 sheet；扫描件无文本层 → 记入 `unreadable`（不要 OCR 造假）。
- 切块：按空行/标题行切段，块大小 ≤1200 字符；每块保留 `{doc_id, page, para_idx, section_title, first_sentence, text}`。
- **语义归一**：内置同义词/缩写映射（如 "PBS"↔"磷酸盐缓冲液"、中英混写、上下位词 "细胞凋亡"⊂"细胞死亡"），查询与索引两侧都做扩展；映射表在 `scripts/synonyms.json`，可按案例领域增补。
- 验收：`index.json` 的 `docs` 数 == inventory 中 readable 文件数；抽查 3 个块能在源文件中逐字找到 `text` 前缀。

### Step 3 检索与过滤（脚本 `search.py`）
- 查询先做同义扩展，再对每块打分：术语命中数（全词命中×2，扩展命中×1）+ 短语完整命中加成 + 关键术语密度。
- **过滤条件是硬约束**：年份、项目编号、文件类型、批次、版本、路径范围不满足的块直接出局，**绝不放宽**；若过滤后为 0 命中，输出 `empty_result=true` 并说明"是过滤导致还是内容确实没有"，不擅自去掉条件重查。
- 重复/副本处理：同哈希副本只保留主路径一份证据，其余记 `alias_of`；旧版本命中要在结果中标注"此为 v1，另有 v2"，避免把旧版当独立证据。
- 验收：每条命中附 `filter_passed` 明细；空结果时 `filters_report` 给出逐条过滤后剩余计数。

### Step 4 章节定位与证据回链（脚本内完成，产物写入 result.json）
- 每条命中输出完整定位：`{path, sha256_8, version_label, page(物理页), printed_page(如可识别), section_title, para_idx, first_sentence, snippet(命中句前后各~120字), char_span}`。
- PDF 双栏/跨页表格：按抽取文本顺序给出段号，注明"双栏版式，段序为抽取顺序"；印刷页与物理页不一致时两者都给。
- 验收：任取一条证据，用 `first_sentence` 在源文件中 `Ctrl+F` 能唯一定位到该页该段。

### Step 5 组织结果（产物 `/app/output/result.json`）
按 §4 契约逐字段填写；先落盘最小可用版本（status+top1 命中），再逐步充实。
同一段问题若多个文件都命中，按过滤条件+得分排序全部列出（不只给一份就下结论）；跨文件互相矛盾的命中要并列呈现并注明差异。

### Step 6 运行记录（产物 `run_log.json`）
记录：每步耗时、扫描文件数、抽取失败/跳过清单（含原因：无权限/加密/无文本层）、过滤前后命中数、查询扩展词表。失败与跳过不写成完成。

## 4. 输出契约（result.json 逐字段）

```json
{
  "case_id": "原样保留",
  "status": "ok | partial | failed",
  "question": {"topic": "查询主题", "granularity": "section|paragraph|file", "filters": {"year": 2023, "project_id": "P-2023-015", "file_type": "pdf"}},
  "inventory": {"total_files": 0, "readable": 0, "unreadable": 0, "duplicate_groups": 0, "version_chains": 0},
  "hits": [
    {"rank": 1, "score": 12.5, "path": "相对路径", "sha256_8": "abcd1234", "version_label": "v2(最新)|v1|alias_of:xxx",
     "page": 3, "printed_page": 2, "section_title": "2.3 缓冲液配制", "para_idx": 4,
     "first_sentence": "…", "snippet": "…命中句…", "filter_passed": {"year": true, "project_id": true},
     "locator": "path#page=3,para=4"}
  ],
  "empty_result": {"triggered": false, "filters_report": {"year": 42, "project_id": 7, "content_match": 0}},
  "operation_evidence": {"index_file": "index.json", "run_log": "run_log.json", "hash_algo": "sha256", "rerun_cmd": "python3 scripts/build_index.py <root> --out /app/work && python3 scripts/search.py ..."},
  "skipped_or_failed": [{"path": "...", "reason": "no_permission|encrypted|no_text_layer|corrupt", "recovery": "已用渲染工具降级提取/如实跳过"}],
  "uncertainty": ["印刷页码与物理页错位±1", "扫描件未入索引，命中不覆盖其中内容"]
}
```

## 5. 数字门槛（达不到诚实标 partial）

- 门槛 A：可读文件入索引率 ≥95% → 否则 partial，列出未入索引清单。
- 门槛 B：top3 命中每条都有完整七元组定位（path/page/section/para/first_sentence/snippet/locator）→ 缺任一项该条降级为 `file_level` 并明示。
- 门槛 C：过滤条件 100% 硬执行 → 任何"放宽条件后给出的命中"必须单独标注 `relaxed=true` 且不计入正式答案。

## 6. 异常处理表

| 情况 | 处置 | 落盘 |
|---|---|---|
| 无权限目录 | 记 skipped，不给猜测内容 | skipped_or_failed |
| 加密/损坏 PDF | 记 unreadable；尝试渲染为图像仅作人工核看，不作为文本证据 | 同上 |
| 扫描件无文本层 | 不入文本索引，uncertainty 声明覆盖盲区 | inventory+uncertainty |
| 重名文件 | 以 sha256 区分，分别给路径 | hits |
| 查询无命中 | empty_result + 逐层过滤计数，不放宽 | empty_result |
| 路径失效（案例运行中文件被移走） | 记 failed，恢复方式：重跑 inventory 重建路径 | run_log |

## 7. 自查清单

- [ ] case_id 原样保留；result.json 在 /app/output。
- [ ] 每条命中可回链（抽查 3 条逐字核对）。
- [ ] 过滤条件未被放宽；空结果如实报告。
- [ ] 副本/旧版本未当成独立证据。
- [ ] unreadable/skipped 全部列出并给恢复方式。

## 8. 效率约束

预算 64 请求/900 秒。步骤 1-2 必须脚本化一次跑完（<60s/千文件）；查询扩展用本地 synonyms.json，不联网；模型请求只用于查询理解与结果组织，≤8 次。先写 result.json 最小版再充实。

## 9. 最小示例（示意输出，非正式案例结果）

输入：`/input/case.json` + 材料目录含 `实验记录_2023/P-2023-015/protocol_v2.pdf`
调用：`python3 scripts/build_index.py 材料根目录 --out /app/work/index.json && python3 scripts/search.py --index /app/work/index.json --query "磷酸盐缓冲液 配方" --filter project_id=P-2023-015 --out /app/output/result.json`
示意输出：`hits[0].locator = "实验记录_2023/P-2023-015/protocol_v2.pdf#page=3,para=4"`，snippet 含"137 mM NaCl，2.7 mM KCl…"。
