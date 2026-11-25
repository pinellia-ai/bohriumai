#!/usr/bin/env python3
"""check_transfer.py — 成果转化改写保真校验器。

输入：
  source.json 源文要素：{"numbers": ["120", "0.05", "35.2%"], "figures": ["Fig.3", "Fig.4"],
                        "terms": {"machine learning": "机器学习"}}
  draft.json  改稿要素：{"numbers": ["120", "0.05"], "figures": ["Fig.3"],
                        "term_forms": {"机器学习": ["机器学习", "ML"]}}

校验：① 数字保真（源文数字是否都被保留或给出删除理由清单 missing_reasons）
     ② 图表引用完整（保留级图表不得缺失）
     ③ 术语唯一（每个锁定术语在改稿只允许一种形式）
输出：stdout 逐项报告，退出码 0=全过，1=有 FAIL，2=输入错误。
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
    src, draft = load(sys.argv[1]), load(sys.argv[2])
    fails = []
    # ① 数字保真
    reasons = set(src.get("missing_reasons", []))
    for n in src.get("numbers", []):
        if n in draft.get("numbers", []):
            print(f"NUM OK   {n}")
        elif f"number:{n}" in reasons:
            print(f"NUM SKIP {n}（有删除理由）")
        else:
            fails.append(f"number:{n}")
            print(f"NUM FAIL {n} 在改稿中缺失且无删除理由")
    # ② 图表引用
    for f_ in src.get("figures", []):
        if f_ in draft.get("figures", []):
            print(f"FIG OK   {f_}")
        else:
            fails.append(f"figure:{f_}")
            print(f"FIG FAIL {f_} 图表引用丢失")
    # ③ 术语唯一
    for term, forms in draft.get("term_forms", {}).items():
        if len(forms) == 1:
            print(f"TERM OK  {term}: {forms[0]}")
        else:
            fails.append(f"term:{term}")
            print(f"TERM FAIL {term} 出现多种形式 {forms}")
    print(f"SUMMARY  fails={fails}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
