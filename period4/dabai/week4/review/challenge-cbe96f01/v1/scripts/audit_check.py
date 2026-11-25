#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_check.py — 引用与事实核验 result.json / citation_ledger / findings 交付验收器。

用法: python3 audit_check.py /app/output/result.json [--workdir /app/output]
验收（全过退出码 0；任一失败退出码 1）:
  1. result.json 顶层字段齐全; status 合法; partial/failed 有界限说明; case_id 非空
  2. findings.json 每条七件齐全且 location.quote 非空（无引用=零分风险）
  3. citation_spots.csv 与 citation_ledger.csv 行数一致，spot 全覆盖
  4. verdict ∈ {fully_supported, partially_supported, unsupported, undeterminable}
  5. unsupported 必须有引文主张对照; undeterminable 必须写缺什么证据
  6. coverage 六类键齐全
"""
import argparse, csv, json, os, sys

CATEGORIES = ["citation_support", "source_reliability", "numeric_consistency",
              "argument_chain", "fact_verification", "academic_norm"]
VERDICTS = {"fully_supported", "partially_supported", "unsupported", "undeterminable"}
ISSUE_TYPES = {"fact_error", "insufficient_evidence", "norm_issue", "suggestion", "pending_review"}
REQUIRED_TOP = ["case_id", "status", "deliverables", "review_report",
                "evidence_and_boundary", "coverage", "sources", "uncertainty_notes"]
FINDING_FIELDS = ["id", "category", "location", "issue_type", "severity", "evidence", "recommendation"]

def read_rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("result_json")
    ap.add_argument("--workdir", default=None)
    a = ap.parse_args()
    w = a.workdir or os.path.dirname(os.path.abspath(a.result_json))
    fails = []

    try:
        res = json.load(open(a.result_json, encoding="utf-8"))
    except Exception as e:
        print(f"FAIL result.json 无法解析: {e}"); sys.exit(1)
    for k in REQUIRED_TOP:
        if k not in res: fails.append(f"result.json 缺顶层字段 {k}")
    if res.get("status") not in ("success", "partial", "failed"):
        fails.append(f"status 非法: {res.get('status')!r}")
    if res.get("status") in ("partial", "failed"):
        b = res.get("evidence_and_boundary", {})
        if not (b.get("unchecked") or b.get("pending_review") or res.get("failure_reason")):
            fails.append("partial/failed 未说明界限")
    if not res.get("case_id"): fails.append("case_id 为空")

    fpath = os.path.join(w, "findings.json")
    findings = []
    if os.path.exists(fpath):
        try: findings = json.load(open(fpath, encoding="utf-8"))
        except Exception as e: fails.append(f"findings.json 无法解析: {e}")
    for f_ in findings:
        fid = f_.get("id", "?")
        for k in FINDING_FIELDS:
            if not f_.get(k): fails.append(f"finding {fid} 缺字段 {k}")
        if f_.get("issue_type") not in ISSUE_TYPES:
            fails.append(f"finding {fid} issue_type 非法: {f_.get('issue_type')!r}")
        if f_.get("category") not in CATEGORIES:
            fails.append(f"finding {fid} category 非法: {f_.get('category')!r}")
        loc = f_.get("location") or {}
        for k in ("file", "locator", "quote"):
            if not loc.get(k): fails.append(f"finding {fid} location 缺 {k}")

    spots, ledger = [], []
    sp = os.path.join(w, "citation_spots.csv")
    lg = os.path.join(w, "citation_ledger.csv")
    if os.path.exists(sp):
        spots = read_rows(sp)
    else:
        fails.append("citation_spots.csv 缺失")
    if os.path.exists(lg):
        ledger = read_rows(lg)
    else:
        fails.append("citation_ledger.csv 缺失")
    if spots and ledger:
        spot_ids = {r.get("spot_id") for r in spots}
        led_ids = [r.get("spot_id") for r in ledger]
        if set(led_ids) != spot_ids:
            fails.append(f"citation_ledger spot 覆盖不一致: spots={len(spot_ids)} ledger={len(set(led_ids))}")
        for r in ledger:
            v = r.get("verdict")
            if v not in VERDICTS:
                fails.append(f"ledger {r.get('spot_id')} verdict 非法: {v!r}")
            elif v == "unsupported" and not (r.get("evidence_quote") or "").strip():
                fails.append(f"ledger {r.get('spot_id')} unsupported 缺引文主张对照 evidence_quote")
            elif v == "undeterminable" and not (r.get("basis") or "").strip():
                fails.append(f"ledger {r.get('spot_id')} undeterminable 未写缺什么证据")
            elif v in ("fully_supported", "partially_supported") and not (r.get("evidence_quote") or "").strip():
                fails.append(f"ledger {r.get('spot_id')} {v} 缺 evidence_quote")
            elif v == "partially_supported":
                pass
            for k in ("locator", "quote"):
                if not (r.get(k) or "").strip():
                    fails.append(f"ledger {r.get('spot_id')} 缺 {k}（无原文位置引用）")

    cov = res.get("coverage") or {}
    if cov:
        for c in CATEGORIES:
            if c not in cov: fails.append(f"result.coverage 缺类别 {c}")
    cj_path = os.path.join(w, "coverage.json")
    if os.path.exists(cj_path):
        try:
            cj = json.load(open(cj_path, encoding="utf-8"))
            for c in CATEGORIES:
                it = cj.get(c)
                if not it: fails.append(f"coverage.json 缺类别 {c}")
                elif not (it.get("checked") or it.get("na")):
                    fails.append(f"coverage.json {c} 未 checked 且未标 na")
        except Exception as e:
            fails.append(f"coverage.json 无法解析: {e}")

    rr = res.get("review_report") or {}
    if rr.get("findings_total") not in (None, len(findings)):
        fails.append("review_report.findings_total 与 findings.json 不一致")

    if fails:
        print("\n".join("FAIL " + x for x in fails))
        print(f"SUMMARY findings={len(findings)} spots={len(spots)} ledger={len(ledger)} -> NOT PASS")
        sys.exit(1)
    print(f"SUMMARY findings={len(findings)} spots={len(spots)} ledger={len(ledger)} -> ALL PASS")

if __name__ == "__main__":
    main()
