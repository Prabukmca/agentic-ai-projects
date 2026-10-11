from pydantic import BaseModel
from typing import Optional, Any, Dict
import re


class CalcInput(BaseModel):
    expression: str


class CalcOutput(BaseModel):
    result: Optional[float]
    success: bool
    error: Optional[str] = None


def evaluate(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a simple arithmetic expression safely.

    Input schema: {"expression": "1 + 2 * (3/4)"}
    Output schema: {"result": float|null, "success": bool, "error": str|null}
    """
    try:
        inp = CalcInput(**input_data)
    except Exception as e:
        return CalcOutput(result=None, success=False, error=f"invalid input: {e}").dict()

    # Allow only digits, whitespace, parentheses and basic operators
    if not re.fullmatch(r"[0-9+\-*/().\s]+", inp.expression):
        return CalcOutput(result=None, success=False, error="expression contains invalid characters").dict()

    try:
        # Evaluate in a restricted environment
        result = eval(inp.expression, {"__builtins__": None}, {})
        return CalcOutput(result=float(result), success=True, error=None).dict()
    except Exception as e:
        return CalcOutput(result=None, success=False, error=str(e)).dict()


if __name__ == "__main__":
    # quick manual test
    print(evaluate({"expression": "1+2*3"}))
