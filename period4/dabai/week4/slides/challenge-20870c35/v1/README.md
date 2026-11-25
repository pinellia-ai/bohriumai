# README — challenge-20870c35 学术汇报内容组织（v1）

## 交付标准清单（从题面提取）

| # | 要求 | 来源 | 落实位置 |
|---|---|---|---|
| 1 | 报告目标：转成可检查目标，定页数/时长/结论强度 | 突破方向① | SKILL.md Step 1 talk_brief（goal+checks+page_budget） |
| 2 | 听众：先验/关注点/质疑 → 铺垫比例、术语范围、证据深度 | 方向② | Step 2 三字段画像+映射规则 |
| 3 | 叙事顺序：问题-方法-结果-结论骨架上取舍铺垫，不按目录搬运 | 方向③ | Step 3 role+取舍规则 |
| 4 | 重点信息：每页唯一主张+证据+证据强度标注 | 方向④ | evidence_strength 字段+措辞匹配规则 |
| 5 | 问答准备：预判追问、备用页、口径一致 | 方向⑤ | Step 4 qa_pack+qa_check.py+backup 页 |
| 6 | 输出：可编辑演示文件 | 输出要求表 | deliverables |
| 7 | 输出：页级证据映射 | 输出要求表 | slides[].evidence+evidence_lint |
| 8 | 输出：渲染与版本记录 | 输出要求表 | coverage.export+version_log |
| 9 | result.json 全字段+case_id；先落盘最小 result.json | Harbor 契约 | §4+Step 0 |
| 10 | 材料缺失/无法判断/运行失败分别说明 | 题面 | gaps/uncertainty/status |
| 11 | ≤50 文件 2MB；64 请求 900 秒 | Harbor 契约 | §8 |

## 目录结构

```
v1/
├── SKILL.md            # 目标→听众→叙事→页主张→问答 六步流水线
├── README.md
└── scripts/
    ├── result_scaffold.py   # 最小 result.json
    ├── plan_to_pptx.py      # 计划→可编辑 pptx
    ├── qa_check.py          # 问答包引用闭合+口径数字保真（本题专用）
    ├── evidence_lint.py     # 溯源+数字保真+六要素
    └── export_check.py      # pptx+PDF 页数一致
```

## 自测记录（2026-11-24，python 3 + python-pptx 1.0.2）

| 项 | 结果 |
|---|---|
| YAML frontmatter 解析 | PASS（name=academic-talk-content-planner） |
| output_contract 覆盖 | PASS（输出 3 块+Harbor 全字段+talk_brief/qa_pack 额外结构） |
| 脚本语法 ast.parse ×6 | PASS |
| plan_to_pptx 实跑 3 页 | PASS |
| evidence_lint 正例/篡改反例 | PASS exit 0 / exit 1 |
| export_check 反例（无PDF/页数不一致） | PASS exit 3 |
| qa_check 正例（3条问答，引用闭合） | PASS exit 0 |
| qa_check 反例（slide_ref 指向不存在页 / answer_key 数字不在源文本） | PASS exit 1 正确拦截 |
| 资源限额 | 9 文件 ≈36KB |
| SKILL.md 行数 | 154 行 |

## 已知限制

- 听众画像与证据强度判断是 LLM 步骤，脚本保证引用闭合/数字保真等可机检部分。
- 本地无 LibreOffice，PDF 导出依赖评测环境工具；失败标 partial 不伪造。
