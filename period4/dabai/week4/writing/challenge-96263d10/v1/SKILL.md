---
name: academic-format-template-adaptation
description: |
  学术格式与模板适配 Skill。从目标模板/格式要求文件中提取可逐项核对的规格（栏数、字号、行距、页边距、标题层级、图表题注、参考文献样式、导出格式），对输入稿件做逐项适配与保真转换，输出可编辑成品 + 模板规格盘点表 + 逐字段映射表 + 格式校验报告，全程保留来源与修改记录。离线运行：所有结论必须指到输入材料的具体位置（文件名/页/段），材料外内容标 gap，不编造模板规格。
---

# 学术格式与模板适配（模板字段盘点 → 逐字段映射 → 格式校验）

## 1. 用途与适用范围

- 用途：把一份真实稿件按目标模板（期刊/学位论文/院系规定）改到可交付，保留来源与修改记录。
- 适用：docx/tex/md 稿件 + 模板文件或格式说明文本；不适合作画/幻灯片动画类任务。
- 核心方法主线：**模板字段盘点表 → 逐字段映射 → 转换 → 格式校验**，每一步产物落盘可复核。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：记录 `case_id`（原样保留）、任务说明、材料路径、output_contract 全字段。
2. 读 `/input/task.md`（如存在）：提取目标体裁、受众、格式约束、导出要求。
3. 盘点材料文件（pdf-text/pdf-render/office 工具可用时读真实内容）：
   - 模板类：投稿模板、学位论文模板、院系补充规定
   - 稿件类：待适配正文
4. 先落盘最小可用 `result.json`（status=partial、三段占位），保证任何中断有可评分产物。
5. 材料缺失或模板规格不可读 → 不虚构，result.json 标 `status=failed`/`gaps`，说明缺什么。

## 3. 工作流程（六步流水线）

### Step 1 模板字段盘点（产出 `template_spec.md`）
从模板文件逐项提取以下字段，**每项必须带模板中的来源位置**（文件/页/节/原文摘句），凭经验猜测的项标 `inferred` 并给出依据：
- 页面：纸张尺寸、页边距（上下左右）、栏数与栏间距、页眉页脚、页码格式
- 字体字号：正文中西文、各级标题、图表题注、脚注的字体/字号/加粗
- 段落：行距、段前段后、首行缩进、对齐方式
- 标题层级：层级数、编号规则（如 1 / 1.1 / 1.1.1）、样式名、目录要求
- 图表：三线表规格、图注表注位置与字号、编号规则、与正文交叉引用方式
- 参考文献：样式名（GB/T 7714、APA、编号制等）、字段顺序、作者截断、标点
- 导出：目标格式、字体嵌入、文件命名

### Step 2 稿件内容单元盘点（产出 `units_inventory.md`）
列出稿件全部内容单元并编号：标题、段落、图（含题注）、表、公式、脚注、批注、修订、域代码、目录。每单元给 `unit_id` 与来源位置。**转换完整性以这份清单为对账基准。**

### Step 3 逐字段映射（产出 `field_mapping.md`）
表格式逐行：`规格项 | 模板要求（含位置） | 原稿现状（含位置） | 动作（keep/fix/add/convert） | 映射到的样式名或命令`。冲突规定（模板 vs 院系补充）时逐条列出并选优先级高者，冲突本身记入 `uncertainty`。

### Step 4 执行转换（产出成品文件，放 `/app/output/`）
- docx 稿件优先保留 docx 可编辑格式；tex 稿件改 tex 后编译验证。
- 保真红线：正文、图表、公式、脚注、批注、修订、域代码、目录**不删除、不合并、不改写、不图片化**。必须替换的项（如旧样式）在 change_log 记录前后值。
- 保留可编辑源文件；导出件与源文件同交付。

### Step 5 格式校验（产出 `validation_report.md`）
- 跑 `scripts/validate_output.py`（下文 §6）核对成品对 template_spec 逐项符合度。
- 转换完整性对账：units_inventory 中每个 unit_id 在成品中均可指认位置，缺失即 FAIL。
- 导出可用性：文件可打开、字体嵌入（font-discovery 工具核对）、页码目录可刷新。

### Step 6 汇总 result.json（覆盖最小占位）
按 §4 契约写入全部字段，status 如实：全部校验过 = `success`；有项未达 = `partial`（在 limits 中列明哪几项未过）；无法继续 = `failed`。

## 4. 输出契约（result.json 逐字段）

