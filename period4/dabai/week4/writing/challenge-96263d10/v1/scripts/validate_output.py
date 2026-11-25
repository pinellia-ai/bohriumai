#!/usr/bin/env python3
"""validate_output.py — 学术格式与模板适配的逐项校验器。

输入：
  spec.json  模板规格表，如 {"正文行距": "1.5倍", "页边距-左": "3.17cm", ...}
            （键为规格项名，值为模板要求值；not_specified 项不放入）
  actual.json 成品实测值，如 {"正文行距": "1.5倍", "页边距-左": "3.17cm", ...}
  units.json  可选，转换完整性对账：
            {"expected": ["U-001","U-002"], "found": ["U-001"]}（expected 中每个 unit 应在 found 中）

输出：stdout 逐项 PASS/FAIL 报告，退出码 0=全过，1=存在 FAIL，2=输入错误。
用法：python3 validate_output.py spec.json actual.json [units.json]
"""
import json
import sys


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def normalize(v):
    return str(v).strip().lower().replace("，", ",")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    spec, actual = load(sys.argv[1]), load(sys.argv[2])
    fails, missing = [], []
    for key, want in spec.items():
        got = actual.get(key)
        if got is None:
            missing.append(key)
            print(f"MISSING  {key}: 成品未实测（模板要求 {want}）")
        elif normalize(got) == normalize(want):
            print(f"PASS     {key} = {want}")
        else:
            fails.append(key)
            print(f"FAIL     {key}: 模板要求 {want}, 成品 {got}")
    units_ok = True
    if len(sys.argv) >= 4:
        units = load(sys.argv[3])
        lost = sorted(set(units.get("expected", [])) - set(units.get("found", [])))
        units_ok = not lost
        print(f"UNITS    expected={len(units.get('expected', []))} found={len(units.get('found', []))}")
        for u in lost:
            print(f"LOST     {u} 内容单元在成品中不可指认")
    print(f"SUMMARY  pass={len(spec) - len(fails) - len(missing)}/{len(spec)} fails={fails} missing={missing} units_ok={units_ok}")
    return 0 if not fails and not missing and units_ok else 1


if __name__ == "__main__":
    sys.exit(main())
