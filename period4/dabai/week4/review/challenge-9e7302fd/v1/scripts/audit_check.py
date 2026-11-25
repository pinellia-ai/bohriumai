#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_check.py — 研究方法与统计审查 result.json / findings 交付验收器。

用法: python3 audit_check.py /app/output/result.json [--workdir /app/output]
验收（全过退出码 0；任一失败退出码 1）:
  1. result.json 顶层字段齐全; status 合法; partial/failed 有界限; case_id 非空
  2. findings 每条八件齐全（含 facet 与 flaw_class）; location.quote 非空
  3. flaw_class ∈ {method_flaw, reporting_gap}; severity ∈ {major, minor, suggestion}
  4. facet ∈ 五面; category ∈ 六类; major 必须写明影响主结论的路径
  5. design_profile.json 每项有 locator 或 not_reported
  6. coverage 五 facet + 六类全出现
"""
import argparse, json, os, sys

FACETS = {"research_design", "variable_definition", "statistical_method",
          "sample_size_power", "results_report"}
CATEGORIES = ["fact_verification", "citation_support", "method_design",
              "statistical_reporting", "argument_chain", "academic_norm"]
FLAW_CLASSES = {"method_flaw", "reporting_gap"}
SEVERITIES = {"major", "minor", "suggestion", "pending_review"}
REQUIRED_TOP = ["case_id", "status", "deliverables", "review_report",
                "evidence_and_boundary", "coverage", "sources", "uncertainty_notes"]
FINDING_FIELDS = ["id", "category", "facet", "location", "flaw_class",
                  "severity", "evidence", "recommendation"]

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
        if f_.get("facet") not in FACETS:
            fails.append(f"finding {fid} facet 非法: {f_.get('facet')!r}")
        if f_.get("category") not in CATEGORIES:
            fails.append(f"finding {fid} category 非法: {f_.get('category')!r}")
        if f_.get("flaw_class") not in FLAW_CLASSES:
            fails.append(f"finding {fid} flaw_class 非法: {f_.get('flaw_class')!r}")
        if f_.get("severity") not in SEVERITIES:
            fails.append(f"finding {fid} severity 非法: {f_.get('severity')!r}")
        loc = f_.get("location") or {}
        for k in ("file", "locator", "quote"):
            if not loc.get(k): fails.append(f"finding {fid} location 缺 {k}")
        if f_.get("severity") == "major" and "影响主结论" not in (f_.get("evidence") or ""):
            fails.append(f"finding {fid} major 未写影响主结论的路径")

    dp_path = os.path.join(w, "design_profile.json")
    if os.path.exists(dp_path):
        try:
            dp = json.load(open(dp_path, encoding="utf-8"))
            if isinstance(dp, dict):
                for k, v in dp.items():
                    if isinstance(v, dict):
                        if not (v.get("locator") or v.get("not_reported") or v.get("na")):
                            fails.append(f"design_profile.{k} 缺 locator 且未标 not_reported")
        except Exception as e:
            fails.append(f"design_profile.json 无法解析: {e}")
    else:
        fails.append("design_profile.json 缺失")

    cov = res.get("coverage") or {}
    need = FACETS | set(CATEGORIES)
    for c in need:
        if c not in cov: fails.append(f"result.coverage 缺 {c}")
    cj_path = os.path.join(w, "coverage.json")
    if os.path.exists(cj_path):
        try:
            cj = json.load(open(cj_path, encoding="utf-8"))
            for c in need:
                it = cj.get(c)
                if not it: fails.append(f"coverage.json 缺 {c}")
                elif not (it.get("checked") or it.get("na")):
                    fails.append(f"coverage.json {c} 未 checked 且未标 na")
        except Exception as e:
            fails.append(f"coverage.json 无法解析: {e}")

    rr = res.get("review_report") or {}
    if rr.get("findings_total") not in (None, len(findings)):
        fails.append("review_report.findings_total 与 findings.json 不一致")

    if fails:
        print("\n".join("FAIL " + x for x in fails))
        print(f"SUMMARY findings={len(findings)} -> NOT PASS")
        sys.exit(1)
    print(f"SUMMARY findings={len(findings)} -> ALL PASS")

if __name__ == "__main__":
    main()
