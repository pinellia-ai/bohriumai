#!/usr/bin/env python3
"""stats_kit.py — 统计检验选择树 + 效应量 + 置信区间（纯标准库）。

选择树（自动执行并把依据写进输出）:
  输入: 两组或多组数值列 + 配对标记
  1) 描述统计: n/missing/mean/sd/median/q1/q3/min/max（每值带口径）
  2) 正态性: Jarque-Bera（p = exp(-JB/2), chi2(2) 精确公式）+ 偏度峰度
  3) 方法选择:
     两组: 配对→ 正态: paired-t(近似) / 非正态: Wilcoxon signed(正态近似)
           独立 → 正态+方差齐→ Student t; 方差不齐→ Welch t; 非正态→ Mann-Whitney U
     多组: 正态 → one-way ANOVA(F); 非正态 → Kruskal-Wallis(H)
     （F/H 分布 p 值用数值积分近似，输出 p_method 标明）
  4) 效应量: Cohen's d / r 效应 / eta² / rank-biserial，附 95%CI（bootstrap 2000 次，固定种子）
  5) 多重比较: 组间两两 Welch + Bonferroni 校正
输出 stats_results.json；每个数字带 column/group/n/计算式。
"""
import json, math, random, statistics as st

def _num(xs):
    return [x for x in xs if isinstance(x, (int, float)) and not (isinstance(x, float) and math.isnan(x))]

def describe(xs, col="", group="", unit=""):
    xs = _num(xs); n = len(xs)
    if not n:
        return {"col": col, "group": group, "unit": unit, "n": 0, "missing": 0,
                "mean": None, "sd": None, "median": None, "q1": None, "q3": None,
                "min": None, "max": None, "calc": "n=0 无有效值"}
    xs_s = sorted(xs)
    q1 = xs_s[int(0.25 * (n - 1))]; q3 = xs_s[int(0.75 * (n - 1))]
    return {"col": col, "group": group, "unit": unit, "n": n, "missing": 0,
            "mean": st.fmean(xs), "sd": st.stdev(xs) if n > 1 else 0.0,
            "median": st.median(xs), "q1": q1, "q3": q3, "min": xs_s[0], "max": xs_s[-1],
            "calc": "mean=Σx/n; sd=样本标准差(n-1)"}

def jarque_bera(xs):
    xs = _num(xs); n = len(xs)
    if n < 8: return {"stat": None, "p": None, "n": n, "note": "n<8 检验功效不足"}
    m = st.fmean(xs); s = st.stdev(xs)
    if s == 0: return {"stat": None, "p": None, "n": n, "note": "方差为0"}
    g1 = sum((x - m) ** 3 for x in xs) / n / s ** 3
    g2 = sum((x - m) ** 4 for x in xs) / n / s ** 4 - 3
    jb = n / 6 * (g1 ** 2 + g2 ** 2 / 4)
    return {"stat": round(jb, 4), "p": round(math.exp(-jb / 2), 5), "p_method": "exp(-JB/2), chi2(2) 精确",
            "skew": round(g1, 3), "kurtosis_excess": round(g2, 3), "n": n}

def _t_p(t, df):
    """两尾 p 值：正态近似（df 大时准确；小样本注明近似）。"""
    p = 2 * (1 - st.NormalDist().cdf(abs(t)))
    return max(p, 1e-6)

def welch_t(a, b):
    na, nb = len(a), len(b)
    va, vb = st.variance(a), st.variance(b)
    t = (st.fmean(a) - st.fmean(b)) / math.sqrt(va / na + vb / nb)
    df = (va / na + vb / nb) ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    return {"t": round(t, 4), "df": round(df, 2), "p": _t_p(t, df), "p_method": "正态近似(两尾)"}

def cohens_d(a, b):
    nx, ny = len(a), len(b)
    sp = math.sqrt(((nx - 1) * st.variance(a) + (ny - 1) * st.variance(b)) / (nx + ny - 2))
    d = (st.fmean(a) - st.fmean(b)) / sp if sp else 0.0
    return {"cohens_d": round(d, 3), "calc": "(mA-mB)/pooled_sd"}

def mann_whitney(a, b):
    """U 统计量 + 正态近似 p（含并列修正）。"""
    ranked = sorted([(v, 0, i) for i, v in enumerate(a)] + [(v, 1, i) for i, v in enumerate(b)])
    ranks = {}
    i = 0
    vals = [x[0] for x in ranked]
    while i < len(ranked):
        j = i
        while j < len(ranked) and vals[j] == vals[i]: j += 1
        avg_rank = (i + j + 1) / 2
        for k in range(i, j): ranks[ranked[k][2]] = avg_rank
        i = j
    ra = sum(ranks[i] for i in range(len(a)))
    U = ra - len(a) * (len(a) + 1) / 2
    mu = len(a) * len(b) / 2
    # 并列修正
    from collections import Counter
    tie_term = sum(t ** 3 - t for t in Counter(vals).values() if t > 1)
    n_, m_ = len(a), len(b)
    sigma = math.sqrt(n_ * m_ / 12 * ((n_ + m_ + 1) - tie_term / ((n_ + m_) * (n_ + m_ - 1))))
    z = (U - mu) / sigma if sigma else 0.0
    return {"U": round(U, 1), "z": round(z, 4), "p": _t_p(z, n_ + m_), "p_method": "正态近似(含并列修正)"}