```json
{
  "case_id": "<原样保留>",
  "status": "success | partial | failed",
  "deliverable": {
    "editable_file": "/app/output/manuscript_adapted.docx",
    "export_file": "/app/output/manuscript_adapted.pdf",
    "template_spec": "template_spec.md",
    "field_mapping": "field_mapping.md",
    "validation_report": "validation_report.md"
  },
  "template_fields": [
    {"field": "正文行距", "value": "1.5倍", "source_location": "template.docx p.2 §2", "inferred": false}
  ],
  "facts_sources": [
    {"unit_id": "U-012", "item": "图1题注字号", "source_location": "template.docx p.3 '图题五号宋体'", "action": "fix", "before": "小四", "after": "五号"}
  ],
  "changes": [
    {"unit_id": "U-003", "type": "style", "before": "Heading 1 手动加粗", "after": "绑定样式 '标题1'", "reason": "模板 §3 标题层级要求"}
  ],
  "uncertainty": [
    {"item": "页边距左右值", "issue": "模板版本v2与院系规定冲突(28mm vs 30mm)", "resolution": "采用院系规定优先级条款", "needs_human_confirm": true}
  ],
  "gaps": ["稿件中图2缺少源文件，仅存占位框"],
  "limits": ["校验未覆盖：脚注字体（模板未规定）"],
  "reproduce": "按 README 步骤可从输入件复现到成品"
}
```

字段硬性要求：
- `case_id` 原样；`status` 三值如实；`template_fields` 覆盖 Step 1 盘点的每一项（模板没写的标 `not_specified`）。
- `facts_sources`：每个被改动的数字/术语/题注/引用可逐条回溯，不新增材料外事实。
- `changes`：修改差异逐条记录（before/after/reason）；`uncertainty`：冲突与待人工确认项；`gaps`：材料缺口；`limits`：部分结果边界。

## 5. 数字门槛（达不到如实标 partial）

- 盘点覆盖率：template_spec 字段项 ≥ 20 项且每项有 source_location，否则 partial。
- 映射覆盖率：units_inventory 中每个内容单元在 field_mapping 中有对应动作行，否则 partial。
- 校验通过率：validation_report 中 FAIL 项 > 0 时 status=partial。
- 保真红线：成品内容单元数 < 原稿单元数（无据删除）→ 立即回滚并修复。

## 6. 校验脚本

捆绑 `scripts/validate_output.py`（纯标准库）：输入 template_spec 解析出的规格表 + 成品文本/样式抽取结果（JSON），输出逐项 PASS/FAIL 与转换完整性对账结果。用法见脚本 docstring；先构造最小样例实跑再用于正式案例。

## 7. 异常处理表

| 异常 | 处置 |
|---|---|
| 模板文件缺失/不可读 | result.json status=failed，gaps 写明，不凭经验生成规格 |
| 模板与院系规定冲突 | 两条均列出，按优先级条款取用，uncertainty 记录 needs_human_confirm |
| 字体缺失 | 按组织方修订使用提供的 Liberation Serif；原缺失输入视为历史遗留，不回改 |
| 转换中内容单元丢失 | 以 units_inventory 对账定位丢失项，回滚重转，不静默跳过 |
| 导出失败 | 保留可编辑源文件 + 上一次成功导出件，limits 注明导出失败原因 |
| 材料含需人工确认项 | 保留原样并标注，不擅自定稿 |

## 8. 效率约束

预算 64 请求 / 900 秒：Step 0-2 合并到前 10 个请求内；转换优先脚本化批量处理；先落最小 result.json 再充实。产物总量 ≤50 文件 / 2MB（不含运行时二进制产物）。

## 9. 最小示例（示意，非正式案例结果）

输入：稿件 draft.docx + 模板 spec.txt（"正文宋体小四 1.5 倍行距，页边距上下 2.54cm 左右 3.17cm，GB/T 7714"）。
调用：按 Step 1→6 执行。
示意输出：template_spec.md 7 项带位置；field_mapping 12 行；result.json status=success，deliverable.editable_file 指向 docx，facts_sources 含 3 条 before/after。

## 11. 命令序列（Agent 执行参考）

```
1. cat /input/case.json           # case_id + output_contract
2. 落最小 result.json（status=partial 占位）
3. 解析模板 → template_spec.md（每项 source_location）
4. 盘点稿件单元 → units_inventory.md
5. 写 field_mapping.md → 批量执行映射动作
6. python3 scripts/validate_output.py spec.json actual.json units.json
7. 修 FAIL 项 → 重跑校验 → status 定为 success/partial
8. 导出 PDF 预览 → 最终 result.json
```

失败对照：跳过 Step 1-2 直接排版 = 凭猜测改格式，是前人低分主因；Step 5 对账不可省。

## 12. 自查清单（交前全过）

- [ ] YAML frontmatter 可解析
- [ ] template_fields 每项有 source_location（含 not_specified 标注）
- [ ] field_mapping 覆盖全部内容单元
- [ ] result.json 含 case_id + status + deliverable + facts_sources + changes + uncertainty + gaps + limits
- [ ] 成品可编辑 + 导出件可打开
- [ ] 脚本 `python3 -c "import ast; ast.parse(open(f).read())"` 通过
- [ ] ≤50 文件 / 2MB
