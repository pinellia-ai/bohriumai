#!/usr/bin/env python3
"""run_guard.py — 受控执行与环境快照。
用法:
  run_guard.py env <out_env.json>                          # 环境快照
  run_guard.py run "<cmd>" <runs_dir> [timeout_s]          # 受控执行，留痕 runs/run_NNN.json
"""
import json, os, platform, shutil, subprocess, sys, time

def env_snapshot(out_p):
    env = {"platform": platform.platform(), "python": sys.version.split()[0],
           "which_python": shutil.which("python3") or sys.executable, "packages": {}}
    for mod in ("numpy", "scipy", "pandas", "matplotlib", "sqlite3", "sklearn"):
        try:
            m = __import__(mod)
            env["packages"][mod] = getattr(m, "__version__", "available")
        except ImportError:
            env["packages"][mod] = "MISSING"
    env["seed_note"] = "随机过程必须显式 seed"
    json.dump(env, open(out_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(env, ensure_ascii=False)[:300])

def run(cmd, runs_dir, timeout=120):
    os.makedirs(runs_dir, exist_ok=True)
    n = 1
    while os.path.exists(os.path.join(runs_dir, f"run_{n:03d}.json")):
        n += 1
    t0 = time.time()
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        rec = {"id": f"run_{n:03d}", "cmd": cmd, "exit_code": p.returncode,
               "seconds": round(time.time() - t0, 2), "stdout": p.stdout[-4000:], "stderr": p.stderr[-4000:],
               "timeout": False}
    except subprocess.TimeoutExpired as e:
        rec = {"id": f"run_{n:03d}", "cmd": cmd, "exit_code": None, "seconds": round(time.time() - t0, 2),
               "stdout": (e.stdout or b"").decode()[-4000:] if isinstance(e.stdout, bytes) else str(e.stdout)[-4000:],
               "stderr": f"TIMEOUT after {timeout}s", "timeout": True}
    out = os.path.join(runs_dir, f"run_{n:03d}.json")
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: rec[k] for k in ("id", "cmd", "exit_code", "seconds", "timeout")}, ensure_ascii=False))
    sys.exit(0 if rec["exit_code"] == 0 else 1)

if __name__ == "__main__":
    if sys.argv[1] == "env":
        env_snapshot(sys.argv[2])
    elif sys.argv[1] == "run":
        run(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 120)
