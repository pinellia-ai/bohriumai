#!/usr/bin/env python3
"""compare_plans.py — 方案比较加权评分与敏感性分析（plan-comparison-selector 配套脚本）

用法:
  python3 compare_plans.py --matrix matrix.json [--out report.json]

matrix.json: {
  "criteria": [{"name": "成本", "weight": 0.3, "direction": "min", "type": "numeric",
                "hard_cap": 5000},                       # numeric: 原始值归一化
               {"name": "证据强度", "weight": 0.25, "type": "anchor"}],  # anchor: 0-3锚点分→归一化
  "plans": [{"plan_id": "A", "values": {"成本": 320, "证据强度": 2}, "hard_fail": []},
            {"plan_id": "B", "values": {"成本": 1150, "证据强度": 3}, "hard_fail": ["HC1:超时间窗3天"]}]
}
规则:
- hard_fail 非空 → 直接淘汰，不计分。
- numeric 归一化: min→1, max→0（direction=min）；direction=max 反之。锚点分 value/3。
- 加权总分 0-100；敏感性: 每维权重±20%（其余等比缩放）重算排序，输出翻转点。

输出: {"ranking": [...], "weighted_totals": {...}, "sensitivity": [...], "eliminated": [...]}
"""
import argparse, json, sys


def normalize(plans, criteria):
    """返回 {plan_id: {criterion: norm_score(0-1)}}"""
    scores = {}
    for c in criteria:
        name, typ = c["name"], c.get("type", "numeric")
        vals = {}
        for p in plans:
            if p.get("hard_fail"):
                continue
            v = (p.get("values") or {}).get(name)
            if v is not None:
                vals[p["plan_id"]] = v
        if not vals:
            continue
        for pid, v in vals.items():
            if typ == "anchor":
                scores.setdefault(pid, {})[name] = min(max(float(v), 0), 3) / 3.0
            else:
                xs = list(vals.values())
                lo, hi = min(xs), max(xs)
                if hi == lo:
                    s = 1.0
                elif c.get("direction", "min") == "min":
                    s = (hi - v) / (hi - lo)
                else:
                    s = (v - lo) / (hi - lo)
                scores.setdefault(pid, {})[name] = s
    return scores


def weighted_total(scores, weights):
    tot = sum(weights.values()) or 1
    return round(100 * sum(scores.get(k, 0) * w for k, w in weights.items()) / tot, 2)


def rank_of(totals):
    return sorted(totals.items(), key=lambda x: -x[1])


def sensitivity(plans, criteria, base_weights):
    out = []
    for c in criteria:
        name = c["name"]
        w0 = base_weights[name]
        for factor, label in ((1.2, "+20%"), (0.8, "-20%")):
            ws = {}
            others = [x["name"] for x in criteria if x["name"] != name]
            rest = 1 - w0 * factor if w0 * factor <= 1 else 0
            rs = sum(base_weights[o] for o in others) or 1
            for x in criteria:
                ws[x["name"]] = w0 * factor if x["name"] == name else rest * base_weights[x["name"]] / rs
            sc = normalize(plans, criteria)
            totals = {pid: weighted_total(s, ws) for pid, s in sc.items()}
            r = rank_of(totals)
            out.append({"dimension": name, "scenario": label, "ranking": r,
                        "flip": bool(base_rank and r and r[0][0] != base_rank[0][0])})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    data = json.load(open(a.matrix, encoding="utf-8"))
    criteria = data.get("criteria") or []
    plans = data.get("plans") or []
    base_weights = {c["name"]: float(c.get("weight", 1)) for c in criteria}

    eliminated = [{"plan_id": p["plan_id"], "reason": "; ".join(p.get("hard_fail") or [])}
                  for p in plans if p.get("hard_fail")]
    live = [p for p in plans if not p.get("hard_fail")]
    sc = normalize(plans, criteria)
    totals = {pid: weighted_total(s, base_weights) for pid, s in sc.items()}
    global base_rank
    base_rank = rank_of(totals)

    margin = round(base_rank[0][1] - base_rank[1][1], 2) if len(base_rank) > 1 else None
    rep = {
        "ranking": base_rank,
        "weighted_totals": totals,
        "per_criterion_normalized": sc,
        "margin_top2": margin,
        "conditional_required": margin is not None and margin < 5,
        "eliminated": eliminated,
        "sensitivity": sensitivity(plans, criteria, base_weights),
        "weights": base_weights,
    }
    text = json.dumps(rep, ensure_ascii=False, indent=2)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text)
    print(text)


if __name__ == "__main__":
    main()
