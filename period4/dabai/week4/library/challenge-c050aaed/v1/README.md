# challenge-c050aaed 阅读批注与知识沉淀 v1

## 交付标准清单（自题面提取）

- [x] output_contract：资料结果（批注清单/结构化笔记/关联/检索入口）、操作证据（哈希/脚本版本/复跑命令）、失败与恢复（no_annot_layer/OCR降级/加密损坏）
- [x] result.json 含 case_id + status + uncertainty
- [x] 突破方向覆盖：批注提取（类型/颜色/页码保留不混类）、笔记结构化（批注→笔记多对一全链可反查）、知识关联（basis+强度，控制过度连接，重复/版本归并）、后续检索（tags/实体/来源/时间）
- [x] 锚点校验：verified/verified_normalized/anchor_shift 三态，不静默挂相邻段
- [x] 笔记带原文出处（evidence 回链批注→文件+页+摘录）
- [x] 脚本实跑通过；最小示例标明示意

## 自测记录（2026-11-24）

1. YAML frontmatter PASS；name=annotate-knowledge-harvest。
2. output_contract 字段 100% 覆盖：PASS。
3. ast.parse：annot_extract.py PASS。
4. 语料实跑（markdown 行内批注 3 高亮+2 页边批注 + 无批注文件）：
   - 提取 5 条，subtype 区分 Highlight/FreeText，行号锚点 anchor=verified：PASS
   - 无批注文件记 no_annotation_found（覆盖率对账）：PASS
   - query 按 --q lysis 命中 2 条（高亮+其批注）：PASS
   - PDF 通道：真实 annotation 对象读取（subtype/color/rect/contents）；测试环境无带批注 PDF，通道代码按 pypdf /Annots 标准实现，无批注 PDF 记 no_annot_layer 不虚构
5. 无虚构：无 excerpt 时如实记 no_excerpt/unverified，不猜摘录：PASS

## 调用方式

```bash
python3 scripts/annot_extract.py extract <材料目录> --out /app/work/annotations.json
# Agent 按批注→笔记多对一规则做结构化（notes.json）与关联（links.json），schema 见 SKILL.md §4
python3 scripts/annot_extract.py query /app/work/annotations.json --tags <tag> --q <关键词>
# 汇总写 /app/output/result.json
```

## 边界与限制

- PDF 摘录精确对齐依赖 quadpoints，当前实现以锚点三态如实标注，对不齐标 anchor_shift 不冒充。
- 扫描件 OCR 降级仅辅助人工核看，坐标标 ocr_unverified。
- 关联规则：单术语重合不建 link（防过度连接）。
