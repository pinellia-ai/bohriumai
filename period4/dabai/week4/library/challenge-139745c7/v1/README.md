# challenge-139745c7 科研文件智能检索 v1

## 交付标准清单（自题面提取）

- [x] output_contract：资料结果（目录/清单/元数据/版本关系/知识结构，与输入一一对应）、操作证据（哈希/来源/权限/变更/日志，可复跑核对）、失败与恢复（跳过/冲突/无权限/重复/恢复记录，不把未完成写成完成）
- [x] result.json 含 case_id + status + 主结果 + 证据定位 + 不确定性
- [x] 突破方向覆盖：跨文件语义检索（同义归一）、章节定位（页码+章节+段落+首句）、过滤条件（硬约束不放宽）、证据回链（七元组 locator）、文件组织与版本（哈希副本+版本链）
- [x] 脚本真实可运行、本地实跑通过
- [x] 最小调用示例（标明为示意输出，非正式案例结果）
- [x] 异常处理：无权限/加密/无文本层/重名/空结果/路径失效
- [x] 资源限额：本目录 ≤50 文件、≤2MB

## 自测记录（2026-11-24）

1. YAML frontmatter 可解析，name=sci-file-smart-retrieval 与用途一致：PASS
2. output_contract 三块字段 100% 覆盖（result.json schema 见 SKILL.md §4）：PASS
3. 脚本语法 ast.parse：inventory.py / build_index.py / search.py 全过
4. 最小构造语料实跑（10 个文件：txt/md/csv/pdf/无文本层占位/重名副本/v1-v2 版本链）：
   - inventory.py：文件计数与 find|wc -l 对账一致，副本组与版本链识别正确
   - build_index.py：8 文件入索引，2 个 no_text_layer/unsupported 正确记入 unreadable
   - search.py："缓冲液 配方" 查询命中 target 段落，locator 可在源文件逐字回链；filter project_id 过滤生效；无命中时 filters_report 正确
5. 无虚构：skill 只描述文件系统操作与本地抽取，不引用题面外接口：PASS

## 调用方式（评测时 Agent 按此执行）

```bash
python3 scripts/inventory.py <材料根目录> --out /app/work/inventory.json
python3 scripts/build_index.py <材料根目录> --out /app/work/index.json
python3 scripts/search.py --index /app/work/index.json --query "<用户问题>" \
  [--filter year=2023 --filter project_id=P-xx] --case-id <case_id> \
  --out /app/output/result.json
```

## 边界与限制

- 扫描件无文本层不入文本索引（uncertainty 声明盲区）；OCR 仅作降级人工核看，不作为文本证据。
- 双栏 PDF 段序为抽取顺序；印刷页码未自动对齐时给物理页并在 uncertainty 声明。
- 同义表按案例领域增补（scripts/synonyms.json）。
