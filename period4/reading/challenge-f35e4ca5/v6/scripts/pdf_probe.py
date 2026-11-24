#!/usr/bin/env python3
"""PDF 探测: pdf_probe.py <file.pdf> -> probe.json (页数/逐页文本层/字符数/图片数/栏猜测)"""
import json, sys
try:
    import fitz
except ImportError:
    print(json.dumps({"error": "PyMuPDF(fitz) 不可用，改用 pdftotext/pdftotext -layout 逐页"})); sys.exit(1)
d = fitz.open(sys.argv[1])
pages = []
for i, p in enumerate(d):
    t = p.get_text()
    imgs = len(p.get_images())
    pages.append({"page": i + 1, "text_layer": bool(t.strip()), "chars": len(t), "images": imgs})
cols = 2 if pages and pages[0]["chars"] > 1200 and pages[0]["page"] <= 2 else 1
json.dump({"file": sys.argv[1], "pages_total": d.page_count, "text_layers_ok": sum(p["text_layer"] for p in pages), "pages": pages, "column_guess": cols}, open('probe.json', 'w'), ensure_ascii=False, indent=1)
print("probe.json written")
