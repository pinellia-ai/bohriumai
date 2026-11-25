#!/usr/bin/env python3
"""plan_check.py — 实验方案结构与算术校验器（experiment-plan-generator 配套脚本）

用法:
  python3 plan_check.py --plan plan.json [--params params.json] [--constraints constraints.json] [--out report.json]

输入 JSON 结构（与 SKILL.md Step 1-5 产出对应）:
plan.json: {
  "hypotheses_variables": [{"h_id","hypothesis","iv":{...},"dv":{...},"confounders":[...],"source"}],
  "controls": [{"group","purpose","n","cost_per_sample"}],
  "steps": [{"step_id","action","equipment":[...],"reagents":[{"name","spec","qty_per_sample","unit_price"?}...],
             "duration_min","parallelizable","depends_on":[]}],
  "readout_criteria": [...], "risks": [...]
}
params.json: [{"param","unit","value","range":[lo,hi],"basis":{"type","location"}}]
constraints.json(可选，来自案例的有限参数域): {"参数名": {"min":x,"max":y}} 或 {"safety_limits":{...},"device_ranges":{...}}

输出: 校验报告 JSON（checks + arithmetic + PASS/FAIL 汇总），exit code: 0=全部通过, 1=有 FAIL。
只做结构与算术校验，不评科学合理性。
"""
import argparse, json, sys, heapq

FAIL, WARN = [], []


def fail(rule, msg, detail=None):
    FAIL.append({"rule": rule, "msg": msg, "detail": detail})


def warn(rule, msg):
    WARN.append({"rule": rule, "msg": msg})


def check_completeness(plan):
    seven = {
        "hypotheses_variables": "假设与变量", "controls": "对照组",
        "steps": "步骤(设备材料)", "readout_criteria": "判读标准",
        "risks": "风险与异常",
    }
    for key, label in seven.items():
        if not plan.get(key):
            fail("seven_elements", f"要素缺失: {label} 为空", key)
    if not plan.get("steps") and not plan.get("parameters"):
        fail("seven_elements", "步骤与参数均缺失")
    # 每个假设的 iv/dv/confounders
    for h in plan.get("hypotheses_variables") or []:
        for k in ("iv", "dv", "confounders"):
            if not h.get(k):
                fail("hypothesis_fields", f"假设 {h.get('h_id','?')} 缺 {k}")
        iv = h.get("iv") or {}
        if iv and not iv.get("unit"):
            warn("variable_unit", f"假设 {h.get('h_id','?')} 自变量无单位")


def check_controls(plan):
    per_h = {}
    ctrl_types = set()
    for c in plan.get("controls") or []:
        purpose = c.get("purpose") or ""
        per_h.setdefault(c.get("for_hypothesis", "*"), []).append(c)
        if not purpose:
            fail("control_purpose", f"对照 {c.get('group','?')} 无 purpose（须指向具体混杂）")
        g = (c.get("group") or "").lower()
        if any(w in g for w in ("blank", "空白", "基线")):
            ctrl_types.add("blank")
        if any(w in g for w in ("positive", "阳性")):
            ctrl_types.add("positive")
        if any(w in g for w in ("negative", "阴性")):
            ctrl_types.add("negative")
        if any(w in g for w in ("gradient", "剂量", "梯度")):
            ctrl_types.add("gradient")
    n_ctrl = len(plan.get("controls") or [])
    n_hyp = len(plan.get("hypotheses_variables") or [1]) or 1
    if n_ctrl < 2 * max(n_hyp, 1) and n_ctrl < 2:
        fail("control_count", f"对照数 {n_ctrl} < 2，至少空白+阳性/阴性两类")
    elif len(ctrl_types) < 2:
        warn("control_types", f"对照类型仅 {sorted(ctrl_types)}，建议空白+阳性或空白+阴性")
    return per_h


