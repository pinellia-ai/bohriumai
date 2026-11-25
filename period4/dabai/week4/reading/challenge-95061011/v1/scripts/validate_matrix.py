#!/usr/bin/env python3
"""validate_matrix.py — 校验多文档比较矩阵（95061011 用）。

用法:
  python3 validate_matrix.py --result result.json --workorder comparison-workorder.json \
      [--corpus-dir DIR]     # 提供语料目录时做 quote 子串匹配
  python3 validate_matrix.py --selftest

校验项:
  1) 矩阵覆盖工单全部 document_id，无缺行
  2) 非空格必有 source_document_id/paragraph_id/quote；提供语料时 quote 子串匹配
  3) not_reported 格 value 必须为 null
  4) comparability 六项判定存在（任何有 ≥2 篇数值时）
  5) conflict 必有 attribution
"""
import argparse, json, os, sys

CELL_STATUS = {"reported", "not_reported", "noncomparable", "source_conflict", "missing-source"}


def corpus_texts(corpus_dir):
    texts = {}
    if corpus_dir and os.path.isdir(corpus_dir):
        for root, _d, files in os.walk(corpus_dir):
            for fn in files:
                p = os.path.join(root, fn)
                try:
                    with open(p, encoding="utf-8", errors="ignore") as f:
                        texts[fn] = f.read()
                except OSError:
                    pass
    return texts


def validate(result, workorder, texts):
    errors, warnings = [], []
    req_docs = set(workorder.get("documents") or
                   [d.get("document_id") for d in workorder.get("document_list", []) if d])
    got_docs = {r.get("source_document_id") for r in result.get("comparison_matrix", [])}
    if req_docs:
        for m in req_docs - got_docs:
            errors.append(f"矩阵缺行: {m}")
    n_values = 0
    for row in result.get("comparison_matrix", []):
        doc = row.get("source_document_id", "?")
        cells = row.get("cells", {})
        if not cells:
            warnings.append(f"{doc}: 行无任何格")
        for fname, cell in cells.items():
            st = cell.get("status")
            if st not in CELL_STATUS:
                errors.append(f"{doc}/{fname}: 非法 status '{st}'")
                continue
            if st == "reported":
                n_values += 1
                q = cell.get("quote")
                if not (cell.get("paragraph_id") and q):
                    errors.append(f"{doc}/{fname}: reported 缺 paragraph_id/quote")
                elif texts:
                    blob = "\n".join(texts.values())
                    if q not in blob:
                        errors.append(f"{doc}/{fname}: quote 在语料中子串匹配失败")
            if st == "not_reported" and cell.get("value") is not None:
                errors.append(f"{doc}/{fname}: not_reported 但 value 非 null")
    comp = result.get("comparability", {})
    if n_values >= 2:
        keys = [k for k in ("task", "metric", "units", "material", "pollutant", "budget")
                if k in comp]
        if len(keys) < 6:
            warnings.append(f"comparability 六项判定不全（缺 {6 - len(keys)} 项），定量合成前必须补齐")
    for c in result.get("consistency", []):
        if c.get("verdict") == "conflict" and not c.get("attribution"):
            errors.append(f"{c.get('dimension', '?')}: conflict 但无 attribution")
    return errors, warnings


def selftest():
    workorder = {"documents": ["docA", "docB"]}
    result = {"case_id": "demo-cmp", "status": "success",
              "comparison_matrix": [
                  {"source_document_id": "docA", "cells": {
                      "metric_value": {"value": "78.4", "units": "%", "status": "reported",
                                       "paragraph_id": "p09", "dataset": "RhB", "metric": "removal 120min",
                                       "quote": "removal efficiency of RhB reached 78.4% after 120 min"}}},
                  {"source_document_id": "docB", "cells": {
                      "metric_value": {"value": "91.0", "units": "%", "status": "reported",
                                       "paragraph_id": "p04", "dataset": "MB", "metric": "removal 60min",
                                       "quote": "91.0% of MB was removed within 60 min"},
                      "catalyst_dose": {"value": None, "units": None, "status": "not_reported",
                                        "paragraph_id": None, "quote": None}}}],
              "comparability": {"task": "both degradation", "metric": "different contact times",
                                "units": "both %", "material": "different dyes",
                                "pollutant": "RhB vs MB noncomparable", "budget": None},
              "consistency": [{"dimension": "direction", "verdict": "partially_consistent",
                               "attribution": {"cause": "conditions"}}]}
    texts = {"docA.txt": "removal efficiency of RhB reached 78.4% after 120 min",
             "docB.txt": "91.0% of MB was removed within 60 min"}
    errs, warns = validate(result, workorder, texts)
    print(f"selftest: errors={errs} warnings={warns}")
    return not errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--result"); ap.add_argument("--workorder"); ap.add_argument("--corpus-dir")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if not (a.result and a.workorder):
        ap.error("--result 与 --workorder 必填（或用 --selftest）")
    with open(a.result, encoding="utf-8") as f:
        result = json.load(f)
    with open(a.workorder, encoding="utf-8") as f:
        workorder = json.load(f)
    errs, warns = validate(result, workorder, corpus_texts(a.corpus_dir))
    for e in errs:
        print(f"ERROR: {e}")
    for w in warns:
        print(f"WARN: {w}")
    print(f"{len(result.get('comparison_matrix', []))} 行, {len(errs)} 错误, {len(warns)} 警告")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
