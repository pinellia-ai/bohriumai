#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_check.py — 论文质量审查 result.json / findings 交付验收器。

用法: python3 audit_check.py /app/output/result.json [--workdir /app/output]
验收项（全部通过退出码 0，任一失败退出码 1 并逐条打印 FAIL）:
  1. result.json 顶层必备字段: case_id/status/deliverables/review_report/evidence_and_boundary/coverage/sources/uncertainty_notes
  2. status 合法; partial/failed 必须给出界限说明
  3. findings.json 每条七件齐全: id/category/location{file,locator,quote}/issue_type/severity/evidence/recommendation
  4. issue_type ∈ {fact_error, insufficient_evidence, norm_issue, suggestion, pending_review}
  5. category ∈ 六类; coverage.json 六类键齐全且 checked=true 或 na=true
  6. 数字门槛: findings 与 coverage 计数一致
"""
import argparse, csv, json, os, sys

CATEGORIES = ["fact_verification", "citation_support", "method_design",
              "statistical_reporting", "argument_chain", "academic_norm"]
ISSUE_TYPES = {"fact_error", "insufficient_evidence", "norm_issue", "suggestion", "pending_review"}
REQUIRED_TOP = ["case_id", "status", "deliverables", "review_report",
                "evidence_and_boundary", "coverage", "sources", "uncertainty_notes"]
FINDING_FIELDS = ["id", "category", "location", "issue_type", "severity", "evidence", "recommendation"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("result_json")
    ap.add_argument("--workdir", default=None)
    a = ap.parse_args()
    workdir = a.workdir or os.path.dirname(os.path.abspath(a.result_json))
    fails = []

    try:
        res = json.load(open(a.result_json, encoding="utf-8"))
    except Exception as e:
        print(f"FAIL result.json 无法解析: {e}"); sys.exit(1)

    for k in REQUIRED_TOP:
        if k not in res:
            fails.append(f"result.json 缺顶层字段 {k}")
    if res.get("status") not in ("success", "partial", "failed"):
        fails.append(f"status 非法: {res.get('status')!r}")
    if res.get("status") in ("partial", "failed"):
        bounds = res.get("evidence_and_boundary", {})
        if not (bounds.get("unchecked") or bounds.get("pending_review") or res.get("failure_reason")):
            fails.append("partial/failed 未说明界限（unchecked/pending_review/failure_reason 全空）")
    if not res.get("case_id"):
        fails.append("case_id 为空（必须从 case.json 原样读取）")

    fpath = os.path.join(workdir, "findings.json")
    findings = []
    if os.path.exists(fpath):
        try:
            findings = json.load(open(fpath, encoding="utf-8"))
        except Exception as e:
            fails.append(f"findings.json 无法解析: {e}")
    for f_ in findings:
        fid = f_.get("id", "?")
        for k in FINDING_FIELDS:
            if k not in f_ or f_[k] in (None, "", {}):
                fails.append(f"finding {fid} 缺字段 {k}")
        if f_.get("issue_type") not in ISSUE_TYPES:
            fails.append(f"finding {fid} issue_type 非法: {f_.get('issue_type')!r}")
        if f_.get("category") not in CATEGORIES:
            fails.append(f"finding {fid} category 非法: {f_.get('category')!r}")
        loc = f_.get("location") or {}
        for k in ("file", "locator", "quote"):
            if not loc.get(k):
                fails.append(f"finding {fid} location 缺 {k}（无引用=零分风险）")
        if f_.get("issue_type") == "pending_review" and not f_.get("evidence", "").strip():
            fails.append(f"finding {fid} pending_review 未写缺什么证据")

    cov = res.get("coverage") or {}
    if isinstance(cov, dict) and cov and "fact_verification" in cov:
        for c in CATEGORIES:
            if c not in cov:
                fails.append(f"coverage 缺类别 {c}")
    cpath = os.path.join(workdir, "coverage.json")
    if os.path.exists(cpath):
        try:
            cj = json.load(open(cpath, encoding="utf-8"))
            for c in CATEGORIES:
                item = cj.get(c)
                if not item:
                    fails.append(f"coverage.json 缺类别 {c}")
                elif not (item.get("checked") or item.get("na")):
                    fails.append(f"coverage.json {c} 既未 checked 也未标 na")
        except Exception as e:
            fails.append(f"coverage.json 无法解析: {e}")

    n = len(findings)
    by_sev = {}
    for f_ in findings:
        by_sev[f_.get("issue_type", "?")] = by_sev.get(f_.get("issue_type", "?"), 0) + 1
    rr = res.get("review_report") or {}
    if rr.get("findings_total") not in (None, n):
        fails.append(f"review_report.findings_total={rr.get('findings_total')} 与 findings.json 实际 {n} 不一致")

    if fails:
        print("\n".join("FAIL " + x for x in fails))
        print(f"SUMMARY findings={n} by_type={by_sev} -> NOT PASS")
        sys.exit(1)
    print(f"SUMMARY findings={n} by_type={by_sev} -> ALL PASS")

if __name__ == "__main__":
    main()
