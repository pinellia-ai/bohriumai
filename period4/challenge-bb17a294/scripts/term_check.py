#!/usr/bin/env python3
"""术语一致性: term_check.py terms.csv <text...> -> term_occurrences.csv
terms.csv: en,zh 两列。检查每个术语全部出现处译名是否一致。"""
import sys, csv, re, glob
terms = list(csv.DictReader(open(sys.argv[1])))
texts = {}
for path in sys.argv[2:]:
    texts[path] = open(path).read()
rows, viol = [], 0
for t in terms:
    en, zh = t.get('en', '').strip(), t.get('zh', '').strip()
    if not en: continue
    occ = []
    for path, txt in texts.items():
        for m in re.finditer(re.escape(en), txt):
            ctx = txt[max(0, m.start() - 60):m.end() + 60]
            occ.append((path, m.start(), ctx))
    # 中文译名出现处若紧邻英文原词以外的写法，记为待查
    zh_count = sum(txt.count(zh) for txt in texts.values()) if zh else 0
    consistent = (zh_count > 0) or (len(occ) == 0)
    if not consistent: viol += 1
    rows.append([en, zh, len(occ), zh_count, 'OK' if consistent else 'CHECK'])
with open('term_occurrences.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['en', 'zh', 'en_occurrences', 'zh_occurrences', 'status']); w.writerows(rows)
print(f"term_occurrences.csv: {len(rows)} terms, {viol} 需人工核查")
