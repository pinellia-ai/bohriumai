#!/usr/bin/env python3
"""plan_to_pptx.py — 把页级计划(slides_plan.json)构建为可编辑 pptx。

用法: python3 plan_to_pptx.py <slides_plan.json> <out_deck.pptx> [template.pptx]
计划 schema:
{
  "case_id": "string",
  "slides": [
    {"idx": 1, "role": "cover|problem|method|evidence|result|limitation|conclusion|backup",
     "title": "页标题", "claim": "本页唯一主张", "bullets": ["要点..."],
     "notes": "讲解备注(不重复页面文字)",
     "figure": {"ref": "Fig.3", "action": "reuse|redraw|omit", "path": "可选本地图片路径"},
     "evidence": {"locator": "Section 4.2 / Fig.3", "locator_type": "figure|table|section|equation|data|abstract",
                  "quote": "原文短引(<=60字)"}
    }, ...
  ]
}
行为:
- 提供 template.pptx 且文件存在: 从模板继承母版/版式(按版式名优先, 退化用 layouts[0]/[1])。
- figure.path 存在则插入图片(等比缩放到内容区)。
- 每页备注 = notes;证据定位写入备注尾部, 保证"每页可溯源"。
退出码: 0 成功; 2 输入缺失; 4 计划 schema 不合法。
"""
import json
import os
import sys

ROLES = {"cover", "problem", "method", "evidence", "result",
         "limitation", "conclusion", "qa", "backup"}
LOC_TYPES = {"figure", "table", "section", "equation", "data", "abstract", "appendix"}


def fail(code, msg):
    print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False))
    sys.exit(code)


def main():
    if len(sys.argv) < 3:
        fail(2, "usage: plan_to_pptx.py <plan.json> <out.pptx> [template.pptx]")
    plan_path, out_path = sys.argv[1], sys.argv[2]
    tpl_path = sys.argv[3] if len(sys.argv) > 3 else None
    if not os.path.isfile(plan_path):
        fail(2, "plan file missing: %s" % plan_path)
    try:
        plan = json.load(open(plan_path, encoding="utf-8"))
    except Exception as e:
        fail(4, "plan not valid json: %s" % e)
    slides = plan.get("slides")
    if not isinstance(slides, list) or not slides:
        fail(4, "plan.slides must be a non-empty list")
    for i, s in enumerate(slides):
        for k in ("title", "claim", "evidence"):
            if k not in s:
                fail(4, "slide[%d] missing field: %s" % (i, k))
        ev = s["evidence"]
        if not isinstance(ev, dict) or not ev.get("locator") or not ev.get("quote"):
            fail(4, "slide[%d] evidence needs locator+quote" % i)
        if ev.get("locator_type") not in LOC_TYPES:
            fail(4, "slide[%d] bad locator_type" % i)

    from pptx import Presentation
    from pptx.util import Emu

    if tpl_path and os.path.isfile(tpl_path):
        prs = Presentation(tpl_path)
        template_used = os.path.basename(tpl_path)
    else:
        prs = Presentation()
        template_used = "python-pptx default"
    layouts = prs.slide_layouts
    title_layout = layouts[0] if len(layouts) > 0 else None
    body_layout = None
    for lay in layouts:
        names = [p.placeholder_format.type for p in lay.placeholders]
        # 找同时含标题(13/中心标题)与正文体的版式
        if any(str(t).startswith("TITLE") for t in names) and \
           any(str(t).startswith("BODY") or str(t).startswith("OBJECT")
               or str(t).startswith("TEXT") for t in names):
            body_layout = lay
            break
    if body_layout is None and len(layouts) > 1:
        body_layout = layouts[1]

    count = 0
    for i, s in enumerate(slides):
        lay = title_layout if i == 0 and s.get("role") == "cover" else (body_layout or title_layout)
        slide = prs.slides.add_slide(lay)
        # 标题
        title_ph = None
        for ph in slide.placeholders:
            if str(ph.placeholder_format.type).startswith(("TITLE", "CENTER_TITLE")):
                title_ph = ph
                break
        if title_ph is not None:
            title_ph.text = str(s["title"])
        # 正文: 主张 + 要点
        body_ph = None
        for ph in slide.placeholders:
            t = str(ph.placeholder_format.type)
            if t.startswith(("BODY", "OBJECT", "TEXT")) and ph is not title_ph:
                body_ph = ph
                break
        if body_ph is not None:
            tf = body_ph.text_frame
            tf.text = "主张: " + str(s["claim"])
            for b in s.get("bullets", []):
                p = tf.add_paragraph()
                p.text = "• " + str(b)
        # 图片(等比缩放)
        fig = s.get("figure") or {}
        img = fig.get("path")
        if img and os.path.isfile(img):
            try:
                sw, sh = prs.slide_width, prs.slide_height
                pic = slide.shapes.add_picture(img, Emu(int(sw*0.55)), Emu(int(sh*0.25)),
                                               width=Emu(int(sw*0.4)))
                # 高度超界则按高度缩
                if pic.height + pic.top > sh:
                    ratio = (sh - pic.top) / pic.height
                    pic.height = Emu(int(pic.height * ratio))
                    pic.width = Emu(int(pic.width * ratio))
            except Exception as e:
                s.setdefault("warnings", []).append("figure insert failed: %s" % e)
        # 备注: 讲解 + 证据定位(可溯源)
        ev = s["evidence"]
        notes = s.get("notes") or ""
        tail = "\n[主张] %s\n[证据] %s (%s): %s" % (
            s["claim"], ev["locator"], ev.get("locator_type", ""), ev["quote"])
        slide.notes_slide.notes_text_frame.text = notes + tail
        count += 1

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    prs.save(out_path)
    print(json.dumps({"ok": True, "slide_count": count, "output": out_path,
                      "template_used": template_used}, ensure_ascii=False))


if __name__ == "__main__":
    main()
