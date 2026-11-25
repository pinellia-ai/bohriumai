# README — product-arena-03-429cc14d 参考文献与引用管理 v1

## 交付标准清单（自题面提取）

1. `result.json` 落 `/app/output`：output_contract 全部原始字段 + `case_id` 原样。
2. 目标产物：可继续编辑的稿件 + 同步的文献表。
3. 事实与来源映射：每条引用可回溯到真实、可定位的文献记录与稿件位置；不新增材料外事实。
4. 版本与边界：改动差异、合并判据、人工确认项、异常全部标注。
5. 题面四重点的应对：
   - 挂得对 → 引用点带 locus+claim_snippet，段末/图注附近标记 misplaced。
   - 编得顺 → 编号重排按首现顺序，audit.numbering_issues 检查连续性。
   - 收得净 → 去重判据（DOI 相同 / 题名+首作者+年份），每次合并写 merge_records。
   - 对得上 → 论断-文献逐点 match/mismatch/uncertain + note，不可核验标 unverified。
6. 不编造文献；DOI 解析失败不判真假。资源 ≤50 文件 / 2MB，脚本仅标准库。
7. 预算 64 请求 / 900 秒；不预制答案。

## 文件清单

- SKILL.md：skill 本体（六步流水线，双向对账为核心步骤）。
- scripts/cite_audit.py：双向对账脚本——提取文内引用点（[n]/\cite）与文献条目，
  报告 dangling citations / orphan entries / 编号顺序问题 / 疑似重复，问题存在时退出码 1。

## 自测记录（2026-11-25）

- YAML frontmatter 解析：通过。
- output_contract 字段覆盖：result.json 契约含 case_id/status/revised_manuscript/reference_list/citation_points/entries/merge_records/audit/unverified/sources/uncertainty，覆盖题面三块要求。
- 脚本语法：ast.parse 通过。
- 脚本实跑（最小输入构造）：
  - 稿件含 `[1] [2,3] [5-7] \cite{x1}`，bib 含 x1 与两条同 DOI 条目；
  - 输出正确识别 dangling（2,3,5,6,7 无条目）、orphan、duplicate（doi_same）、首现顺序问题；退出码 1。
  - 修正稿件后重跑，ok=true 退出码 0。
- 资源限额：3 文件约 15KB。
- 无虚构：示例为构造输入，明确标注示意。
