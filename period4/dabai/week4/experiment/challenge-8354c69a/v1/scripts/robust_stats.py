#!/usr/bin/env python3
"""robust_stats.py — 实验数据稳健判读器（result-interpretation-anomaly-analysis 配套脚本）

用法:
  python3 robust_stats.py --data data.csv --roles roles.json [--value-col 读数列] [--group-cols 批次,通道] [--time-col 时间列]
                          [--mode all|baseline|anomalies|trend] [--k 5] [--out report.json]

roles.json: {"columns": [{"name": "OD450", "role": "measure", "unit": "OD"},
                         {"name": "type", "role": "control_flag"},   # 值含 control/ctrl/对照 → 对照行
                         {"name": "batch", "role": "group"},
                         {"name": "time", "role": "time"}]}
mode:
  baseline   — 总体与分组基线: median/MAD/IQR围栏; 对照行(若n>=3)控制限 mean±3sd, 否则 insufficient_replicates
  anomalies  — 三规则并集: |modified_z|>3.5, IQR围栏外, 对照控制限外; 输出对象维度+偏离量+规则+行号
  trend      — 对 time 列按组最小二乘斜率/R², 平台期检测(连续k点斜率绝对值<全段斜率10%)
  all        — 以上全部
不虚构数据: 只读输入文件真实值; 列缺失/重复<3 如实降级。输出 exit 0; 全列缺失 exit 1。
"""
import argparse, csv, json, sys, math


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def col(rows, name):
    return [float(r[name]) for r in rows if r.get(name) not in (None, "", "NA", "NaN")]


def median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def mad(xs, m=None):
    m = median(xs) if m is None else m
    return median([abs(x - m) for x in xs])


def quantile(xs, q):
    s = sorted(xs)
    i = q * (len(s) - 1)
    lo, hi = int(math.floor(i)), int(math.ceil(i))
    return s[lo] if lo == hi else s[lo] + (s[hi] - s[lo]) * (i - lo)


def linfit(ys, ts):
    n = len(ys)
    mt, my = sum(ts) / n, sum(ys) / n
    sxx = sum((t - mt) ** 2 for t in ts)
    if sxx == 0:
        return 0.0, 0.0
    slope = sum((t - mt) * (y - my) for t, y in zip(ts, ys)) / sxx
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (slope * t + (my - slope * mt))) ** 2 for t, y in zip(ts, ys))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return round(slope, 6), round(max(r2, 0.0), 4)


def groupby(rows, gcols):
    g = {}
    for r in rows:
        key = tuple(r.get(c, "") for c in gcols) if gcols else ("*",)
        g.setdefault(key, []).append(r)
    return g


def baseline(rows, vcol, gcols, ctrl_col):
    vals = col(rows, vcol)
    out = {"n": len(vals), "median": None, "mad": None, "iqr_fence": None}
    if vals:
        m, d = median(vals), mad(vals)
        q1, q3 = quantile(vals, .25), quantile(vals, .75)
        out.update({"median": round(m, 6), "mad": round(d, 6),
                    "iqr_fence": [round(q1 - 1.5 * (q3 - q1), 6), round(q3 + 1.5 * (q3 - q1), 6)],
                    "control_limit": None, "control_n": 0, "insufficient_replicates": len(vals) < 3})
        ctrl_rows = [r for r in rows if ctrl_col and str(r.get(ctrl_col, "")).lower() in ("control", "ctrl", "对照", "blank")]
        cv = col(ctrl_rows, vcol)
        out["control_n"] = len(cv)
        if len(cv) >= 3:
            mu = sum(cv) / len(cv)
            sd = math.sqrt(sum((x - mu) ** 2 for x in cv) / (len(cv) - 1)) if len(cv) > 1 else 0
            out["control_limit"] = [round(mu - 3 * sd, 6), round(mu + 3 * sd, 6)]
    groups = {}
    for key, gr in groupby(rows, gcols).items():
        gv = col(gr, vcol)
        if gv:
            groups["|".join(key)] = {"n": len(gv), "median": round(median(gv), 6), "mad": round(mad(gv), 6)}
    out["groups"] = groups
    return out