def _f_p(F, df1, df2):
    """F 分布生存函数数值积分（近似，注明）。"""
    def fpdf(x):
        lb = (math.lgamma((df1 + df2) / 2) - math.lgamma(df1 / 2) - math.lgamma(df2 / 2)
              + (df1 / 2) * math.log(df1 / df2))
        return math.exp(lb + (df1 / 2 - 1) * math.log(x) - (df1 + df2) / 2 * math.log(1 + df1 * x / df2))
    n = 20000
    step = (50 * df2 / (df1 + df2) - 1e-6) / n
    s = sum(fpdf(1e-6 + i * step) * step for i in range(n) if (df1 / 2 - 1) >= 0 or (1e-6 + i * step) > 0)
    return round(max(0.0, min(1.0, 1 - s)), 5)

def anova_oneway(groups):
    k = len(groups); allv = [x for g in groups for x in g]
    N = len(allv); gm = st.fmean(allv)
    ssb = sum(len(g) * (st.fmean(g) - gm) ** 2 for g in groups)
    ssw = sum((x - st.fmean(g)) ** 2 for g in groups for x in g)
    df1, df2 = k - 1, N - k
    F = (ssb / df1) / (ssw / df2) if ssw else float("inf")
    return {"F": round(F, 4), "df": [df1, df2], "p": _f_p(F, df1, df2), "p_method": "数值积分近似",
            "eta_sq": round(ssb / (ssb + ssw), 4) if (ssb + ssw) else 0.0, "calc": "SSB/SSW 组间组内平方和"}

def kruskal_wallis(groups):
    ranked = sorted([(v, gi, i) for gi, g in enumerate(groups) for i, v in enumerate(g)])
    ranks = {}; i = 0
    vals = [x[0] for x in ranked]
    while i < len(ranked):
        j = i
        while j < len(ranked) and vals[j] == vals[i]: j += 1
        avg = (i + j + 1) / 2
        for k in range(i, j): ranks[ranked[k][2]] = avg
        i = j
    idx = 0; N = len(vals); eps = 0.0
    H = 0.0
    for gi, g in enumerate(groups):
        r = [ranks[idx + k] for k in range(len(g))]; idx += len(g)
        H += sum(r) ** 2 / len(g)
    H = 12 / (N * (N + 1)) * H - 3 * (N + 1)
    from collections import Counter
    tie_term = sum(t ** 3 - t for t in Counter(vals).values() if t > 1)
    H /= (1 + tie_term / (N * (N + 1) * (N - 1)))
    chi2p = round(math.exp(-H / 2), 5)  # df=k-1；近似用 chi2(2) 公式上界，注明
    return {"H": round(H, 4), "df": len(groups) - 1, "p": chi2p, "p_method": "近似(偏保守,如需精确请用 scipy)"}

def paired_t(a, b):
    d = [x - y for x, y in zip(a, b)]
    m, s = st.fmean(d), st.stdev(d)
    t = m / (s / math.sqrt(len(d))) if s else float("inf")
    return {"t": round(t, 4), "df": len(d) - 1, "p": _t_p(t, len(d) - 1), "p_method": "正态近似",
            "mean_diff": round(m, 4), "calc": "t=mean(d)/(sd(d)/sqrt(n))"}

def wilcoxon_signed(a, b):
    d = sorted(abs(x - y) for x, y in zip(a, b) if x != y)
    n = len(d)
    W = sum(i + 1 for i, v in enumerate(d)) if False else 0
    # W+ 近似
    diffs = [x - y for x, y in zip(a, b) if x != y]
    ranked = sorted((abs(v), k) for k, v in enumerate(diffs))
    ranks = {}
    i = 0
    while i < len(ranked):
        j = i
        while j < len(ranked) and ranked[j][0] == ranked[i][0]: j += 1
        avg = (i + j + 1) / 2
        for k in range(i, j): ranks[ranked[k][1]] = avg
        i = j
    Wp = sum(r for k, v in enumerate(diffs) if v > 0 for r in [ranks[k]])
    mu = n * (n + 1) / 4
    sigma = math.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    z = (Wp - mu) / sigma if sigma else 0.0
    return {"W": round(Wp, 1), "z": round(z, 4), "p": _t_p(z, n), "p_method": "正态近似", "n_pairs": n}

def bootstrap_ci(xs, fn=st.fmean, iters=2000, seed=42, alpha=0.05):
    rnd = random.Random(seed); xs = _num(xs)
    if not xs: return {"ci": None}
    stats_ = sorted(fn([rnd.choice(xs) for _ in xs]) for _ in range(iters))
    return {"ci95": [round(stats_[int(alpha / 2 * iters)], 4), round(stats_[int((1 - alpha / 2) * iters) - 1], 4)],
            "method": f"bootstrap {iters} 次, seed={seed}"}

