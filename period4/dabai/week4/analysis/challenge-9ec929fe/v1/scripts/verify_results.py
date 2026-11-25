#!/usr/bin/env python3
"""verify_results.py — 静默错误检测：行数对照 + 数值复算 + AST 模式扫描。
用法: verify_results.py <run_json> <raw_csv> <result_json>
"""
import ast, csv, json, statistics as st, sys

SILENT_PATTERNS = [
    ("missing_as_zero_risk", lambda tree, src: any(
        isinstance(n, ast.Call) and getattr(n.func, "id", getattr(n.func, "attr", "")) in ("mean", "sum", "fmean")
        for n in ast.walk(tree)) and ("dropna" not in src and "isna" not in src and "isnull" not in src
                                      and "parse_num" not in src and "float(" not in src)),
    ("no_dedup_before_groupby", lambda tree, src: "groupby" in src and "drop_duplicates" not in src and "dedup" not in src),
    ("test_without_assumption_check", lambda tree, src: (
        "ttest" in src or "t_test" in src) and not any(k in src for k in ("shapiro", "normality", "jarque", "normaltest"))),
    ("hardcoded_abs_path", lambda tree, src: bool(any(
        isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.startswith("/")
        for n in ast.walk(tree)) and "/app/" in src and "argv" not in src)),
]

def main(run_p, raw_p, result_p):
    rec = json.load(open(run_p, encoding="utf-8"))
    probs = []
    if rec.get("exit_code") != 0:
        probs.append(f"执行未成功: exit={rec.get('exit_code')}")
    res = json.load(open(result_p, encoding="utf-8")) if result_p not in ("-", "") else {}
    rows = list(csv.DictReader(open(raw_p, encoding="utf-8-sig")))
    n_raw = len(rows)
    n_res = res.get("n_rows")
    if n_res is not None and n_res > n_raw:
        probs.append(f"result 行数 {n_res} > 原始 {n_raw}（行数膨胀）")
    # 数值复算：result.json 若含 mean_<col> 字段则直算比对
    recomp = []
    for k, v in (res.get("means") or {}).items():
        vals = []
        for r in rows:
            try: vals.append(float(r[k]))
            except (ValueError, KeyError, TypeError): pass
        if vals:
            m = st.fmean(vals)
            ok = abs(m - float(v)) < 1e-6
            recomp.append({"col": k, "reported": v, "recomputed": round(m, 6), "match": ok})
            if not ok: probs.append(f"复算不一致: {k} 报 {v} vs 实 {m:.4f}")
    # AST 静默扫描（analysis.py 由 run cmd 提取）
    src_path = None
    for tok in rec.get("cmd", "").split():
        if tok.endswith(".py") and "scripts" not in tok:
            src_path = tok
    scan = {}
    if src_path:
        try:
            src = open(src_path, encoding="utf-8").read()
            tree = ast.parse(src)
            for name, fn in SILENT_PATTERNS:
                hit = fn(tree, src)
                scan[name] = "WARN" if hit else "pass"
                if hit: probs.append(f"静默错误模式: {name} ({src_path})")
        except Exception as e:
            probs.append(f"AST 扫描失败: {e}")
    out = {"pass": not probs, "n_raw": n_raw, "recompute": recomp, "silent_scan": scan, "problems": probs}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(0 if out["pass"] else 1)

if __name__ == "__main__":
    main(*sys.argv[1:4])
