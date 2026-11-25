#!/usr/bin/env python3
"""check_proposal.py — 基金申请书要素一致性与证据覆盖校验器。

输入：
  mapping.json  G/C/R/M 对应表：[{"goal":"G1","content":"C1","route":"R1","metric":"M1"}, ...]
                也接受缺行项 {"goal":"G2","content":null,...} 用于查错。
  banned.json   违禁词与全文：{"banned": ["首次","国际领先","填补空白"], "text_file": "proposal.txt"}
  claims.json   事实句→证据：[{"sentence":"...","ev_id":"ev-04"}, ...]
校验：① MAPPING：每行四要素齐且无重复编号、无缺行（目标三个路线两条即 FAIL）
     ② BANNED：全文中违禁修饰词计数
     ③ EVID：事实句缺 ev_id 即 FAIL
输出：stdout 报告，退出码 0=全过，1=有 FAIL，2=输入错误。
"""
import json
import sys


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    fails = []
    # ① 要素对应
    mapping = load(sys.argv[1])
    seen = {k: [] for k in ("goal", "content", "route", "metric")}
    for row in mapping:
        for k in seen:
            v = row.get(k)
            if not v:
                fails.append(f"mapping:{k} missing")
                print(f"MAPPING FAIL  第{row.get('goal', '?')}行缺少 {k}")
            else:
                seen[k].append(v)
    for k, v in seen.items():
        dup = sorted({x for x in v if v.count(x) > 1})
        if dup:
            fails.append(f"mapping:dup {k}")
            print(f"MAPPING FAIL  {k} 存在重复/错配 {dup}")
    print(f"MAPPING  rows={len(mapping)} goals={len(seen['goal'])} routes={len(seen['route'])}")
    # ② 违禁词
    b = load(sys.argv[2])
    with open(b["text_file"], encoding="utf-8") as f:
        text = f.read()
    for w in b.get("banned", []):
        n = text.count(w)
        if n:
            fails.append(f"banned:{w}")
            print(f"BANNED FAIL  违禁修饰词 '{w}' 出现 {n} 次")
        else:
            print(f"BANNED OK    '{w}' 未出现")
    # ③ 证据覆盖
    claims = load(sys.argv[3])
    for c in claims:
        if c.get("ev_id"):
            print(f"EVID OK    {c['ev_id']}")
        else:
            fails.append("evid:missing")
            print(f"EVID FAIL  事实句缺 ev_id：{c.get('sentence', '')[:30]}...")
    print(f"SUMMARY   fails={fails}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
