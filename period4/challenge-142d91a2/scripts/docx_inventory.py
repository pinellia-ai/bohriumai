#!/usr/bin/env python3
"""DOCX 清点: docx_inventory.py <file.docx> -> inventory.json (段/表/图/批注计数, 样式分布)"""
import json, sys
try:
    from docx import Document
except ImportError:
    print(json.dumps({"error": "python-docx 不可用"})); sys.exit(1)
doc = Document(sys.argv[1])
styles = {}
for p in doc.paragraphs:
    s = p.style.name if p.style else 'None'
    styles[s] = styles.get(s, 0) + 1
inv = {"file": sys.argv[1], "paragraphs": len(doc.paragraphs), "tables": len(doc.tables),
       "table_rows": sum(len(t.rows) for t in doc.tables), "inline_images": len(doc.inline_shapes),
       "sections": len(doc.sections), "style_distribution": styles}
json.dump(inv, open('inventory.json', 'w'), ensure_ascii=False, indent=1)
print("inventory.json written")
