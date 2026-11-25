#!/usr/bin/env python3
"""pipeline.py — 五段流水线编排器（checkpoint + resume）。
plan.json:
{"tasks": [
  {"name": "ingest",  "cmd": "python3 $S/db_probe.py <db> /app/work", "assert": "row_counts_json_exists"},
  {"name": "clean",   "cmd": "python3 $S/clean.py <raw> <rules> /app/output/cleaned"},
  {"name": "stats",   "cmd": "python3 $S/stats_kit.py <clean> <spec> /app/output/stats_results.json"},
  {"name": "plot",    "cmd": "python3 $S/chart_builder.py <spec> --outdir /app/output"},
  {"name": "report",  "cmd": "python3 $S/report_builder.py <stats> <template> /app/output/report.md"}
]}
$S = 本脚本目录。--resume 从最后 done checkpoint 续跑。
"""
import json, os, re, subprocess, sys, time

def ckpt_dir(work): return os.path.join(work, "checkpoints")

def last_done(work):
    best = 0
    d = ckpt_dir(work)
    if os.path.isdir(d):
        for f in os.listdir(d):
            m = re.match(r"stage_(\d+)\.json", f)
            if m:
                c = json.load(open(os.path.join(d, f), encoding="utf-8"))
                if c.get("status") == "done":
                    best = max(best, int(m.group(1)))
    return best

def main(plan_p, work, outdir, resume=False):
    os.makedirs(ckpt_dir(work), exist_ok=True)
    os.makedirs(outdir, exist_ok=True)
    plan = json.load(open(plan_p, encoding="utf-8"))
    S = os.path.dirname(os.path.abspath(__file__))
    start = last_done(work) if resume else 0
    results = []
    for i, task in enumerate(plan["tasks"], start=1):
        if i <= start:
            results.append({"stage": i, "name": task["name"], "status": "skipped(done)"})
            continue
        cmd = task["cmd"].replace("$S", S)
        t0 = time.time()
        try:
            p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=180)
            ok = p.returncode == 0
            err = p.stderr[-1000:]
        except subprocess.TimeoutExpired:
            ok, err = False, "TIMEOUT"
        c = {"stage": i, "name": task["name"], "cmd": cmd, "status": "done" if ok else "failed",
             "seconds": round(time.time() - t0, 2), "stderr": err, "assert": task.get("assert", "")}
        json.dump(c, open(os.path.join(ckpt_dir(work), f"stage_{i}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        results.append({"stage": i, "name": task["name"], "status": c["status"]})
        if not ok:
            print(json.dumps({"stopped_at": i, "reason": err[:200], "results": results}, ensure_ascii=False))
            sys.exit(1)
    print(json.dumps({"all_done": True, "results": results}, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], a[2], resume="--resume" in a)
