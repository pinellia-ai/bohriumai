#!/usr/bin/env python3
"""元数据清单：从路径与文件内容抽取字段，每个字段带出处；缺失标 missing 不猜测。
用法: python3 metadata.py <库根目录> --out metadata.json [--fields title,year,project_id,instrument]
"""
import argparse, json, os, re

FIELD_PATTERNS = {
    "project_id": [r'(P[-_]\d{3,}[-_]?\d{0,4})', r'(project[-_][\w-]+)'],
    "year": [r'(20\d{2})'],
    "instrument": [r'(HPLC|GC[- ]?MS|LC[- ]?MS|qPCR|离心机|色谱|质谱|分光光度计)', r'(instrument[:：]\s*\S+)'],
}
TITLE_HINT = re.compile(r'^(.{5,120})$')

def extract_fields(rel, content_head):
    fields, source = {}, {}
    for k, pats in FIELD_PATTERNS.items():
        val = None; src = "missing"
        m = re.search(pats[0], rel)
        if m:
            val, src = m.group(1), "path"
        else:
            for pat in pats[1:]:
                m = re.search(pat, content_head, re.I)
                if m:
                    val, src = m.group(1)[:60], "content:head"
                    break
        fields[k] = val if val else "missing"
        source[k] = src
    lines = [l.strip() for l in content_head.splitlines() if l.strip()]
    title = lines[0][:100] if lines else os.path.splitext(os.path.basename(rel))[0]
    fields["title"] = title; source["title"] = "content:first_line" if lines else "filename"
    return fields, source

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root"); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rows, missing_cnt = [], 0
    for dp, _, fns in os.walk(a.root):
        for n in sorted(fns):
            fp = os.path.join(dp, n)
            rel = os.path.relpath(fp, a.root)
            try:
                head = open(fp, encoding='utf-8', errors='ignore').read(4000)
            except Exception:
                head = ""
            fields, source = extract_fields(rel, head)
            fields["file_type"] = os.path.splitext(n)[1].lstrip('.').lower()
            fields["path"] = rel
            missing_cnt += sum(1 for k, v in fields.items() if v == "missing" and k != "instrument")
            rows.append({"path": rel, **fields, "field_source": source})
    json.dump({"root": a.root, "n_rows": len(rows), "rows": rows,
               "note": "missing=内容与路径均无信息来源，未猜测"}, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print(f"metadata for {len(rows)} files -> {a.out} (missing fields: {missing_cnt})")

if __name__ == "__main__":
    main()
