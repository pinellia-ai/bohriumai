# benchmark-a1d81ca4 · 文献阅读 Benchmark 与评测工具（v1）

## 交付标准清单（自题面提取）

- output_contract 全字段逐字段落实 result.json（以评测时 /input/case.json 为最高优先），含 case_id 原样保留。
- 覆盖六方面：任务定义、数据与答案管理、评分维度、原始输出留存、误差分析、版本迭代。
- 四个验收问题：判得动 / 跑得一致 / 查得回 / 改得动，每步有产物与验收断言。
- 题卡 10 字段齐备且脚本可校验（scripts/validate_itemcard.py）。
- 评分 0/1/2 档、规则可脚本复算、每分带 basis 可追溯。
- 面板按 task_type×input_type×difficulty 三维汇总，不只报总分。
- 失败样例→专项题→只重算受影响分数，链条闭合。
- 运行状态三态（success/partial/failed）+ 不确定性如实登记；不虚构分数与案例结果。
- 资源限额：≤50 文件 / 单文件 ≤500KB / 总量 ≤2MB。

## 自测记录

- YAML frontmatter 可解析：name=literature-reading-benchmark-kit，通过。
- scripts/validate_itemcard.py 语法校验（ast.parse）通过。
- output_contract 覆盖：SKILL.md §4 以 case.json 为最高优先并给出基准全集字段（case_id/status/deliverables/benchmark_summary/evidence_and_boundary/sources/uncertainty_notes/change_log）。
- 文件数 2（SKILL.md + 1 脚本），总量 <2MB，通过。
- SKILL.md 175 行，含数字门槛（§5）、异常处理表（§6）、自查清单（§7）、最小示例（§9）。

## 版本说明

v1 初版：题卡规范 + 统一运行器 + 可复算评分 + 三维面板 + 失败样例库闭环。
