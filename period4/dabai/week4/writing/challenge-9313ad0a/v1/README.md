# challenge-9313ad0a 写作19｜思维导图 v1

## 交付标准清单（自题面提取）

- 抓得准：识别核心概念/研究问题/方法/证据/结论/任务，装饰性词语不入节点。
- 理得清：合理根节点/层级/同级粒度，避免层级混乱、分类交叉、节点重复、重要信息埋没（关键结论≤3级可见）。
- 连得对：因果/依赖/对比/时间/引用/支持/冲突关系边必须有材料依据，无依据连接禁止。
- 证据可追溯：关键节点与关系回溯到材料页码/段落（S-n 定位表），节点分 fact/summary/inference 三级显式标注，推断占比≤20%。
- 交付可打开、可读、可继续编辑：markdown 层级大纲（机读主格式）+ OPML（可导入脑图工具）。
- result.json 落实 output_contract 全字段 + case_id。

## 组件

- SKILL.md：五步流水线（概念抽取→层级组织→关系标注→导图生成→脚本校验交付）。
- scripts/check_mindmap.py：节点规模、evidence 覆盖率、S-n 有效性、关系端点存在性、边 evidence 五项校验。

## 自测记录

1. YAML frontmatter 结构校验：PASS（name=mindmap-builder）。
2. output_contract 覆盖：mindmap.md/mindmap.opml/relations/extract + fact_source_map（节点→S-n→kind）+ version_and_boundaries 全覆盖。PASS。
3. 脚本实跑两轮：第一轮导图引用了索引中不存在的 S-3..S-6，正确 FAIL evidence_valid；补全 source-index 后 5 项全 PASS（exit=0）。OPML XML well-formed 验证通过。
4. 资源限额：3 文件约 12KB ≤2MB。PASS。
