#!/usr/bin/env python3
"""tolerance_check.py — 复现指标 vs 论文指标的容差对比（da62e8d4 用）。

用法:
  python3 tolerance_check.py --spec compare-spec.json
  python3 tolerance_check.py --selftest

compare-spec 格式:
  {"comparisons": [
     {"metric": "rmse", "reproduced": 0.412, "reported": "0.41",
      "source": "Table 2, p05",
      "tolerance": {"type": "relative", "value": 0.05, "declared_at": "task.md §tolerance"}}]}

判定:
  - tolerance 缺失或无 declared_at → unverifiable（禁止事后定容差）
  - relative: |rep-reported|/|reported| <= tol → within_tolerance
  - absolute: |rep-reported| <= tol → within_tolerance
"""
import argparse, json, re, sys


def parse_num(s):
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    m = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", str(s))
    return float(m.group()) if m else None


def check(item):
    out = {"metric": item.get("metric"), "source": item.get("source")}
    rep = parse_num(item.get("reported"))
    prod = item.get("reproduced")
    tol = item.get("tolerance") or {}
    if prod is None or rep is None:
        out["verdict"] = "unverifiable"
        out["reason"] = "reproduced/reported 缺失或无法解析"
        return out
    if tol.get("value") is None or not tol.get("declared_at"):
        out["verdict"] = "unverifiable"
        out["reason"] = "事前容差未声明或缺 declared_at（禁止事后定容差）"
        out["deviation"] = abs(prod - rep)
        return out
    t = float(tol["value"])
    if tol.get("type") == "absolute":
        dev = abs(prod - rep)
        out["deviation"] = f"{dev:.6g} (abs)"
        ok = dev <= t
    else:  # relative 默认
        if rep == 0:
            out["verdict"] = "unverifiable"
            out["reason"] = "reported 为 0，相对容差不可用"
            return out
        dev = abs(prod - rep) / abs(rep)
        out["deviation"] = f"{dev:.2%}"
        ok = dev <= t
    out["verdict"] = "within_tolerance" if ok else "out_of_tolerance"
    return out


def selftest():
    spec = {"comparisons": [
        {"metric": "rmse", "reproduced": 0.412, "reported": "0.41",
         "source": "Table 2, p05", "tolerance": {"type": "relative", "value": 0.05,
                                                 "declared_at": "task.md §tolerance"}},
        {"metric": "r2", "reproduced": 0.87, "reported": "0.95",
         "source": "Table 2, p05", "tolerance": {"type": "relative", "value": 0.05,
                                                 "declared_at": "task.md §tolerance"}},
        {"metric": "mae", "reproduced": 0.31, "reported": "0.30", "source": "p06",
         "tolerance": None},
        {"metric": "bias", "reproduced": 0.02, "reported": "0.00", "source": "p06",
         "tolerance": {"type": "relative", "value": 0.05, "declared_at": "task.md"}}]}
    results = [check(i) for i in spec["comparisons"]]
    for r in results:
        print(json.dumps(r, ensure_ascii=False))
    ok = (results[0]["verdict"] == "within_tolerance"
          and results[1]["verdict"] == "out_of_tolerance"
          and results[2]["verdict"] == "unverifiable"
          and results[3]["verdict"] == "unverifiable")
    print("selftest:", "PASS" if ok else "FAIL")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec"); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if not a.spec:
        ap.error("--spec 必填（或用 --selftest）")
    with open(a.spec, encoding="utf-8") as f:
        spec = json.load(f)
    outs = [check(i) for i in spec.get("comparisons", [])]
    print(json.dumps(outs, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
