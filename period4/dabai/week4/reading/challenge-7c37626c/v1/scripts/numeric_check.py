#!/usr/bin/env python3
"""numeric_check.py — 公式数值代入核验（7c37626c 用）。

用法:
  python3 numeric_check.py --spec spec.json
  python3 numeric_check.py --selftest

spec 格式:
  {"verifications": [
     {"formula_id": "eq-2",
      "expression": "A * exp(-E_a/(R*T))",
      "variables": {"A": {"value": 1e6, "unit": "s^-1"},
                    "E_a": {"value": 50, "unit": "kJ/mol"},
                    "T": {"value": 320, "unit": "K"},
                    "R": {"value": 8.314, "unit": "J/mol/K"}},
      "reported": "3.5e-3 s^-1"}]}

安全求值：AST 白名单（+ - * / ** ()、math 白名单函数与常数），禁一切调用外函数/属性/下标。
输出：中间值与最终值、与 reported 的偏差与数量级检查（≥3 个数量级 → magnitude_mismatch）。
缺变量/除零/非法运算 → unverifiable，不硬算、不填 0。
"""
import argparse, ast, json, math, operator, sys

OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg,
       ast.UAdd: operator.pos, ast.Mod: operator.mod}
FUNCS = {"exp": math.exp, "log": math.log, "log10": math.log10, "sqrt": math.sqrt,
         "abs": abs, "sin": math.sin, "cos": math.cos, "tan": math.tan}
CONSTS = {"pi": math.pi, "e": math.e, "inf": math.inf}


class _Eval(ast.NodeVisitor):
    def __init__(self, variables):
        self.vars = variables
        self.steps = []

    def visit_Constant(self, node):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError(f"不允许的字面量: {node.value!r}")

    def visit_Name(self, node):
        if node.id in self.vars:
            v = self.vars[node.id]
            val = v["value"] if isinstance(v, dict) else v
            self.steps.append(f"{node.id} = {val}")
            return float(val)
        if node.id in CONSTS:
            return CONSTS[node.id]
        raise ValueError(f"未定义变量: {node.id}")

    def visit_BinOp(self, node):
        L, R = self.visit(node.left), self.visit(node.right)
        op = OPS.get(type(node.op))
        if op is None:
            raise ValueError(f"不允许的运算: {type(node.op).__name__}")
        if isinstance(node.op, ast.Div) and R == 0:
            raise ZeroDivisionError("除零: 代入无解，标 unverifiable")
        res = op(L, R)
        self.steps.append(f"{ast.dump(node.op)[:14]}... {L} op {R} = {res}")
        return res

    def visit_UnaryOp(self, node):
        op = OPS.get(type(node.op))
        if op is None:
            raise ValueError("不允许的一元运算")
        return op(self.visit(node.operand))

    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name) or node.func.id not in FUNCS:
            raise ValueError(f"不允许的函数调用: {getattr(node.func, 'id', '?')}")
        args = [self.visit(a) for a in node.args]
        return FUNCS[node.func.id](*args)

    def generic_visit(self, node):
        raise ValueError(f"不允许的语法节点: {type(node).__name__}")


def safe_eval(expression, variables):
    tree = ast.parse(expression, mode="eval")
    if not isinstance(tree, ast.Expression):
        raise ValueError("须为表达式")
    ev = _Eval(variables)
    val = ev.visit(tree.body)
    return val, ev.steps


def parse_reported(s):
    """'3.5e-3 s^-1' -> 3.5e-3（取首个数字）。"""
    if not s:
        return None
    import re
    m = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", str(s))
    return float(m.group()) if m else None


def check(item):
    out = {"formula_id": item.get("formula_id")}
    try:
        val, steps = safe_eval(item["expression"], item.get("variables", {}))
        out["computed"] = f"{val:.6g}"
        out["steps"] = steps
        rep = parse_reported(item.get("reported"))
        if rep is not None and rep != 0 and val != 0:
            ratio = abs(val / rep)
            if ratio >= 1e3 or ratio <= 1e-3:
                out["verdict"] = "magnitude_mismatch"
            else:
                out["verdict"] = "consistent"
            out["deviation"] = f"{abs(val - rep) / abs(rep):.2%}"
        else:
            out["verdict"] = "reported_missing_or_zero"
    except (ValueError, ZeroDivisionError, OverflowError) as e:
        out["verdict"] = "unverifiable"
        out["reason"] = str(e)
    return out


def selftest():
    spec = {"verifications": [
        {"formula_id": "eq-2", "expression": "A * exp(-E_a/(R*T))",
         "variables": {"A": {"value": 1e6, "unit": "s^-1"},
                       "E_a": {"value": 50000, "unit": "J/mol"},
                       "T": {"value": 320, "unit": "K"},
                       "R": {"value": 8.314, "unit": "J/mol/K"}},
         "reported": "3.5e-3 s^-1"},
        {"formula_id": "eq-unit-bug", "expression": "A * exp(-E_a/(R*T))",
         "variables": {"A": {"value": 1e6, "unit": "s^-1"},
                       "E_a": {"value": 50, "unit": "kJ/mol"},
                       "T": {"value": 320, "unit": "K"},
                       "R": {"value": 8.314, "unit": "J/mol/K"}},
         "reported": "3.5e-3 s^-1"},
        {"formula_id": "eq-bad", "expression": "x / y",
         "variables": {"x": {"value": 1, "unit": "m"}, "y": {"value": 0, "unit": "s"}},
         "reported": None},
        {"formula_id": "eq-hack", "expression": "__import__('os').system('x')",
         "variables": {}, "reported": None}]}
    results = [check(i) for i in spec["verifications"]]
    for r in results:
        print(json.dumps(r, ensure_ascii=False))
    ok = (results[0]["verdict"] == "consistent"
          and results[1]["verdict"] == "magnitude_mismatch"
          and results[2]["verdict"] == "unverifiable"
          and results[3]["verdict"] == "unverifiable")
    print("selftest:", "PASS" if ok else "FAIL")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec"); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if not a.spec:
        ap.error("--spec 必填（或用 --selftest）")
    with open(a.spec, encoding="utf-8") as f:
        spec = json.load(f)
    outs = [check(i) for i in spec.get("verifications", [])]
    print(json.dumps(outs, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
