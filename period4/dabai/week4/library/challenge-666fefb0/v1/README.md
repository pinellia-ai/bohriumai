# challenge-666fefb0 文献与资料自动分类 v1

## 交付标准清单（自题面提取）

- [x] output_contract：资料结果（分类/标签/改名/去重/批量清单）、操作证据（哈希/plan/ops_log/manifest 可回滚）、失败与恢复（unprocessed/冲突/恢复记录）
- [x] result.json 含 case_id + status + uncertainty
- [x] 突破方向覆盖：文献分类（依据可核对）、标签生成（同义归一≤5个）、自动命名（降级规则）、去重与版本区分（三级判据不误删）、批量整理（幂等/续跑/回滚）
- [x] 真实改动目录而非建议；plan 依据可核对
- [x] 脚本实跑通过；最小示例标明示意

## 自测记录（2026-11-24）

1. YAML frontmatter PASS；name=lit-auto-classifier。
2. output_contract 字段 100% 覆盖：PASS。
3. ast.parse：classify.py PASS。
4. 语料实跑两轮：
   - 轮A（伪 .pdf 无文本层）：3 个进 unprocessed（no_text_layer_or_unreadable），txt 正常分类——无文本层文件不猜测：PASS
   - 轮B（5 个 txt：完全重复副本、DOI 同文、规则命中、无命中）：哈希重复 archive_duplicate、DOI 同文 archive_duplicate+dup_key、uncategorized 兜底、命名降级 degraded 标注：PASS
   - apply 幂等：第二次 run ok=0：PASS
5. 无虚构：作者/年份/DOI 仅在真实命中时填写，缺失走降级：PASS

## 调用方式

```bash
python3 scripts/classify.py classify <输入目录> --rules scripts/tag_rules.json --out /app/work/classification.json
python3 scripts/classify.py apply /app/work/classification.json --src <输入目录> --dst <库根> \
  --log /app/work/ops_log.jsonl --manifest /app/work/manifest.json
# 汇总写 /app/output/result.json（schema 见 SKILL.md §4）
```

## 边界与限制

- 只归档/移动不删除；疑似重复（标题+作者+年份同、哈希异）标 needs_review 交人工。
- 主题规则表按案例领域扩充 scripts/tag_rules.json；无命中进 uncategorized/。
- 文献类型判定基于文件名与首页特征词，unknown 不硬猜。
