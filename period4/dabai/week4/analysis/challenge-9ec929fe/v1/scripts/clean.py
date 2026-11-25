#!/usr/bin/env python3
"""clean.py — 规则外置的科研数据清洗器（纯标准库）。

用法: clean.py <data.csv> <rules.json> <outdir>
rules.json（全部规则显式可读，清洗动作留痕）:
{
  "missing_tokens": ["", "NA", "N/A", "-999", " ", "未检出"],   # 按字段语义改写
  "missing_policy": {"<col>": "keep_missing"},                  # 本工具不填补！只标记。impute 明确禁止
  "dedup": {"keys": ["sample_id", "timestamp"], "keep": "first|last|largest_complete"},
  "outliers": {"<col>": {"lower": 0, "upper": 100, "method": "physical|iqr", "iqr_k": 3, "action": "flag|cap|drop"}},
  "units": {"<col>": {"from": "mg/L", "to": "μg/mL", "factor": 1000.0}},   # 换算留映射
  "numeric_cols": ["<col>", ...],
  "date_cols": {"<col>": "%Y-%m-%d"}
}
输出: clean.csv / cleaning_log.json（逐字段逐动作计数+受影响行号）/ 不改动原始文件。
原则: 缺失一律保留为空并计数（不填补不推测）；异常默认 flag 不删；单位换算保留原值列 _raw_<col>。
"""
import csv, json, math, os, sys
from datetime import datetime

def is_missing(v, tokens):
    return v is None or str(v).strip() in tokens

def parse_num(v):
    try:
        return float(str(v).strip())
    except (ValueError, TypeError):
        return None

def main(data_p, rules_p, outdir):
    rules = json.load(open(rules_p, encoding="utf-8"))
    os.makedirs(outdir, exist_ok=True)
    with open(data_p, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        fields = rows[0].keys() if rows else []
    log = {"source": os.path.abspath(data_p), "n_rows_in": len(rows),
           "actions": [], "field_stats": {}}

    # 1 缺失标记（不填补）
    tokens = set(rules.get("missing_tokens", ["", "NA", "N/A", "-999"]))
    for col in fields:
        miss_rows = [i for i, r in enumerate(rows) if is_missing(r.get(col), tokens)]
        if miss_rows:
            for i in miss_rows:
                rows[i][col] = ""
            log["field_stats"].setdefault(col, {})["missing"] = len(miss_rows)
            log["actions"].append({"field": col, "action": "mark_missing", "n": len(miss_rows),
                                   "rows": miss_rows[:50], "policy": "keep_missing(不填补)"})

    # 2 数值化（不可解析的进缺失并记数）
    for col in rules.get("numeric_cols", []):
        bad = [i for i, r in enumerate(rows) if r.get(col) and parse_num(r[col]) is None]
        for i, r in enumerate(rows):
            v = parse_num(r.get(col))
            rows[i][col] = "" if v is None else repr(v)
        if bad:
            log["actions"].append({"field": col, "action": "coerce_numeric_failed_to_missing", "n": len(bad), "rows": bad[:50]})

    # 3 单位换算（保留原值）
    for col, u in rules.get("units", {}).items():
        raw_col = "_raw_" + col
        for i, r in enumerate(rows):
            v = parse_num(r.get(col))
            if v is not None:
                rows[i][raw_col] = r[col]
                rows[i][col] = repr(v * u["factor"])
        log["actions"].append({"field": col, "action": "unit_convert",
                               "detail": f'{u["from"]}->{u["to"]} x{u["factor"]}', "raw_kept_in": raw_col})

    # 4 日期标准化
    for col, fmt in rules.get("date_cols", {}).items():
        ok, bad = 0, []
        for i, r in enumerate(rows):
            v = (r.get(col) or "").strip()
            if not v: continue
            try:
                rows[i][col] = datetime.strptime(v, fmt).date().isoformat(); ok += 1
            except ValueError:
                bad.append(i)
        log["actions"].append({"field": col, "action": "date_normalize", "fmt": fmt, "n_ok": ok, "n_bad": len(bad)})

    # 5 异常值（默认 flag）
    for col, o in rules.get("outliers", {}).items():
        vals = [(i, parse_num(r.get(col))) for i, r in enumerate(rows)]
        vals = [(i, v) for i, v in vals if v is not None]
        flagged = []
        if o.get("method") == "physical" and ("lower" in o or "upper" in o):
            flagged = [i for i, v in vals if (o.get("lower") is not None and v < o["lower"]) or (o.get("upper") is not None and v > o["upper"])]
        elif o.get("method") == "iqr":
            vs = sorted(v for _, v in vals)
            if len(vs) >= 2:
                q = lambda p: vs[min(len(vs) - 1, int(p * (len(vs) - 1)))]
                iqr = q(0.75) - q(0.25); k = o.get("iqr_k", 3)
                lo, hi = q(0.25) - k * iqr, q(0.75) + k * iqr
                flagged = [i for i, v in vals if v < lo or v > hi]
        act = o.get("action", "flag")
        if flagged:
            for i in flagged:
                if act == "cap" and parse_num(rows[i][col]) is not None:
                    rows[i][col + "_capped"] = rows[i][col]
                    rows[i][col] = repr(min(max(parse_num(rows[i][col]), o.get("lower", -math.inf)), o.get("upper", math.inf)))
                elif act == "drop":
                    rows[i][col + "_dropped"] = "1"
            log["actions"].append({"field": col, "action": f"outlier_{act}", "n": len(flagged),
                                   "rows": flagged[:50], "method": o.get("method")})

    # 6 去重（按真实主键）
    dd = rules.get("dedup", {})
    if dd.get("keys"):
        keys = dd["keys"]
        seen, drop = {}, []
        for i, r in enumerate(rows):
            k = tuple((r.get(c) or "").strip().lower() for c in keys)
            if k in seen:
                if dd.get("keep") == "last":
                    drop.append(seen[k]); seen[k] = i
                else:
                    drop.append(i)
            else:
                seen[k] = i
        if drop:
            rows = [r for i, r in enumerate(rows) if i not in drop]
            log["actions"].append({"field": ",".join(keys), "action": "dedup", "n_removed": len(drop),
                                   "rows": drop[:50], "keep": dd.get("keep", "first")})

    out_csv = os.path.join(outdir, "clean.csv")
    if rows:
        allf = list(fields) + sorted({c for r in rows for c in r if c not in fields})
        with open(out_csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=allf)
            w.writeheader(); w.writerows(rows)
    log["n_rows_out"] = len(rows)
    log["n_removed"] = log["n_rows_in"] - len(rows)
    json.dump(log, open(os.path.join(outdir, "cleaning_log.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"clean_csv": out_csv, "rows_in": log["n_rows_in"], "rows_out": log["n_rows_out"],
                      "actions": len(log["actions"])}, ensure_ascii=False))

if __name__ == "__main__":
    main(*sys.argv[1:4])
