from tools.calculator_tool import evaluate


def run_tests():
    cases = [
        "1+2*3",
        "10 / 4",
        "(2+3)*4 - 1",
        "2 ** 3",  # exponentiation supported by Python eval
        "import os",
        "1 + foo",
    ]

    for c in cases:
        out = evaluate({"expression": c})
        print(f"{c!r} -> {out}")


if __name__ == '__main__':
    run_tests()
