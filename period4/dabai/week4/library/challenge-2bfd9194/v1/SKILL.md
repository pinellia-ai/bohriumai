---
name: sci-library-file-manager
description: |
  科研资料库与文件管理 Skill：把一批混杂的科研文件（仪器数据/扫描件/补充材料/旧版分析稿/改名备份）按约定目录结构真实落库，
  并交付可复核的清单与操作记录。方法主线：盘点+内容哈希→目录模板驱动归位（plan→apply 两阶段）→结构化元数据清单（字段带出处）→
  版本链重建（按内容哈希与命名递进）→归档包与完整性校验。全程幂等、可回滚、落日志；超大文件/中文特殊文件名/无权限/损坏文件
  显式记录为 skipped，绝不静默跳过、绝不同名覆盖、绝不虚构元数据。
---

# 科研资料库与文件管理（Library Ingest & Provenance）

## 1. 用途与适用范围

- **做**：批量文件入库：目录组织、元数据维护、版本管理、长期归档。验收三件事：目录树+元数据清单与约定一致；重复与版本按**内容哈希**判断而非文件名；整个整理过程可被他人按记录复跑核对。
- **不做**：文献检索发现、单篇精读、存储系统底层权限建设。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id` 原样保留、源目录、目标库路径、目录模板/命名约定、元数据字段要求、输出要求。
2. 读 `task.md`，确定：组织维度（项目/年份/数据类型）、命名模板（如 `作者-年份-标题`）、必填元数据字段。
3. 任一关键输入缺失 → `status=failed`，写明缺什么。

## 3. 工作流程（五步，plan→apply 两阶段执行）

### Step 1 盘点（产物 `inventory.json`；脚本 `organize.py scan`）
- 遍历源目录：相对路径、大小、mtime、sha256（≤64MB）、可读性、特殊字符文件名标记。
- 记录权限不足、损坏（哈希失败）、超大（>500MB 只记不入哈希）文件 → `skipped` 清单。

### Step 2 落库计划（产物 `plan.json`；脚本 `organize.py plan`）
- 按 case.json 的目录模板为每个文件生成目标路径：`<库根>/<项目>/<年份>/<数据类型>/`。
- **冲突规则**：目标已存在同名 → 比较 sha256；同哈希=副本（记 alias，不移动）；异哈希=版本（目标名加 `_v2` 后缀，绝不覆盖）；目标路径存在但源哈希相同且已落库 → 幂等跳过（记 no-op）。
- 命名规范化：特殊字符替换表（`/:*?"<>|`→`_`），超长截断 180 字符，中文保留。
- 计划中每条 action：`{action: copy|alias|skip|rename, src, dst, sha256, reason}`。**plan 阶段不动任何文件**。

### Step 3 执行落库（产物 `manifest.json` + `ops_log.jsonl`；脚本 `organize.py apply`）
- 按 plan 逐条执行 copy（默认 copy 不 move，源保留，如 case 要求 move 则记入 ops_log 的 move 记录）。
- 落库后**回读哈希校验**：dst 哈希 != src 哈希 → 标记 `hash_mismatch` 并从 manifest 完成项移入失败项（不写成完成）。
- 每条操作追加 JSONL 日志：时间、action、src、dst、sha256、结果。中断后重跑 apply 会按 manifest+日志续跑（已完成的跳过）。

### Step 4 元数据清单（产物 `metadata.csv` + `metadata.json`）
- 从**文件内容与伴随信息**抽取：标题（首行/文件名）、年份（路径/内容正则）、项目编号（路径/内容）、文件类型、仪器型号（内容关键词，找不到就留空标 `unknown`——**不凭文件名猜**）。
- 每个字段带 `source`：`content:page/line | path | provided`（人工补录）。缺失字段显式 `missing`，不编造。

### Step 5 版本链与归档（产物 `versions.json`、`archive_manifest.json`）
- 版本链：同 base 名异哈希按 mtime 排序成链，记录 `who_replaces_whom` 与**差异要点**（行数/大小/首尾行 diff 概要，文本类文件）。
- 归档包：库根打 zip（或 tar），`archive_manifest.json` 记录每文件 sha256 与总数，校验命令随 result 交付。

## 4. 输出契约（result.json 逐字段）

```json
{
  "case_id": "原样保留",
  "status": "ok|partial|failed",
  "library_tree": "落库后目录树（缩进文本）",
  "manifest": {"total_ingested": 0, "aliased": 0, "skipped": 0, "hash_mismatch": 0},
  "metadata": [{"path": "库内路径", "title": "...", "year": 2023, "project_id": "...", "file_type": "pdf",
                 "instrument": "unknown", "field_source": {"year": "path", "instrument": "missing"}}],
  "versions": [{"chain": ["a_v1.docx", "a_v2.docx"], "latest": "a_v2.docx", "diff_note": "行数 12→45，新增 2.3 节"}],
  "operation_evidence": {"hash_algo": "sha256", "ops_log": "ops_log.jsonl", "manifest": "manifest.json",
                          "plan": "plan.json", "rerun_cmd": "organize.py scan→plan→apply→verify"},
  "skipped_or_failed": [{"path": "...", "reason": "no_permission|hash_mismatch|too_large|corrupt", "recovery": "修复权限后重跑 apply 续跑"}],
  "uncertainty": ["元数据 instrument 字段 3 条缺失，内容无该信息，未猜测"]
}
```

## 5. 数字门槛

- 落库哈希一致率 100%（不一致即 fail 该文件并计入 skipped_or_failed，不静默）。
- 输入批次覆盖率：`manifest.total_ingested + aliased + skipped == inventory.total_files`，逐一对账。
- 元数据必填字段填充率 ≥80%（确实无信息来源的字段如实 missing，计入 uncertainty）。

## 6. 异常处理表

| 情况 | 处置 | 不做 |
|---|---|---|
| 无权限目录/文件 | skipped + recovery 提示 | 静默跳过 |
| 同名不同内容 | dst 加 `_v2`，建版本链 | 覆盖 |
| 上传/复制中断 | manifest 续跑，幂等 | 从头重来 |
| 哈希不符（损坏） | 入失败清单 | 写成完成 |
| 元数据缺失 | missing + uncertainty | 编造字段 |
| 存储空间不足 | 中止并报告剩余空间与已完成数 | 部分写入不记录 |

## 7. 自查清单

- [ ] case_id 原样；result.json 在 /app/output；plan 阶段未动文件。
- [ ] 目录树/清单与输入一一对应（计数对账通过）。
- [ ] 所有移动/复制有日志与哈希，他人可复跑核对。
- [ ] 无同名覆盖、无静默跳过、无编造元数据。

## 8. 效率约束

哈希与大目录遍历全部脚本化；模型请求只用于目录模板决策与元数据疑难判断，≤8 次。先落 result.json 最小版（status+manifest 计数），再充实元数据与版本链。

## 9. 最小示例（示意输出，非正式案例结果）

`organize.py plan 源目录 --template "{project}/{year}/{type}" --out plan.json`
→ plan.json 含 37 条 action（34 copy + 2 alias + 1 skip）；
`organize.py apply plan.json --dst 库根 --log ops_log.jsonl`
→ manifest.json `total_ingested=34, aliased=2`，ops_log 37 行可逐条回放。
