from typing import List


def validate_constraints(constraints: List[str]) -> bool:
    return all(isinstance(value, str) and value for value in constraints)
