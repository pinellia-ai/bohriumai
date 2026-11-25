# README — product-arena-04-4b82ad21 引言与相关工作写作 v1

## 交付标准清单（自题面提取）

1. `result.json` 落 `/app/output`：output_contract 全字段 + `case_id` 原样。
2. 目标产物：可直接进入论文的引言与相关工作成稿，四部分（背景/相关工作/空白/贡献）齐全且承接，引用落在具体论断上。
3. 事实与来源映射：他人工作转述与原文一致（带原文位置）、引用元数据真实、空白由已引文献缺口推出、贡献与实际结果相符。
4. 版本与边界：人工确认项、材料缺口、unverified 全部标注。
5. 题面四重点应对：
   - 立得住 → 禁空转铺垫句，背景必须指向具体问题与技术约束。
   - 分得清 → 按方法路线/问题设定分组，同维度比较，related_map 带原文位置。
   - 说得实 → gap_chain 显式推导链，作者判断单独标注。
   - 对得上 → contributions ↔ self_evidence 逐条对齐，claim_cite_check.py 校验。
6. 不编造文献；文献不足落占位标 needs_literature。≤50 文件 / 2MB，标准库脚本。

## 文件清单

- SKILL.md：六步流水线（要素抽取→分组→空白推导→贡献→成稿→对账自检）。
- scripts/claim_cite_check.py：引用绑定/空白链/贡献-证据三重闭合检查，问题存在退出码 1。

## 自测记录（2026-11-25）

- YAML frontmatter 解析：通过。
- output_contract 字段覆盖：契约含 case_id/status/draft_text/related_map/gap_chain/contributions/citation_binding/self_evidence/unverified/weak_claims/sources/uncertainty，覆盖题面五要素要求。
- 脚本语法：ast.parse 通过。
- 脚本实跑：构造合法样例（2 引用绑定 + 1 空白链带位置 + 2 贡献带证据）→ ok=true 退出码 0；
  构造缺陷样例（引用无 locus、空白无位置、贡献无证据）→ 3 类错误全部正确捕获，退出码 1。
- 资源限额：3 文件约 14KB。
- 无虚构：示例为构造输入并标注示意。
