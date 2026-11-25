#!/usr/bin/env python3
"""param_optimizer.py — 约束感知参数搜索器（bounded-parameter-optimizer 配套脚本）

用法:
  python3 param_optimizer.py --domain domain.json --objective objective.json [--mode search|feasible|verify] [--out result.json] [--max-grid 20000]

domain.json: {"parameters": [{"name","unit","min","max","step","source":{...}}],
              "constraints": [{"type":"material|device|safety","expr":"温度<=80","source":"..."}]}  # expr 形如 "参数名<=值" 或 "参数名>=值"
objective.json: {"response":"产率","direction":"max|min",
                 "model":{"type":"linear","coefs":{"参数名":coef,...},"intercept":c}}   # 预测: intercept+Σcoef*param
mode:
  feasible  — 计算每个参数可行区间（自身区间∩约束）
  search    — 可行域内网格搜索（>max-grid 自动分阶段：先粗步长后局部加密），保留 search_log 与停止判据
  verify    — 校验指定参数组合是否在可行域内（--check '{"温度":70}'）
输出: JSON（feasible_ranges / candidates / search_log / stop_reason / conflicts），exit 0；可行域为空 exit 1。
"""
import argparse, json, sys
from itertools import product

OPS = {"<=": lambda a, b: a <= b, ">=": lambda a, b: a >= b, "<": lambda a, b: a < b, ">": lambda a, b: a > b}


def parse_constraint(expr):
    # "温度<=80"
    for op in ("<=", ">=", "<", ">"):
        if op in expr:
            name, val = expr.split(op)
            return name.strip(), op, float(val)
    return None, None, None


def feasible_ranges(params, constraints):
    ranges, conflicts = {}, []
    for p in params:
        lo, hi = float(p["min"]), float(p["max"])
        cut_by = []
        for c in constraints or []:
            n, op, val = parse_constraint(c.get("expr", ""))
            if n and (n == p["name"] or n in p["name"]):
                if op in ("<=", "<") and lo > val:
                    conflicts.append({"param": p["name"], "expr": c["expr"], "reason": "下限已违反约束"})
                elif op in (">=", ">") and hi < val:
                    conflicts.append({"param": p["name"], "expr": c["expr"], "reason": "上限已违反约束"})
                else:
                    if op in ("<=", "<"):
                        hi = min(hi, val if op == "<=" else val)  # 保守取等
                        cut_by.append(c["expr"])
                    else:
                        lo = max(lo, val)
                        cut_by.append(c["expr"])
        ranges[p["name"]] = {"feasible": [lo, hi] if lo <= hi else None,
                             "original": [float(p["min"]), float(p["max"])], "cut_by": cut_by,
                             "unit": p.get("unit"), "step": p.get("step")}
        if lo > hi:
            conflicts.append({"param": p["name"], "expr": "区间交集为空", "reason": f"[{lo},{hi}]"})
    return ranges, conflicts


def predict(model, point):
    v = float(model.get("intercept") or 0)
    for k, c in (model.get("coefs") or {}).items():
        key = next((pk for pk in point if pk == k or k in pk), None)
        if key is not None:
            v += float(c) * float(point[key])
    return round(v, 4)


def grid_points(ranges, params, max_grid):
    axes, steps = [], []
    for p in params:
        r = ranges[p["name"]]
        if not r["feasible"]:
            return []
        lo, hi = r["feasible"]
        st = float(r.get("step") or (hi - lo) / 10 or 1) or 1.0
        n = int((hi - lo) / st) + 1
        axes.append([lo + i * st for i in range(n)])
        steps.append(p["name"])
    total = 1
    for a in axes:
        total *= max(len(a), 1)
    if total > max_grid:
        return None  # 触发分阶段
    return [dict(zip(steps, pts)) for pts in product(*axes)]


