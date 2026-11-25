#!/usr/bin/env python3
"""盘点材料目录：路径、大小、mtime、sha256、可读性、副本与版本链。
用法: python3 inventory.py <材料根目录> --out /app/work/inventory.json
"""
import argparse, hashlib, json, os, re, sys, time

VERSION_PAT = re.compile(r'(?:[_\-\s(]|\b)(v(\d+)|final|修订版?|rev(\d+)|copy|\(\d+\))', re.IGNORECASE)
MAX_HASH = 64 * 1024 * 1024

def sha256_of(p):
    h = hashlib.sha256()
    try:
        with open(p, 'rb') as f:
            for chunk in iter(lambda: f.read(1 << 20), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

def scan(root):
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        for name in sorted(filenames):
            fp = os.path.join(dirpath, name)
            rel = os.path.relpath(fp, root)
            try:
                st = os.stat(fp)
                readable = os.access(fp, os.R_OK)
            except OSError as e:
                files.append({"path": rel, "status": "no_permission", "error": str(e)})
                continue
            size = st.st_size
            digest = sha256_of(fp) if readable and size <= MAX_HASH else None
            files.append({
                "path": rel, "size": size, "mtime": int(st.st_mtime),
                "readable": readable, "sha256": digest,
                "version_tag": (VERSION_PAT.search(name).group(0).strip(' (_-') if VERSION_PAT.search(name) else None),
            })
    return files

def group_versions(files):
    by_hash, chains = {}, {}
    for f in files:
        if not f.get("sha256"):
            continue
        by_hash.setdefault(f["sha256"], []).append(f["path"])
    dupes = {h: ps for h, ps in by_hash.items() if len(ps) > 1}
    # 命名递进的版本链：同 base 名不同哈希
    base_map = {}
    for f in files:
        base = re.sub(r'(v\d+|final|修订|\(\d+\))', '', os.path.splitext(f["path"])[0], flags=re.I).rstrip(' _-')
        base_map.setdefault(base, []).append(f)
    for base, group in base_map.items():
        hashes = {f.get("sha256") for f in group}
        if len(group) > 1 and len(hashes) > 1:
            chains[base] = [f["path"] for f in group]
    return dupes, chains

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root"); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    if not os.path.isdir(a.root):
        json.dump({"status": "failed", "reason": f"root not found: {a.root}"}, open(a.out, "w"), ensure_ascii=False)
        sys.exit(1)
    files = scan(a.root)
    dupes, chains = group_versions(files)
    out = {
        "root": a.root, "scanned_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_files": len(files), "readable": sum(1 for f in files if f.get("readable")),
        "unreadable_or_failed": [f for f in files if not f.get("readable") or not f.get("sha256") and f.get("readable")],
        "duplicate_groups": dupes, "version_chains": chains, "files": files,
        "elapsed_s": round(time.time() - t0, 2),
    }
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump(out, open(a.out, "w"), ensure_ascii=False, indent=1)
    print(f"scanned {out['total_files']} files -> {a.out}")

if __name__ == "__main__":
    main()
