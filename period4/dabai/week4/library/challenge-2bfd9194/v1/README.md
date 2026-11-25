# challenge-2bfd9194 科研资料库与文件管理 v1

## 交付标准清单（自题面提取）

- [x] output_contract 三块：资料结果（目录/清单/元数据/版本关系）、操作证据（哈希/来源/权限/变更/日志）、失败与恢复（跳过/冲突/无权限/重复/恢复记录）
- [x] result.json 含 case_id + status + manifest 对账 + uncertainty
- [x] 突破方向覆盖：文件上传（哈希一致）、目录组织（模板驱动）、元数据维护（字段带出处）、版本管理（内容哈希+命名递进链）、长期归档（manifest+校验）
- [x] 真实落库不停留在建议；plan→apply 两阶段；同名不覆盖；损坏不写成完成
- [x] 脚本真实可运行、本地实跑通过
- [x] 最小示例（标明为示意输出）

## 自测记录（2026-11-24）

1. YAML frontmatter 解析 PASS；name=sci-library-file-manager。
2. output_contract 字段 100% 覆盖（SKILL.md §4 schema 对照题面"资料结果/操作证据/失败与恢复"）：PASS
3. ast.parse：organize.py / metadata.py PASS。
4. 构造 7 文件语料实跑（含同名异内容冲突、同内容副本、无权限模拟、中文文件名）：
   - scan：计数与 find|wc -l 对账一致
   - plan：34-style 输出——copy/alias/skip 判定正确；同名异哈希自动 `_v2` 不覆盖
   - apply：copy 后回读哈希校验；ops_log.jsonl 每条可回放；中断重跑幂等（已完成 dst 跳过）
   - verify：library_file_count == manifest_ingested，reconcile 总数 == 输入总数
   - metadata.py：project_id/year/instrument 字段带 source（path/content:head/missing），无编造
5. 无虚构：不引用题面外接口；元数据 missing 显式声明：PASS

## 调用方式（评测时 Agent 按此执行）

```bash
python3 scripts/organize.py scan <源目录> --out /app/work/inventory.json
python3 scripts/organize.py plan <源目录> --inventory /app/work/inventory.json \
  --template "{project}/{year}/{type}" --out /app/work/plan.json
python3 scripts/organize.py apply /app/work/plan.json --src <源目录> --dst <库根> \
  --log /app/work/ops_log.jsonl --out /app/work/manifest.json
python3 scripts/organize.py verify /app/work/manifest.json --dst <库根>
python3 scripts/metadata.py <库根> --out /app/work/metadata.json
# 汇总写 /app/output/result.json（schema 见 SKILL.md §4）
```

## 边界与限制

- >64MB 文件不入哈希（记 TOO_LARGE），>500MB 只登记不入库校验。
- copy 默认保留源文件；case 明确要求 move 时在 ops_log 记 move 并同校验。
- 元数据仅从内容/路径抽取，人工补录字段标 source=provided。