def anomalies(rows, vcol, gcols, bl, row_ids):
    m, d = bl["median"], bl["mad"] or 0
    res = []
    q1, q3 = bl["iqr_fence"]
    cl = bl.get("control_limit")
    for i, r in enumerate(rows):
        raw = r.get(vcol)
        if raw in (None, "", "NA", "NaN"):
            continue
        v = float(raw)
        mz = 0.6745 * (v - m) / d if d > 0 else 0.0
        rules = []
        if abs(mz) > 3.5:
            rules.append(f"modified_z={round(mz,2)}>3.5")
        if q1 and not (q1 <= v <= q3):
            rules.append("IQR_fence")
        if cl and not (cl[0] <= v <= cl[1]):
            rules.append(f"control_limit 超出{round(min(abs(v - cl[0]), abs(v - cl[1])), 4)}")
        if rules:
            res.append({"object": "|".join(r.get(g, "") for g in gcols) or f"row{i}", "row": row_ids[i] if row_ids else i + 2,
                        "value": v, "modified_z": round(mz, 3), "rules": rules, "iqr_fence": q1})
    return res


def trend(rows, vcol, tcol, gcols, k, ctrl_col=None):
    res = []
    if ctrl_col:
        rows = [r for r in rows if str(r.get(ctrl_col, "")).lower() not in ("control", "ctrl", "对照", "blank")]
    for key, gr in groupby(rows, gcols).items():
        ts, ys = [], []
        for r in gr:
            if r.get(vcol) not in (None, "", "NA", "NaN") and r.get(tcol) not in (None, "", "NA", "NaN"):
                ts.append(float(r[tcol])); ys.append(float(r[vcol]))
        if len(ys) < 3:
            res.append({"group": "|".join(key), "n": len(ys), "note": "insufficient_replicates(<3)"})
            continue
        slope, r2 = linfit(ys, ts)
        # 平台期: 滑窗斜率（窗口时间跨度须>0，否则跳过）
        plateau = None
        full = abs(slope) or 1e-9
        for i in range(len(ys) - k + 1):
            if ts[i + k - 1] <= ts[i]:
                continue
            ws, _ = linfit(ys[i:i + k], ts[i:i + k])
            if abs(ws) < 0.1 * full:
                plateau = {"window": [ts[i], ts[i + k - 1]], "slope": ws}
                break
        res.append({"group": "|".join(key), "n": len(ys), "slope": slope, "r2": r2,
                    "direction": "up" if slope > 0 else "down" if slope < 0 else "flat",
                    "plateau": plateau})
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--roles")
    ap.add_argument("--value-col")
    ap.add_argument("--group-cols", default="")
    ap.add_argument("--time-col")
    ap.add_argument("--mode", default="all", choices=["all", "baseline", "anomalies", "trend"])
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--out")
    a = ap.parse_args()
    rows = read_csv(a.data)
    if not rows:
        print(json.dumps({"error": "no rows"}, ensure_ascii=False)); sys.exit(1)
    roles = json.load(open(a.roles, encoding="utf-8")) if a.roles else {"columns": []}
    role_map = {c["name"]: c.get("role") for c in roles.get("columns", [])}
    vcol = a.value_col or next((n for n, rl in role_map.items() if rl == "measure"), list(rows[0].keys())[0])
    gcols = a.group_cols.split(",") if a.group_cols else [n for n, rl in role_map.items() if rl == "group"]
    tcol = a.time_col or next((n for n, rl in role_map.items() if rl == "time"), None)
    ctrl_col = next((n for n, rl in role_map.items() if rl == "control_flag"), None)
    if vcol not in rows[0]:
        print(json.dumps({"error": f"value column {vcol} not found", "columns": list(rows[0].keys())}, ensure_ascii=False)); sys.exit(1)
    row_ids = [r.get("_row_id") for r in rows]
    rep = {"value_column": vcol, "group_columns": gcols, "n_rows": len(rows)}
    if a.mode in ("baseline", "all"):
        rep["baseline"] = baseline(rows, vcol, gcols, ctrl_col)
    if a.mode in ("anomalies", "all"):
        rep["anomalies"] = anomalies(rows, vcol, gcols, rep.get("baseline") or baseline(rows, vcol, gcols, ctrl_col), row_ids)
    if a.mode in ("trend", "all") and tcol:
        rep["trend"] = trend(rows, vcol, tcol, gcols, a.k, ctrl_col)
    text = json.dumps(rep, ensure_ascii=False, indent=2)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text)
    print(text)


if __name__ == "__main__":
    main()