def staged_search(ranges, params, model, direction, max_grid):
    log = []
    # 第一轮：粗步长（区间/5）
    coarse = {}
    for p in params:
        r = ranges[p["name"]]
        lo, hi = r["feasible"]
        coarse[p["name"]] = r
        r["step"] = max((hi - lo) / 5, 1e-9)
    pts = grid_points(ranges, params, max_grid)
    scored = [(predict(model, pt), pt) for pt in pts]
    log.append({"round": 1, "stage": "coarse", "n_points": len(scored)})
    best = max(scored) if direction == "max" else min(scored)
    # 第二轮：最优邻域加密（步长/10）
    for p in params:
        r = ranges[p["name"]]
        b = best[1][p["name"]]
        span = (r["feasible"][1] - r["feasible"][0]) / 5
        r["feasible"] = [max(r["feasible"][0], b - span), min(r["feasible"][1], b + span)]
        r["step"] = max(span / 5, 1e-9)
    pts2 = grid_points(ranges, params, max_grid)
    scored2 = [(predict(model, pt), pt) for pt in (pts2 or [])]
    log.append({"round": 2, "stage": "local_refine", "n_points": len(scored2)})
    if scored2:
        best2 = max(scored2) if direction == "max" else min(scored2)
        improvement = abs(best2[0] - best[0]) / max(abs(best[0]), 1e-9)
        stop = "local_refine_improvement<1%" if improvement < 0.01 else "refine_exhausted"
        best = best2 if ((direction == "max" and best2[0] >= best[0]) or (direction == "min" and best2[0] <= best[0])) else best
    else:
        stop = "refine_empty"
    return best, scored + scored2, log, stop


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", required=True)
    ap.add_argument("--objective")
    ap.add_argument("--mode", default="search", choices=["search", "feasible", "verify"])
    ap.add_argument("--check")
    ap.add_argument("--max-grid", type=int, default=20000)
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--out")
    a = ap.parse_args()
    domain = json.load(open(a.domain, encoding="utf-8"))
    params = domain.get("parameters") or []
    constraints = domain.get("constraints") or []

    ranges, conflicts = feasible_ranges(params, constraints)
    if a.mode == "feasible":
        rep = {"feasible_ranges": ranges, "conflicts": conflicts}
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        sys.exit(1 if conflicts else 0)

    if a.mode == "verify":
        point = json.loads(a.check or "{}")
        ok = True
        for p in params:
            r = ranges[p["name"]]
            v = next((pv for pk, pv in point.items() if pk == p["name"] or p["name"] in pk), None)
            if v is None or not r["feasible"] or not (r["feasible"][0] <= v <= r["feasible"][1]):
                ok = False
        print(json.dumps({"verify": ok, "feasible_ranges": ranges}, ensure_ascii=False, indent=2))
        sys.exit(0 if ok else 1)

    # search
    obj = json.load(open(a.objective, encoding="utf-8")) if a.objective else {}
    model = obj.get("model") or {"type": "linear", "coefs": {}, "intercept": 0}
    direction = obj.get("direction", "max")
    if conflicts:
        print(json.dumps({"conflicts": conflicts, "stop_reason": "infeasible_domain"}, ensure_ascii=False, indent=2))
        sys.exit(1)
    pts = grid_points(ranges, params, a.max_grid)
    if pts is None:
        best, allscored, log, stop = staged_search(ranges, params, model, direction, a.max_grid)
    elif not pts:
        print(json.dumps({"conflicts": conflicts, "stop_reason": "empty_grid"}, ensure_ascii=False, indent=2))
        sys.exit(1)
    else:
        allscored = [(predict(model, pt), pt) for pt in pts]
        best = max(allscored) if direction == "max" else min(allscored)
        log = [{"round": 1, "stage": "full_grid", "n_points": len(allscored)}]
        stop = "grid_exhausted"
    ranked = sorted(allscored, key=lambda x: x[0], reverse=(direction == "max"))
    rep = {
        "feasible_ranges": {k: v["feasible"] for k, v in ranges.items()},
        "objective": {"response": obj.get("response"), "direction": direction, "model_type": model.get("type")},
        "best": {"predicted_response": best[0], "params": best[1]},
        "top_candidates": [{"predicted_response": s, "params": p} for s, p in ranked[: a.top]],
        "search_log": log,
        "stop_reason": stop,
        "conflicts": conflicts,
    }
    if a.out:
        open(a.out, "w", encoding="utf-8").write(json.dumps(rep, ensure_ascii=False, indent=2))
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