def check_critical_path(steps):
    """关键路径 = 依赖图上最长时长路径；返回 (serial_sum, critical_path) 分钟。"""
    by_id = {s.get("step_id"): s for s in steps}
    serial = sum(float(s.get("duration_min") or 0) for s in steps)
    # 拓扑最长路径
    indeg = {sid: 0 for sid in by_id}
    succ = {sid: [] for sid in by_id}
    for s in steps:
        for d in s.get("depends_on") or []:
            if d in by_id:
                succ[d].append(s.get("step_id"))
                indeg[s.get("step_id")] += 1
    longest = {sid: 0.0 for sid in by_id}
    q = [sid for sid, d in indeg.items() if d == 0]
    order = []
    while q:
        sid = q.pop()
        order.append(sid)
        for t in succ[sid]:
            longest[t] = max(longest[t], longest[sid] + float(by_id[sid].get("duration_min") or 0))
            indeg[t] -= 1
            if indeg[t] == 0:
                q.append(t)
    crit = max((longest[sid] + float(by_id[sid].get("duration_min") or 0) for sid in by_id), default=0.0)
    # 依赖成环检测
    if len(order) != len(steps):
        fail("dependency_cycle", "步骤依赖存在环，无法计算关键路径")
    # 并行步骤同时被计入 serial 与关键路径属正常；若声称全部并行但存在依赖则提示
    return serial, round(crit, 1)


def check_budget(plan):
    """预算 = Σ 耗材 qty×unit_price + Σ 对照成本 + 步骤成本项。缺单价则记 price_missing。"""
    total, missing = 0.0, []
    for st in plan.get("steps") or []:
        for r in st.get("reagents") or []:
            price, qty = r.get("unit_price"), r.get("qty_total") or r.get("qty_per_sample")
            if price is None or qty is None:
                missing.append(f"{st.get('step_id','?')}/{r.get('name','?')}")
            else:
                try:
                    total += float(price) * float(qty)
                except (TypeError, ValueError):
                    missing.append(f"{st.get('step_id','?')}/{r.get('name','?')}(非数值)")
        for c in (st.get("cost_items") or []):
            try:
                total += float(c.get("amount") or 0)
            except (TypeError, ValueError):
                missing.append(f"{st.get('step_id','?')}/cost_item")
    for c in plan.get("controls") or []:
        try:
            total += float(c.get("n") or 0) * float(c.get("cost_per_sample") or 0)
        except (TypeError, ValueError):
            missing.append(f"对照 {c.get('group','?')} 成本")
    if missing:
        warn("price_missing", f"缺单价/数量项（计0处理并需人工补价）: {missing[:10]}")
    return round(total, 2), missing


def check_params(params, constraints):
    ok = True
    for p in params or []:
        name, val = p.get("param"), p.get("value")
        rng = p.get("range") or []
        basis = p.get("basis") or {}
        if not basis.get("type"):
            fail("param_basis", f"参数 {name} 无依据来源(basis.type)", p)
            ok = False
        if not rng or len(rng) != 2:
            fail("param_range", f"参数 {name} 无 [lo,hi] 区间", p)
            ok = False
            continue
        try:
            lo, hi, v = float(rng[0]), float(rng[1]), float(val)
        except (TypeError, ValueError):
            fail("param_numeric", f"参数 {name} 值/区间非数值", p)
            ok = False
            continue
        if not (lo <= v <= hi):
            fail("param_out_of_own_range", f"参数 {name}={v} 超出自身区间 [{lo},{hi}]", p)
            ok = False
        # 对照案例给的有限参数域
        for cname, lim in (constraints or {}).items():
            if cname == name or cname in str(name):
                try:
                    cmin, cmax = float(lim["min"]), float(lim["max"])
                except (KeyError, TypeError, ValueError):
                    continue
                if not (rng[0] >= cmin and rng[1] <= cmax):
                    fail("param_vs_domain", f"参数 {name} 区间[{lo},{hi}] 超出约束域[{cmin},{cmax}]", p)
                    ok = False
        if not p.get("out_of_range_action"):
            warn("param_oor_action", f"参数 {name} 无越界处置")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--params")
    ap.add_argument("--constraints")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    plan = json.load(open(a.plan, encoding="utf-8"))
    params = json.load(open(a.params, encoding="utf-8")) if a.params else plan.get("parameters") or []
    constraints = json.load(open(a.constraints, encoding="utf-8")) if a.constraints else {}

    check_completeness(plan)
    check_controls(plan)
    serial, crit = check_critical_path(plan.get("steps") or [])
    budget, missing = check_budget(plan)
    params_ok = check_params(params, constraints)
    if params and not params_ok:
        pass  # 已记入 FAIL

    report = {
        "summary": {"FAIL": len(FAIL), "WARN": len(WARN), "pass": len(FAIL) == 0},
        "arithmetic": {"serial_total_min": serial, "critical_path_min": crit,
                       "budget_total": budget, "price_missing_count": len(missing)},
        "FAIL": FAIL, "WARN": WARN,
    }
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text)
    print(text)
    sys.exit(0 if len(FAIL) == 0 else 1)


if __name__ == "__main__":
    main()
