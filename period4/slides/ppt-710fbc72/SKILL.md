---
name: ppt-template-adapter
description: |
  学术 PPT 模板与格式适配 Skill。真实套用指定模板（母版/版式/占位符继承可查）、版式约束
  （固定版心内定位对齐、文本溢出以可解释字号阶梯处理而非压到不可读）、主题字体与颜色继承
  （缺失字体如实登记）、图表等比缩放且编号与引用一致、整册批量一致性（页脚/页码/标题位/
  留白统一）。导出 pptx↔PDF/PNG 一致性横切检查：字体替换、图片丢失、备注错位逐项记录。
  交付可编辑 pptx + 导出件 + 逐页核对记录。
---

# PPT Template Adapter — 学术 PPT 模板与格式适配 Skill

## 1. 用途与适用范围

三标准：① 指定模板被**真实套用**（母版、版式、占位符继承关系可查）；② 页内内容与源论文和图表**对得上**；③ 整册版式与导出结果可复跑、可逐页核对。

六类要素：论文主线、页结构、图表引用、讲解逻辑、模板约束、导出渲染。

## 2. 输入识别（必做第一步）

1. `ls /input/`；读 case.json / task.md 与 workorder，记录 case_id。
2. 盘点：模板文件（母版/版式/占位符结构）、起始 deck（如需编辑适配）、源论文材料、受众/时长/页数约束。
3. 记录模板约束：版心尺寸、主题字体、主题色、占位符清单、页脚页码规则。
4. 模板或源材料缺失：status=failed。

## 3. 工作流程

### Step 1 模板套用（真实继承，可查）
- 解析模板母版/版式/占位符结构；内容写入**对应版式的正确占位符**（标题进 title 占位符、正文进 body 占位符）——不是把文本框拖到页面上冒充。
- 保留主题字体与主题色（theme 引用，不用硬编码色值）；占位符缺失时用规定的替代版式并登记。
- 输出继承关系清单：`{页码 → 版式名 → 占位符 → 内容来源}`，可逐页核对。

### Step 2 版式约束（可解释的字号阶梯）
- 固定版心内定位与对齐；文本框溢出**不许压字号到不可读**——按阶梯处理：精简文字 → 调整字号至下一档（记录理由）→ 拆页。
- 标题过长截断规则、多图并排布局、跨页标题位置一致。

### Step 3 字体与颜色
- 中英文字体搭配与字号层级（标题/正文/注释三档）；主题色与强调色按模板；对比度可读。
- 字体缺失导致的回退**如实登记**（不冒充已嵌入）。

### Step 4 图表适配（对得上）
- 图表按容器**等比缩放或裁切**（绝不拉伸变形）；保留坐标轴与图例可读性。
- 图表编号与正文引用一一对应（论文图号 → 页面引用）；矢量图优先，位图混排标注。

### Step 5 批量一致性 + 导出渲染（横切）
- 整册统一规则：页脚、页码、标题位置、留白、字号层级——批量应用后逐页校验。
- 导出 PDF/PNG：与 pptx 一致性核对——字体替换、图片丢失、备注错位逐项记录；记录导出参数（可复跑）。
- 逐页核对记录：`{页码, 版式, 内容要点, 图表号, 问题}`。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "ppt_template_adaptation",
  "status": "success | partial | failed",
  "inheritance_map": [{"page":1,"layout":"Title Slide","placeholder":"title","content_source":"论文标题","theme_inherited":true}],
  "layout_audit": [{"page":3,"overflow":false,"font_scale_step":"default","action":null}],
  "font_color": {"theme_fonts":true,"missing_fonts":[],"contrast_ok":true},
  "figure_audit": [{"page":4,"figure":"Fig.2","scaled":"proportional","axes_readable":true,"ref_matches_source":true}],
  "consistency_audit": {"footer_uniform":true,"page_numbers":true,"title_position":true,"pages_checked":12},
  "export": {"pdf":"deck.pdf","png_dir":"pages/","font_substitution":[],"images_lost":0,"notes_ok":true,"params_recorded":true},
  "page_review": [{"page":1,"issues":[]}],
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：inheritance_map 逐页可查（证明真实套用）；figure_audit 无变形（scaled=proportional）；导出一致性检查逐项记录；deck 可编辑（pptx 原生对象，非图片拼贴）。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 内容超出页数约束 | 按主线优先级裁剪，取舍登记 |
| 占位符结构不支持某内容 | 用规定替代版式 + 登记 |
| 模板字体系统缺失 | theme 声明保留 + 登记回退 |
| 图源分辨率不足 | 保持等比并登记清晰度风险，不拉伸 |
| 预算不足 | 先模板套用与图表适配（评审硬伤项），一致性校验 partial |

## 6. 自查清单

1. [ ] 母版/版式/占位符真实继承（清单可查）？
2. [ ] 无文本溢出硬塞？字号处理有记录？
3. [ ] 图表无变形、编号与引用一致？
4. [ ] 整册页脚/页码/标题位统一？
5. [ ] 导出与 pptx 一致，字体/图片问题如实登记？
6. [ ] result.json 可解析、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。解析模板结构一次完成；批量规则脚本化应用；导出与校验合并单次执行。中断时已适配页完整可交（partial）。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"success",
 "inheritance_map":[{"page":1,"layout":"Title Slide","placeholder":"title","content_source":"论文标题","theme_inherited":true},
                    {"page":4,"layout":"Two Content","placeholder":"leftBody","content_source":"§3 结果段","theme_inherited":true}],
 "layout_audit":[{"page":4,"overflow":false,"font_scale_step":"default","action":null}],
 "figure_audit":[{"page":4,"figure":"Fig.2","scaled":"proportional","axes_readable":true,"ref_matches_source":true}],
 "consistency_audit":{"footer_uniform":true,"page_numbers":true,"title_position":true,"pages_checked":12},
 "export":{"pdf":"deck.pdf","png_dir":"pages/","font_substitution":[],"images_lost":0,"notes_ok":true,"params_recorded":true},
 "page_review":[{"page":1,"issues":[]}],"gaps":[],"uncertainty_notes":[],"changes":[]}
```

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段（如存在）。它定义本案例 `result.json` 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实内容**；contract 里有而本文件 §4 未描述的字段，按 contract 字段语义填实际结果，绝不遗漏；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：一律从 `/input/case.json` 原样读取，禁止自造。
3. **路径**：工作过程写 `/app/work/`；最终产物写 `/app/output/`，主输出为 /app/output/result.json（含 case.json 的 output_contract 全部字段）。
4. **尽早落盘**：先用最小可用结果写一次 /app/output/result.json（含 case.json 的 output_contract 全部字段），再增量增强——任何时刻中断都保证已落盘内容诚实、结构合法（status 如实标 partial）。
5. **不虚构**：无数据、无文件、无软件状态一律不编造；材料缺失写 gaps，无法判断写 uncertainty，禁止把推断写成事实。
6. **可核验**：每个关键结论保留来源定位（页/段/句/表号/图号或文件位置），他人可独立复核。
7. **交付物自检**：本 Skill 的提交材料为 SKILL.md + README.md（使用与方法说明）；运行时按上述契约执行案例。二者不一致处以本节契约为准。
