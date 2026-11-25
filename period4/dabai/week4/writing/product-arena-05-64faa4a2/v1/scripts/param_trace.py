#!/usr/bin/env python3
"""参数溯源校验：检查 result.json 中正文数值是否都能在四表中找到来源。
用法: python3 param_trace.py result.json （存在无来源数值时退出码 1）"""
import json, re, sys

def numbers_in(s):
    """提取文本中的数字（含科学计数/小数/百分比），排除年份与编号类。"""
    out = []
    for m in re.finditer(r"\d+(?:\.\d+)?(?:[eE][+-]?\d+)?%?", str(s)):
        tok = m.group(0)
        v = tok.rstrip("%")
        if 1900 <= float(v) <= 2100 and "." not in v and "e" not in v.lower():
            continue  # 年份
        out.append(v)
    return out

def table_values(tables):
    vals = set()
    for t in tables or []:
        v = str(t.get("value", ""))
        if v:
            vals.add(v.lstrip("0") or "0")
    return vals

def main():
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    errs = []
    tables = []
    for k in ("material_table", "parameter_table", "qc_table", "procedure_table"):
        tables.extend(data.get(k, []))
    known = table_values(tables)
    text = data.get("chapter_text", "")
    unmatched = []
    for n in numbers_in(text):
        if n.lstrip("0") not in known and n not in known:
            unmatched.append(n)
    # 参数表来源检查
    for i, p in enumerate(data.get("parameter_table", [])):
        if not p.get("source"):
            errs.append(f"parameter_table[{i}] '{p.get('name')}' 无来源（不得入正文）")
    for i, p in enumerate(data.get("parameter_table", [])):
        if p.get("status") == "verified" and p.get("source") in (None, "", "UNVERIFIED"):
            errs.append(f"parameter_table[{i}] status=verified 但无 source")
    print(json.dumps({"ok": not errs and not unmatched, "errors": errs,
                      "numbers_in_text": len(numbers_in(text)),
                      "unmatched_numbers": sorted(set(unmatched)),
                      "table_entries": len(tables)},
                     ensure_ascii=False, indent=2))
    sys.exit(0 if (not errs and not unmatched) else 1)

if __name__ == "__main__":
    main()
