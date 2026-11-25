#!/usr/bin/env python3
"""export_check.py — 导出渲染校验: pptx 可打开 + PDF 页数与幻灯片页数一致。

用法: python3 export_check.py <deck.pptx> [deck.pdf]
检查:
  1. pptx 可被 python-pptx 打开且 slide_count>0;
  2. 备注页数与幻灯片页数一致;
  3. 若提供 PDF: 页数与 pptx 页数一致(pypdf, 缺失则回退正则 /Type /Page 计数);
  4. 记录 warnings(如 pdf 缺失、备注缺失)。
退出码: 0 通过; 3 pdf 缺失或页数不一致; 2 pptx 损坏; 2 输入缺失。
输出: JSON 报告。
"""
import json
import os
import re
import sys


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "usage: export_check.py deck.pptx [deck.pdf]"}))
        sys.exit(2)
    pptx_path, pdf_path = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else None)
    warnings = []
    if not os.path.isfile(pptx_path):
        print(json.dumps({"ok": False, "error": "pptx missing: %s" % pptx_path}))
        sys.exit(2)
    try:
        from pptx import Presentation
        prs = Presentation(pptx_path)
        n_slides = len(prs.slides)
        n_notes = sum(1 for s in prs.slides
                      if s.has_notes_slide and s.notes_slide.notes_text_frame.text.strip())
    except Exception as e:
        print(json.dumps({"ok": False, "error": "pptx broken: %s" % e}))
        sys.exit(2)
    if n_slides == 0:
        print(json.dumps({"ok": False, "error": "pptx has 0 slides"}))
        sys.exit(2)
    report = {"pptx": os.path.basename(pptx_path), "slide_count": n_slides,
              "notes_count": n_notes, "warnings": warnings, "ok": True}
    if n_notes < n_slides:
        warnings.append("notes missing on %d slide(s)" % (n_slides - n_notes))
    if pdf_path:
        if not os.path.isfile(pdf_path):
            warnings.append("pdf missing: %s" % pdf_path)
            report["ok"] = False
            report["pdf"] = None
            print(json.dumps(report, ensure_ascii=False))
            sys.exit(3)
        n_pdf = None
        try:
            from pypdf import PdfReader
            n_pdf = len(PdfReader(pdf_path).pages)
        except Exception:
            raw = open(pdf_path, "rb").read()
            n_pdf = len(re.findall(rb"/Type\s*/Page[^s]", raw))
        report["pdf"] = os.path.basename(pdf_path)
        report["pdf_pages"] = n_pdf
        if n_pdf != n_slides:
            warnings.append("pdf pages %s != pptx slides %s" % (n_pdf, n_slides))
            report["ok"] = False
            print(json.dumps(report, ensure_ascii=False))
            sys.exit(3)
    else:
        warnings.append("pdf not provided (export step pending)")
    print(json.dumps(report, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