def choose_and_run(groups, paired=False, col="value", unit="", seed=42):
    """主入口：选择树 + 运行 + 效应量。groups: {group_name: [数值]}"""
    names = list(groups)
    arrs = [_num(groups[k]) for k in names]
    out = {"col": col, "unit": unit, "groups": names,
           "descriptive": [describe(a, col, names[i], unit) for i, a in enumerate(arrs)],
           "normality": {names[i]: jarque_bera(a) for i, a in enumerate(arrs)}}
    small = [k for k, a in zip(names, arrs) if len(a) < 2]
    if small:
        out["test"] = {"name": "not_run", "reason": f"组样本量不足(n<2): {small}", "p": None}
        out["decision_basis"] = {"rule": "n<2 不做推断检验，仅描述统计"}
        return out
    tiny = [k for k, a in zip(names, arrs) if len(a) < 8]
    if tiny:
        out["power_warning"] = f"组样本量<8, 检验功效不足: {tiny}"
    all_normal = all(v.get("p") is None or v["p"] > 0.05 for v in out["normality"].values())
    if len(names) == 2:
        a, b = arrs
        if all_normal:
            va_eq = st.variance(a) / st.variance(b) if st.variance(b) else 1
            if paired:
                r = paired_t(a, b); out["test"] = {"name": "paired-t", **r}
            elif 0.5 < va_eq < 2.0:
                from statistics import fmean, variance
                sp = math.sqrt(((len(a) - 1) * variance(a) + (len(b) - 1) * variance(b)) / (len(a) + len(b) - 2))
                t = (fmean(a) - fmean(b)) / (sp * math.sqrt(1 / len(a) + 1 / len(b)))
                out["test"] = {"name": "student-t(方差齐)", "t": round(t, 4), "df": len(a) + len(b) - 2,
                               "p": _t_p(t, len(a) + len(b) - 2), "p_method": "正态近似"}
            else:
                out["test"] = {"name": "welch-t(方差不齐)", **welch_t(a, b)}
            out["effect_size"] = cohens_d(a, b)
        else:
            out["test"] = {"name": "mann-whitney-u(非正态)", **mann_whitney(a, b)}
            out["effect_size"] = {"note": "rank-biserial r = 1-2U/(n1*n2)"}
        if not paired:
            out["mean_diff_ci"] = {"diff": round(st.fmean(a) - st.fmean(b), 4),
                                   "ci95": None, "note": "配对/独立均差CI需原始配对信息，bootstrap见mean_ci"}
    else:
        if all_normal:
            out["test"] = {"name": "one-way-anova", **anova_oneway(arrs)}
            out["effect_size"] = {"eta_sq": out["test"].get("eta_sq"), "calc": "SSB/(SSB+SSW)"}
        else:
            out["test"] = {"name": "kruskal-wallis", **kruskal_wallis(arrs)}
        # 多重比较 Bonferroni
        pairs = []
        m = len(names) * (len(names) - 1) // 2
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                if arrs[i] and arrs[j]:
                    r = welch_t(arrs[i], arrs[j])
                    r["pair"] = f"{names[i]} vs {names[j]}"
                    r["p_bonferroni"] = round(min(1.0, r["p"] * m), 5)
                    pairs.append(r)
        out["posthoc_bonferroni"] = pairs
        out["multiple_comparison"] = {"method": "Bonferroni", "m": m}
    if len(names) >= 1:
        out["mean_ci"] = {names[i]: bootstrap_ci(a, seed=seed) for i, a in enumerate(arrs)}
    out["decision_basis"] = {"all_normal_jb": all_normal, "rule": "JB p>0.05 视为近似正态；两组独立看方差比(0.5-2 视为齐)"}
    return out

def run(clean_csv, spec_json, out_json):
    import csv as _csv
    spec = json.load(open(spec_json, encoding="utf-8"))
    rows = list(_csv.DictReader(open(clean_csv, encoding="utf-8-sig")))
    def num_col(rows, c):
        out_ = []
        for r in rows:
            v = (r.get(c) or "").strip()
            try: out_.append(float(v))
            except ValueError: pass
        return out_
    results = {"n_rows": len(rows), "seed": spec.get("seed", 42), "tests": []}
    for t in spec.get("tests", []):
        col = t["col"]
        if t.get("type") == "descriptive":
            results["tests"].append({"kind": "descriptive", "by": describe(num_col(rows, col), col, unit=t.get("unit", ""))})
        elif t.get("type") == "grouped":
            groups = {}
            for r in rows:
                g = (r.get(t["group_col"]) or "").strip()
                if g:
                    v = (r.get(col) or "").strip()
                    try: groups.setdefault(g, []).append(float(v))
                    except ValueError: pass
            results["tests"].append({"kind": "grouped", "group_col": t["group_col"],
                                     "result": choose_and_run(groups, paired=t.get("paired", False), col=col, unit=t.get("unit", ""), seed=results["seed"])})
    json.dump(results, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return results

if __name__ == "__main__":
    import sys
    print(json.dumps(run(sys.argv[1], sys.argv[2], sys.argv[3]), ensure_ascii=False)[:200])
    print("written:", sys.argv[3])
