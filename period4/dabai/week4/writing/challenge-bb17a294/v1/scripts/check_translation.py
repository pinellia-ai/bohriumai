#!/usr/bin/env python3
"""check_translation.py — 学术翻译数字保真与术语一致性校验器。

输入：
  numbers.json           原文数字：[{"value":"1.2 million","location":"p.2","norm":"1.2e6"}, ...]
  translated_numbers.json 译文数字：[{"value":"120万","location":"P-002","norm":"1.2e6"}, ...]
  term_check.json        术语→译文出现形式：{"gradient descent": ["梯度下降"]}
输出：NUM OK/MISS/ALTER + TERM OK/MULTI 报告，退出码 0=全过，1=有 FAIL，2=输入错误。
比对逻辑：按 norm（归一化数值）匹配；norm 缺失时按 value 顺序配对。
"""
import json
import sys


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    src_nums, dst_nums = load(sys.argv[1]), load(sys.argv[2])
    fails = []
    dst_norms = [d.get("norm") or d.get("value") for d in dst_nums]
    for n in src_nums:
        key = n.get("norm") or n["value"]
        if key in dst_norms:
            print(f"NUM OK    {n['value']} -> {key} @ {n.get('location','?')}")
        else:
            fails.append(f"number:{n['value']}")
            print(f"NUM FAIL  {n['value']} @ {n.get('location','?')} 在译文中未找到（漏译或改值）")
    extra = [k for k in dst_norms if k not in {n.get("norm") or n["value"] for n in src_nums}]
    if extra:
        fails.append("number:extra")
        print(f"NUM EXTRA 译文出现原文没有的数值 {extra}（查增译/算错）")
    if len(sys.argv) >= 4:
        terms = load(sys.argv[3])
        for term, forms in terms.items():
            uniq = sorted(set(forms))
            if len(uniq) == 1:
                print(f"TERM OK   {term} -> {uniq[0]}")
            else:
                fails.append(f"term:{term}")
                print(f"TERM FAIL {term} 多种形式 {uniq}（应锁定一种）")
    print(f"SUMMARY   fails={fails}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
