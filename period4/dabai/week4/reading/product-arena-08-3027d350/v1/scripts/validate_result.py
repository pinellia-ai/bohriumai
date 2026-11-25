#!/usr/bin/env python3
"""校验 result.json 是否满足五层结构契约（文档解析题通用自查）。
用法: python3 scripts/validate_result.py <result.json>"""
import json
import sys

REQUIRED_TOP = ["case_id", "status", "document", "evidence_and_boundary",
                "run_status", "sources", "uncertainty_notes", "change_log"]
DOC_LAYERS = ["metadata", "sections", "paragraphs", "tables", "figures"]


def main():
    if len(sys.argv) < 2:
        print("usage: validate_result.py <result.json>")
        return 2
    with open(sys.argv[1]) as f:
        r = json.load(f)
    errors = []
    for k in REQUIRED_TOP:
        if k not in r:
            errors.append(f"missing top field: {k}")
    doc = r.get("document", {})
    for layer in DOC_LAYERS:
        if layer not in doc:
            errors.append(f"missing document layer: {layer}")
    for p in doc.get("paragraphs", []):
        if "page_no" not in p or "reading_order" not in p:
            errors.append(f"paragraph {p.get('para_id')} missing page_no/reading_order")
    for t in doc.get("tables", []):
        if "cells" not in t or "page_no" not in t:
            errors.append(f"table {t.get('table_id')} missing cells/page_no")
    for u in r.get("evidence_and_boundary", {}).get("unresolved", []):
        if "reason" not in u:
            errors.append("unresolved entry missing reason")
    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("OK: all contract layers covered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
