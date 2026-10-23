"""Small expression language for student implementations, without arbitrary exec."""
import ast
import cv2
import numpy as np

REFERENCE = {
    "hsv": "cv2.cvtColor(image, cv2.COLOR_BGR2HSV)",
    "raw": "cv2.inRange(hsv, lower, upper)",
    "contours": "cv2.findContours(clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]",
    "selected": "max(eligible, key=cv2.contourArea) if eligible else None",
}
FUNCTIONS = {"cv2.cvtColor": cv2.cvtColor, "cv2.inRange": cv2.inRange,
             "cv2.findContours": cv2.findContours, "cv2.contourArea": cv2.contourArea, "max": max}
CONSTANTS = {"cv2.COLOR_BGR2HSV": cv2.COLOR_BGR2HSV, "cv2.RETR_EXTERNAL": cv2.RETR_EXTERNAL,
             "cv2.CHAIN_APPROX_SIMPLE": cv2.CHAIN_APPROX_SIMPLE}


def expression(source, context, functions=None, constants=None):
    functions, constants = functions or {}, constants or {}
    if not isinstance(source, str) or len(source) > 1000:
        raise ValueError("Use one short expression, not a program")
    if not source.strip(): raise ValueError("Enter an expression using the operation reference above")
    try:
        tree = ast.parse(source, mode="eval")
        if len(list(ast.walk(tree))) > 100: raise ValueError("Expression is too complex")
        def visit(node):
            if isinstance(node, ast.Expression): return visit(node.body)
            if isinstance(node, ast.Constant) and isinstance(node.value, (str, int, float, bool, type(None))): return node.value
            if isinstance(node, ast.Name) and node.id in context: return context[node.id]
            name = ast.unparse(node)
            if name in functions: return functions[name]
            if name in constants: return constants[name]
            if isinstance(node, ast.IfExp): return visit(node.body) if visit(node.test) else visit(node.orelse)
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not): return not visit(node.operand)
            if isinstance(node, ast.BoolOp):
                values = [bool(visit(v)) for v in node.values]
                return all(values) if isinstance(node.op, ast.And) else any(values)
            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and node.slice.value == 0:
                return visit(node.value)[0]
            if isinstance(node, ast.Call) and ast.unparse(node.func) in functions:
                if any(k.arg is None for k in node.keywords): raise ValueError("Expanded arguments are not supported")
                return functions[ast.unparse(node.func)](*[visit(a) for a in node.args], **{k.arg: visit(k.value) for k in node.keywords})
            raise ValueError("Use only the documented names, calls, and conditional expressions")
        return visit(tree)
    except (SyntaxError, TypeError, IndexError, KeyError, cv2.error) as error:
        raise ValueError(f"Check your expression: {error}") from error


def evaluate(source, context):
    return expression(source, context, FUNCTIONS, CONSTANTS)


def check_implementation(code):
    if not isinstance(code, dict) or set(code) != set(REFERENCE):
        raise ValueError("Implement all four expressions")
    missing = [name for name,value in code.items() if not isinstance(value,str) or not value.strip()]
    if missing: raise ValueError("Complete the implementation fields: "+", ".join(missing))
    # Check operations, not accuracy on the photo. No hard-coded image answers pass.
    for seed in (4, 19):
        image = np.random.default_rng(seed).integers(0, 256, (24, 32, 3), dtype=np.uint8)
        context = {"image": image, "lower": np.array([0, 0, 150], np.uint8), "upper": np.array([179, 65, 255], np.uint8)}
        for key in ("hsv", "raw"):
            expected = evaluate(REFERENCE[key], context)
            actual = evaluate(code[key], context)
            if not isinstance(actual, np.ndarray) or not np.array_equal(actual, expected):
                raise ValueError(f"{key}: output does not match the documented operation")
            context[key] = actual
        context["clean"] = context["raw"]
        contours = evaluate(code["contours"], context)
        expected = evaluate(REFERENCE["contours"], context)
        if not isinstance(contours, (tuple, list)) or len(contours) != len(expected) or any(not np.array_equal(a,b) for a,b in zip(contours,expected)):
            raise ValueError("contours: return the contours, not the hierarchy")
        for eligible in ([], list(contours)):
            context["eligible"] = eligible
            selected = evaluate(code["selected"], context)
            correct = evaluate(REFERENCE["selected"], context)
            if (selected is None) != (correct is None) or (correct is not None and not np.array_equal(selected, correct)):
                raise ValueError("selected: choose the largest eligible contour and handle an empty list")
    return True
