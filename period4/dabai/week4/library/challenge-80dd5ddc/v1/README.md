# challenge-80dd5ddc 科研知识库问答 v1

## 交付标准清单（自题面提取）

- [x] output_contract：资料结果（kb_overview/answers/claims+evidence）、操作证据（索引/检索日志/哈希/复跑命令）、失败与恢复（coverage_gap/missing_evidence/conflict）
- [x] result.json 含 case_id + status + uncertainty
- [x] 突破方向覆盖：多文件检索（范围+召回策略）、带来源引用问答（论断↔片段一一对应+置信分级）、证据回链（文件+版本+页/段 locator）、不确定性提示（分级+缺什么）、目录元数据版本管理（副本归并/版本链）
- [x] 缺证敢说"没有依据"；冲突并列不取一方
- [x] 脚本实跑通过；最小示例标明示意

## 自测记录（2026-11-24）

1. YAML frontmatter PASS；name=sci-kb-grounded-qa。
2. output_contract 字段 100% 覆盖：PASS。
3. ast.parse：kb.py PASS。
4. 语料实跑（v1/v2 版本链 + 同内容副本 + 无关文件 + 3 问含缺证问题）：
   - 副本入 dup_groups 不重复索引（3 docs 而非 4）
   - 版本链标注：旧版命中标 "vN(旧版,最新为…)"，最新版优先排序
   - 缺证问题（量子霍尔效应）hit_count=0 → sufficient_evidence=False → missing_evidence 触发并给建议：PASS
   - retrieval_log 记录检索词与 top-k，可复跑：PASS
5. 无虚构：无证据路径不产生 claim；confidence 分级由证据支撑决定：PASS

## 调用方式

```bash
python3 scripts/kb.py build <库根目录> --out /app/work/kb_index.json
python3 scripts/kb.py answer --index /app/work/kb_index.json \
  --query-file questions.txt --case-id <case_id> \
  --out /app/work/answers.json --log /app/work/retrieval_log.json
# Agent 将 candidate_evidence 绑定为 claims（proven/indicative/unresolved）后汇总写 /app/output/result.json
```

## 边界与限制

- 扫描件无文本层 → coverage_gap 声明，不在检索范围。
- 副本按哈希归并只索引主路径；版本链按文件名版本号优先、mtime 兜底。
- 每问题模型开销：改写 1 次 + 证据绑定 1 次。
