#!/usr/bin/env python3
"""引用扫描: citation_scan.py <paper.txt|md> -> citations.csv (编号式[3]与作者年份式全部捕获)"""
import re, sys, csv
text = open(sys.argv[1]).read()
pat = re.compile(r'(\[\d+(?:\s*[,-]\s*\d+)*\])|(\([A-Z][A-Za-z\-]+(?:\s+et\s+al\.?)?,?\s*\d{4}[a-z]?\))')
sentences = re.split(r'(?<=[.!?])\s+', text)
rows, seen = [], 0
pos = 0
for si, s in enumerate(sentences):
    for m in pat.finditer(s):
        seen += 1
        rows.append([f'c{seen}', m.group(0), s.strip()[:200], f'sentence#{si+1}'])
with open('citations.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['cite_id', 'marker', 'sentence', 'locator']); w.writerows(rows)
print(f"citations.csv: {seen} in-text citations")
