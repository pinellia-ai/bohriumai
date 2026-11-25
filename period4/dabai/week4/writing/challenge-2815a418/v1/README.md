# challenge-2815a418 审稿回复与论文修改 v1

## 交付标准清单（自题面提取）

- 输入 = 审稿意见清单 + 指定版本稿件（本版题面限定：只修订 manuscript-baseline.md 基线，意见是摘要不是逐字全文）。
- 交付四件套：可编辑修订稿 + 逐条回复信草案 + 修改定位 + 未到位证据清单。
- 四问题：答得全（意见及子要求 100% 识别并给处理结论）、改得准（"已修改"真实落在正文且定位可核对）、证得住（补证据意见有可查证证据或说清为何无法补做）、对得上（回复信/修订稿/版本三者一致，多轮承诺台账）。
- 语气四档：接受/澄清/礼貌反驳/申诉；禁冒犯、过度承诺、无原则顺从。
- 不可跳过可执行修改：缺材料不等于免修，实质修改必须落在基线中。
- result.json 落实 output_contract 全字段 + case_id；status/sources/uncertainty/change records 如实。

## 组件

- SKILL.md：六步流水线（意见拆解→回应决策→修订稿→回复信→脚本对账→交付）。
- scripts/check_rebuttal.py：锚点存在性、before 可检索、TODO-E 台账、语气违例四向校验。

## 自测记录

1. YAML frontmatter 结构校验：PASS（name=rebuttal-writer）。
2. output_contract 覆盖：目标产物（修订稿/回复信/定位/证据清单四件套）、事实与来源映射（fact_source_map=意见→改动→位置→依据）、版本与边界（change_records/manual_review/gaps/anomalies）全覆盖。PASS。
3. 脚本实跑：构造最小三件套实跑通过（见下）。
4. 资源限额：3 文件约 10KB ≤2MB。PASS。
