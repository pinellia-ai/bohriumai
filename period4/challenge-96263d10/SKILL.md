---
name: template-format-adapter
description: |
  学术格式与模板适配 Skill。从模板文件与格式要求中抽取可逐项核对的规格清单（栏数/字号/
  行距/页边距/标题层级/题注/参考文献样式/导出格式），按样式（而非外观）完成标题层级、
  编号、图表题注与交叉引用、参考文献条目适配，保证转换完整性（公式/脚注/批注/域代码/
  目录不丢失不图片化），导出可打开、字体嵌入、页码目录可用的成品并保留可编辑源文件。
---

# Template Format Adapter — 学术格式与模板适配 Skill

## 1. 用途与适用范围

"认得准、排得对、转得全、交得出"：把稿件适配到目标模板，输出可交付、可复核的成品。聚焦**模板规格抽取清单 → 样式化排版 → 转换完整性核对 → 导出验证**闭环。字体约束（组织方修订）：使用提供的 Liberation Serif；字体不可用时如实登记，不冒充已嵌入。

## 2. 输入识别（必做第一步）

1. `ls /input/`；读 case.json / task.md，记录 case_id。
2. 盘点：目标模板文件（投稿模板/学位模板/补充规定）、原稿、提供的字体文件。
3. **从模板文件实际抽取规格**（不凭经验猜）：栏数、页面尺寸、页边距、字号、行距、标题层级样式绑定、图表题注位置与字号、参考文献样式（字段顺序/作者截断/标点）、导出格式。互相冲突的规定并列登记。
4. 原稿缺失或模板不可读：status=failed 说明。

## 3. 工作流程

### Step 1 规格清单（认得准）
输出结构化 spec 清单，每项可逐条核对：`{item, required_value, source(模板文件+位置)}`。模板版本差异与冲突规定显式记录。

### Step 2 样式化适配（排得对）
- **标题层级用样式绑定**（Heading 1/2/3 或等价机制），不改字号加粗冒充层级——保证目录与书签自动生成正确。
- 编号规则按模板（章-节-条）；图表题注位置与字号按 spec；交叉引用用引用域而非手写编号。
- 参考文献条目按目标样式逐字段重排（字段顺序、作者截断 et al 规则、标点、中英文混排）。
- 页眉页脚、页码起始按模板设置。

### Step 3 转换完整性（转得全）
转换/套用后逐项核对不丢失：正文段落、图表、公式（保持可编辑，不图片化）、脚注、批注、修订记录、域代码、分节符、嵌入对象、目录。
- 输出转换前后内容单元计数对照表；缺失/合并/改写的单元显式列出并修复或登记。

### Step 4 导出验证（交得出）
- 按要求导出（PDF/Word/LaTeX）：验证文件可打开、页数合理、**字体嵌入**（PDF 字体清单核对，含 Liberation Serif）、页码与目录刷新可用。
- 保留可编辑源文件与导出件两份。
- 页边距与页面尺寸实测（渲染后量测），与 spec 逐项对账。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "template_format_adaptation",
  "status": "success | partial | failed",
  "spec_checklist": [{"item":"columns","required":"double","source":"template.cls line 45","verified":true}],
  "style_bindings": [{"element":"heading1","mechanism":"Heading 1 style","toc_ready":true}],
  "cross_references": {"total":14,"as_fields":14,"broken":0},
  "references_reformatted": {"count":32,"style":"...","issues":[]},
  "conversion_inventory": {"before":{"paragraphs":120,"figures":6,"equations":4,"footnotes":7,"comments":2},
                           "after":{"...同构..."},"lost_or_changed":[]},
  "export": {"file":"output.docx + output.pdf","opens":true,"fonts_embedded":["LiberationSerif"],
             "page_size_ok":true,"toc_page_ok":true,"editable_source":"manuscript_editable.docx"},
  "font_notes": ["提供的Liberation Serif已嵌入；系统缺某字体时如实登记不冒充"],
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：spec 每项带模板出处；交叉引用用域机制；转换前后清点表必须有；导出件实测（打开/字体/页码）后才允许标 success。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 模板规定互相冲突 | 并列登记，采用更严格者，needs_human_review 提示 |
| 字体不可用 | 用提供的 Liberation Serif；仍缺则登记并保留可替换设置 |
| 公式转换成图片 | 视为完整性失败，改用可编辑公式机制重做 |
| 域代码损坏 | 重建引用域，破损清单登记 |
| 预算不足 | 先标题层级与参考文献（最影响评审），status=partial |

## 6. 自查清单

1. [ ] 规格逐项有模板出处，非经验猜测？
2. [ ] 标题层级样式绑定、目录书签可用？交叉引用是域？
3. [ ] 转换清点表无丢失项，或缺失已登记？
4. [ ] 导出件实测可打开、字体嵌入、页码目录正常？
5. [ ] 可编辑源文件保留？
6. [ ] result.json 可解析、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。规格抽取与样式适配优先；导出验证在最后统一跑一次脚本完成（打开/字体/页码检查合并）；转换清点用脚本计数，不逐段人工。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"success",
 "spec_checklist":[{"item":"page_size","required":"A4, margin 2.5cm","source":"README.pdf p1","verified":true}],
 "style_bindings":[{"element":"heading2","mechanism":"Heading 2 style","toc_ready":true}],
 "cross_references":{"total":9,"as_fields":9,"broken":0},
 "conversion_inventory":{"before":{"paragraphs":80,"figures":3,"equations":2,"footnotes":2,"comments":0},"after":{"paragraphs":80,"figures":3,"equations":2,"footnotes":2,"comments":0},"lost_or_changed":[]},
 "export":{"file":"out.pdf","opens":true,"fonts_embedded":["LiberationSerif"],"page_size_ok":true,"toc_page_ok":true,"editable_source":"out.docx"},
 "gaps":[],"uncertainty_notes":[],"changes":[]}
```

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段（如存在）。它定义本案例 `result.json` 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实内容**；contract 里有而本文件 §4 未描述的字段，按 contract 字段语义填实际结果，绝不遗漏；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：一律从 `/input/case.json` 原样读取，禁止自造。
3. **路径**：工作过程写 `/app/work/`；最终产物写 `/app/output/`，主输出为 /app/output/result.json（含 case.json 的 output_contract 全部字段）。
4. **尽早落盘**：先用最小可用结果写一次 /app/output/result.json（含 case.json 的 output_contract 全部字段），再增量增强——任何时刻中断都保证已落盘内容诚实、结构合法（status 如实标 partial）。
5. **不虚构**：无数据、无文件、无软件状态一律不编造；材料缺失写 gaps，无法判断写 uncertainty，禁止把推断写成事实。
6. **可核验**：每个关键结论保留来源定位（页/段/句/表号/图号或文件位置），他人可独立复核。
7. **交付物自检**：本 Skill 的提交材料为 SKILL.md + README.md（使用与方法说明）；运行时按上述契约执行案例。二者不一致处以本节契约为准。
