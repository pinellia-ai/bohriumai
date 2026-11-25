# README — ppt-6ad93034 学术 PPT 生成与编辑（v1）

## 交付标准清单（从题面提取）

| # | 要求 | 来源 | 落实位置 |
|---|---|---|---|
| 1 | 学术页面生成：取舍+页序规划+每页叙事角色 | 突破方向① | SKILL.md A1（role 字段+取舍规则） |
| 2 | 内容编辑：压缩/扩写/换受众/换语言，术语符号一致 | 方向② | B1-B2（edit_ops+glossary 锁定） |
| 3 | 图表插入：图注/编号/单位/引用，哪些可重绘 | 方向③ | A1 figure.action 规则（redraw 需数据表支撑） |
| 4 | 演示稿迭代：版本可比对、每轮改了什么、可回退 | 方向④ | B3 deck_diff.py changelog + 回退协议 |
| 5 | 模板约束与导出渲染：不塌版、字体不丢、图片不裁 | 方向⑤ | A2/B4 plan_to_pptx 模板继承 + export_check |
| 6 | 输出：可编辑演示文件 | 输出要求表 | result.json deliverables |
| 7 | 输出：页级证据映射 | 输出要求表 | slides[].evidence + evidence_lint |
| 8 | 输出：渲染与版本记录（逐页 diff、运行日志、版本记录） | 输出要求表 | version_log + changelog_v{n}.json |
| 9 | result.json 全字段 + case_id；先落盘最小 result.json | Harbor 契约 | §4 契约 + Step 0 |
| 10 | 编辑产物需 PDF/PNG 预览 | Harbor 契约 | export_check |
| 11 | 材料缺失/无法判断/运行失败分别说明 | 题面 | gaps/uncertainty/status |
| 12 | ≤50 文件 2MB；64 请求 900 秒 | Harbor 契约 | §8 |

## 目录结构

```
v1/
├── SKILL.md            # 双模式流水线（生成 A1-A3 / 编辑 B1-B4 / 迭代 C）
├── README.md
└── scripts/
    ├── result_scaffold.py   # 最小 result.json
    ├── plan_to_pptx.py      # 计划→可编辑 pptx（模板继承+备注）
    ├── deck_diff.py         # 两版计划逐页/字段 diff → changelog
    ├── evidence_lint.py     # 证据映射+数字保真校验
    └── export_check.py      # pptx 完整性+PDF 页数一致
```

## 自测记录（2026-11-24，python 3 + python-pptx 1.0.2）

| 项 | 结果 |
|---|---|
| YAML frontmatter 解析 | PASS（name=academic-deck-generate-edit） |
| output_contract 覆盖 | PASS（输出要求 3 块+Harbor 全字段） |
| 脚本语法 ast.parse ×5 | PASS |
| plan_to_pptx 实跑 3 页 | PASS（slide_count=3） |
| deck_diff 实跑（改 bullets 一处） | PASS（"修改1页"，字段级 diff 正确） |
| evidence_lint 正例/数字篡改反例 | PASS exit 0 / PASS exit 1 |
| export_check 无PDF/页数不一致反例 | PASS exit 3 正确告警 |
| result_scaffold 新建/保留 | PASS |
| 资源限额 | 7 文件 ≈28KB |
| SKILL.md 行数 | 175 行 |

## 已知限制

- 换受众/换语言的"质量"靠 LLM 步骤执行，脚本只保证局部性、术语/数字锁定与导出一致。
- 本地无 LibreOffice，PDF 导出依赖评测环境工具；失败按 §6 标 partial。
