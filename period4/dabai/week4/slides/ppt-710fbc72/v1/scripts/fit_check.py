#!/usr/bin/env python3
"""fit_check.py — 版式约束校验: 文本溢出风险 + 字号下限 + 标题长度。

用法: python3 fit_check.py <deck.pptx> [--min-font 12] [--max-title 40]
启发式(明确标注为估算, 不是渲染级精判):
  - 每个文本框容量 ≈ (shape宽/平均字宽) × (shape高/行高), 平均字宽按
    中英混排取 0.62×字号(pt→EMU 换算), 行高取 1.35×字号;
  - 文本字符数(全角计1, 半角计0.6) > 容量×0.9 → overflow 风险;
  - 实际字号 < min_font → small-font 风险;
  - 标题字符数 > max_title → long-title 提示。
退出码: 0 无风险; 1 存在 overflow/small-font 风险; 2 输入缺失。
输出: JSON 报告(逐 shape 定位 slide_idx/shape_name, 可据此改字号或删要点)。
"""
import json
import sys

import os


def width_chars(text):
    units = 0.0
    for ch in text:
        units += 1.0 if ord(ch) > 0x2E80 else 0.6
    return units


def main():
    args = sys.argv[1:]
    if not args:
        print(json.dumps({"ok": False, "error": "usage: fit_check.py deck.pptx [--min-font 12]"}))
        sys.exit(2)
    deck = args[0]
    min_font, max_title = 12, 40
    if "--min-font" in args:
        min_font = int(args[args.index("--min-font") + 1])
    if "--max-title" in args:
        max_title = int(args[args.index("--max-title") + 1])
    if not os.path.isfile(deck):
        print(json.dumps({"ok": False, "error": "deck missing"}))
        sys.exit(2)
    from pptx import Presentation
    from pptx.util import Emu
    prs = Presentation(deck)
    PT = 12700  # EMU per pt
    risks = []
    for si, slide in enumerate(prs.slides, 1):
        for sh in slide.shapes:
            if not sh.has_text_frame:
                continue
            tf = sh.text_frame
            text = tf.text or ""
            if not text.strip():
                continue
            sizes = [r.font.size.pt for p in tf.paragraphs for r in p.runs
                     if r.font.size is not None]
            eff_pt = min(sizes) if sizes else 18.0
            if sizes and eff_pt < min_font:
                risks.append({"slide": si, "shape": sh.name, "type": "small-font",
                              "detail": "min font %.1fpt < %dpt" % (eff_pt, min_font)})
            w_in = sh.width / 914400 if sh.width else 10
            h_in = sh.height / 914400 if sh.height else 5
            # 每行可容纳字符数(按有效字号), 行数
            char_w_in = eff_pt * 0.62 / 72.0
            line_h_in = eff_pt * 1.35 / 72.0
            cap = max(1, int(w_in / char_w_in)) * max(1, int(h_in / line_h_in))
            need = width_chars(text)
            if need > cap * 0.9:
                risks.append({"slide": si, "shape": sh.name, "type": "overflow",
                              "detail": "chars≈%.0f > capacity≈%.0f" % (need, cap)})
            is_title = str(sh.shape_type).startswith("PLACEHOLDER") and \
                "TITLE" in sh.name.upper()
            if is_title and width_chars(text) > max_title:
                risks.append({"slide": si, "shape": sh.name, "type": "long-title",
                              "detail": "title len=%.0f > %d" % (width_chars(text), max_title)})
    report = {"ok": not any(r["type"] in ("overflow", "small-font") for r in risks),
              "deck": os.path.basename(deck), "n_slides": len(prs.slides),
              "risks": risks,
              "note": "启发式估算, overflow 建议减要点或调字号后重跑"}
    print(json.dumps(report, ensure_ascii=False, indent=1))
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
