# challenge-8021aacb 论文结构与逻辑优化 v1

## 交付标准清单（自题面提取）

- 诊得准：结构问题定位到章节/段落/句子+锚文本，并归类（不输出生姜放哪都准的写作原则）。
- 改得动：输出可执行编辑动作五型（move/merge/split/narrow/add-transition），不另起炉灶改写。
- 链得通：研究问题-方法-结果-结论闭环，论点-论据逐条映射（断裂/跳跃/循环/论据不足），跨章呼应。
- 说得清：每条判断指回原文位置与依据，作者可判采纳/部分采纳/驳回。
- 六类覆盖：研究问题与贡献主张对齐、章节结构与叙事顺序、论证链与论据对应、段落关系与重复内容、结论边界与表述尺度——某类确无问题须显式声明而非漏查。
- 本版题面修订：可编辑 JSON/Markdown 即可，不要求 PDF，不要求未请求的全文改写。
- result.json 落实 output_contract 全字段 + case_id。

## 组件

- SKILL.md：六步流水线（章节功能拆解→论点-论据映射→脚本机械检查→结论边界→修改方案→交付）。
- scripts/check_structure.py：重复候选（n-gram）、超长段、弱衔接线索（候选类）+ 编辑动作类型合法性/锚文本原文可检索（硬校验）。

## 自测记录

1. YAML frontmatter 结构校验：PASS（name=structure-doctor）。
2. output_contract 覆盖：edit_plan/revision_notes/claim_evidence_map/section_map + fact_source_map（诊断→锚→依据）+ version_and_boundaries 全覆盖。PASS。
3. 脚本实跑两轮：第一轮发现重复候选漏检（中文短句长度阈值 16 过高），降为 10 后正确检出 1 处重复；硬校验正确拦截坏类型（shout）与原文不可检索锚（"x"）。第二轮干净计划全 PASS（exit=0）。阈值修正过程如实记录。
4. 资源限额：3 文件约 12KB ≤2MB。PASS。
