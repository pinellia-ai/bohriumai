#!/usr/bin/env python3
"""资料库落库三阶段：scan → plan → apply(含校验/日志/幂等续跑) → verify。
用法:
  python3 organize.py scan <源目录> --out inventory.json
  python3 organize.py plan <源目录> --inventory inventory.json --template "{project}/{year}/{type}" --out plan.json
  python3 organize.py apply plan.json --dst <库根> --log ops_log.jsonl --out manifest.json
  python3 organize.py verify manifest.json --dst <库根>
"""
import argparse, hashlib, json, os, re, shutil, sys, time

VERSION_PAT = re.compile(r'(v\d+|final|修订|\(\d+\))', re.IGNORECASE)
TYPE_MAP = {'.pdf': 'documents', '.doc': 'documents', '.docx': 'documents',
            '.csv': 'data', '.tsv': 'data', '.xlsx': 'data', '.txt': 'data',
            '.png': 'figures', '.jpg': 'figures', '.tif': 'figures', '.svg': 'figures'}

def sha256_of(p, max_bytes=64 << 20):
    h = hashlib.sha256()
    try:
        with open(p, 'rb') as f:
            if os.path.getsize(p) > max_bytes:
                return "TOO_LARGE"
            for chunk in iter(lambda: f.read(1 << 20), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

def cmd_scan(a):
    files = []
    for dp, _, fns in os.walk(a.source):
        for n in sorted(fns):
            fp = os.path.join(dp, n)
            rel = os.path.relpath(fp, a.source)
            try:
                st = os.stat(fp)
            except OSError as e:
                files.append({"path": rel, "status": "no_permission", "error": str(e)}); continue
            d = sha256_of(fp)
            files.append({"path": rel, "size": st.st_size, "mtime": int(st.st_mtime),
                          "sha256": d, "special_chars": bool(re.search(r'[\\/:*?"<>|]', n))})
    json.dump({"source": a.source, "total_files": len(files), "files": files}, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print(f"scanned {len(files)} -> {a.out}")

def classify_type(rel):
    return TYPE_MAP.get(os.path.splitext(rel)[1].lower(), 'misc')

def guess_year(rel):
    m = re.search(r'(20\d{2}|19\d{2})', rel)
    return m.group(1) if m else 'unknown_year'

def guess_project(rel):
    m = re.search(r'(P[-_]\d{3,}[-_]\d{0,4}|project[-_][\w-]+)', rel, re.I)
    return m.group(1) if m else 'unknown_project'

def sanitize(name):
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    return name[:180]

def cmd_plan(a):
    inv = json.load(open(a.inventory, encoding='utf-8'))
    seen_hashes, dst_taken = {}, {}
    actions = []
    for f in inv['files']:
        if not f.get('sha256'):
            actions.append({"action": "skip", "src": f['path'], "reason": f.get('status', 'unreadable_or_too_large')}); continue
        base = os.path.basename(f['path'])
        year = guess_year(f['path']); proj = guess_project(f['path']); typ = classify_type(f['path'])
        dst_rel = a.template.format(project=proj, year=year, type=typ).strip('/') + '/' + sanitize(base)
        if f['sha256'] in seen_hashes:
            actions.append({"action": "alias", "src": f['path'], "dst": dst_rel, "alias_of": seen_hashes[f['sha256']],
                            "sha256": f['sha256'], "reason": "same content hash as ingested file"}); continue
        seen_hashes[f['sha256']] = dst_rel
        cand, k = dst_rel, 2
        while dst_rel in dst_taken and dst_taken[dst_rel] != f['sha256']:
            stem, ext = os.path.splitext(dst_rel)
            cand = f"{stem}_v{k}{ext}"; k += 1
        reason = "unique" if cand == dst_rel else "name collision, different hash -> versioned, never overwrite"
        dst_taken[cand] = f['sha256']
        actions.append({"action": "copy", "src": f['path'], "dst": cand, "sha256": f['sha256'], "reason": reason})
    json.dump({"template": a.template, "n_actions": len(actions), "actions": actions}, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print(f"plan {len(actions)} actions -> {a.out}")

def cmd_apply(a):
    plan = json.load(open(a.plan, encoding='utf-8'))
    done = set()
    if os.path.exists(a.out):
        done = {m.get('dst_rel') for m in json.load(open(a.out, encoding='utf-8')).get('ingested', [])}
    log = open(a.log, 'a', encoding='utf-8')
    ingested, aliases, skipped, mismatch = [], [], [], []
    for act in plan['actions']:
        if act['action'] == 'skip':
            skipped.append(act); continue
        if act['action'] == 'alias':
            aliases.append(act); continue
        # apply 需要 --src 指向源目录（与 plan 时的 source 相同）
        src = os.path.join(a.src, act['src'])
        dst = os.path.join(a.dst, act['dst'])
        if act['dst'] in done:
            continue
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        except Exception as e:
            skipped.append({"action": "skip", "src": act['src'], "reason": f"copy_failed: {e}"})
            log.write(json.dumps({"t": time.time(), "action": "copy_failed", "src": act['src'], "dst": act['dst'], "error": str(e)}, ensure_ascii=False) + '\n')
            continue
        got = sha256_of(dst)
        rec = {"t": time.time(), "action": "copy", "src": act['src'], "dst": act['dst'], "sha256": act['sha256']}
        if got == act['sha256']:
            ingested.append(act); rec["result"] = "ok"
        else:
            mismatch.append({**act, "got": got}); rec["result"] = "hash_mismatch"
            try:
                os.remove(dst)
            except OSError:
                pass
        log.write(json.dumps(rec, ensure_ascii=False) + '\n')
    log.close()
    manifest = {"total_ingested": len(ingested), "aliased": len(aliases), "skipped": len(skipped),
                "hash_mismatch": len(mismatch), "ingested": ingested, "aliases": aliases,
                "failed": mismatch + skipped}
    json.dump(manifest, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print(f"applied: {manifest['total_ingested']} ingested, {manifest['aliased']} aliased, {manifest['skipped']} skipped, {manifest['hash_mismatch']} mismatch -> {a.out}")

def cmd_verify(a):
    m = json.load(open(a.manifest, encoding='utf-8'))
    bad = []
    for act in m['ingested']:
        got = sha256_of(os.path.join(a.dst, act['dst']))
        if got != act['sha256']:
            bad.append(act['dst'])
    n_files = sum(len(fns) for _, _, fns in os.walk(a.dst))
    print(json.dumps({"verify": "pass" if not bad else "fail", "bad": bad,
                      "library_file_count": n_files, "manifest_ingested": m['total_ingested'],
                      "reconcile": m['total_ingested'] + m['aliased'] + m['skipped']}, ensure_ascii=False))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('scan'); s.add_argument('source'); s.add_argument('--out', required=True)
    p = sub.add_parser('plan'); p.add_argument('source'); p.add_argument('--inventory', required=True)
    p.add_argument('--template', default='{project}/{year}/{type}'); p.add_argument('--out', required=True)
    apx = sub.add_parser('apply'); apx.add_argument('plan'); apx.add_argument('--src', required=True)
    apx.add_argument('--dst', required=True); apx.add_argument('--log', required=True); apx.add_argument('--out', required=True)
    v = sub.add_parser('verify'); v.add_argument('manifest'); v.add_argument('--dst', required=True)
    a = ap.parse_args()
    {'scan': cmd_scan, 'plan': cmd_plan, 'apply': cmd_apply, 'verify': cmd_verify}[a.cmd](a)
