#!/usr/bin/env python3
"""feasibility_score.py — 可行性审查量化评分器（experiment-feasibility-review 配套脚本）

用法:
  python3 feasibility_score.py --review review.json [--weights weights.json] [--check-arithmetic plan.json] [--out report.json]

review.json: {"checklist": [{"cat": "...", "item_id": "...", "verdict": "pass|fail|conditional|not_specified|indeterminate|na", "blocking": false}...]}
verdict→分: pass=100, conditional=60, not_specified=40, indeterminate=50, fail=0(blocking fail 类直接0), na 不计入分母。
weights.json(可选): {"假设与变量": 1, "对照组": 1, ...} 缺省等权。
--check-arithmetic plan.json: 步骤时长求和与预算求和复核（steps[].duration_min, reagents[].unit_price*qty_total, controls[].n*cost_per_sample）。

输出: {"per_category": {...}, "overall": x.x, "grade": "...", "blocking": [...], "condition_list": [...]}
exit 0 正常；--check-arithmetic 有缺口时 exit 1。
"""
import argparse, json, sys
from collections import defaultdict

SCORE_MAP = {"pass": 100, "conditional": 60, "not_specified": 40, "indeterminate": 50, "fail": 0}
GRADES = [(80, "可行"), (60, "有条件可行"), (0, "不可行")]


def grade_of(s):
    for th, g in GRADES:
        if s >= th:
            return g
    return "不可行"


def score(review, weights):
    cat_scores, blocking, conditions = {}, [], []
    agg = defaultdict(list)
    for it in review.get("checklist") or []:
        cat = it.get("cat") or "未分类"
        v = it.get("verdict")
        if v == "na":
            continue
        agg[cat].append(SCORE_MAP.get(v, 0))
        if v == "fail":
            entry = {"item_id": it.get("item_id"), "cat": cat}
            if it.get("blocking") or it.get("blocking") is None:
                blocking.append(entry)
        if v == "conditional":
            conditions.append({"item_id": it.get("item_id"), "condition": it.get("needed_action") or it.get("reason")})
        if v == "not_specified":
            conditions.append({"item_id": it.get("item_id"), "condition": "补充方案中缺失的信息: " + str(it.get("check") or "")})
    for cat, scores in agg.items():
        cat_scores[cat] = round(sum(scores) / len(scores), 1)
    if not cat_scores:
        return {"per_category": {}, "overall": 0.0, "grade": "无法判定", "blocking": [], "condition_list": []}
    tot_w = sum(float(weights.get(c, 1)) for c in cat_scores)
    overall = sum(cat_scores[c] * float(weights.get(c, 1)) for c in cat_scores) / tot_w if tot_w else 0.0
    g = grade_of(overall)
    if blocking:
        g = "不可行"
        overall = min(overall, 59.9)
    return {"per_category": cat_scores, "overall": round(overall, 1), "grade": g,
            "blocking": blocking, "condition_list": conditions}


def check_arithmetic(plan):
    total_min = sum(float(s.get("duration_min") or 0) for s in plan.get("steps") or [])
    budget = 0.0
    gaps = []
    for s in plan.get("steps") or []:
        for r in s.get("reagents") or []:
            p, q = r.get("unit_price"), r.get("qty_total")
            if p is None or q is None:
                gaps.append(f"{s.get('step_id')}/{r.get('name')}")
            else:
                budget += float(p) * float(q)
    for c in plan.get("controls") or []:
        try:
            budget += float(c.get("n") or 0) * float(c.get("cost_per_sample") or 0)
        except (TypeError, ValueError):
            gaps.append(f"control/{c.get('group')}")
    return {"total_min": total_min, "budget": round(budget, 2), "price_missing": gaps}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--review", required=True)
    ap.add_argument("--weights")
    ap.add_argument("--check-arithmetic")
    ap.add_argument("--out")
    a = ap.parse_args()
    review = json.load(open(a.review, encoding="utf-8"))
    weights = json.load(open(a.weights, encoding="utf-8")) if a.weights else {}
    rep = score(review, weights)
    exit_code = 0
    if a.check_arithmetic:
        plan = json.load(open(a.check_arithmetic, encoding="utf-8"))
        rep["arithmetic"] = check_arithmetic(plan)
        if rep["arithmetic"]["price_missing"]:
            exit_code = 1
    text = json.dumps(rep, ensure_ascii=False, indent=2)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text)
    print(text)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
