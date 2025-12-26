from dataclasses import dataclass
from enum import Enum

from source.printing import exit_with_error

@dataclass
class Theme:
    name: str = "unnamed"

@dataclass
class Property:
    name: str
    type: str
    value: str

@dataclass
class Style:
    name: str
    properties: list

@dataclass
class Class:
    name: str
    styles: dict # maps a style name onto a list of states

@dataclass
class Color:
    red: int
    green: int
    blue: int

class VariableType(Enum):
    COLOR = 0,
    SIGNED_INT = 1,
    BOOLEAN = 2,
    SIGNED_NUMBER = 3,
    VARIABLE = 4,
    ESCAPED_STRING = 5,
    TEXT_ALIGNMENT = 6,
    DP = 7

@dataclass
class Variable:
    name: str
    type: VariableType
    value: object

def to_variable_type(text: str) -> VariableType:
    if text == "COLOR":
        return VariableType.COLOR
    elif text == "SIGNED_INT":
        return VariableType.SIGNED_INT
    elif text == "BOOLEAN":
        return VariableType.BOOLEAN
    elif text == "SIGNED_NUMBER":
        return VariableType.SIGNED_NUMBER
    elif text == "ESCAPED_STRING":
        return VariableType.ESCAPED_STRING
    elif text == "VARIABLE":
        return VariableType.VARIABLE
    elif text == "DP":
        return VariableType.DP
    elif text == "TEXT_ALIGNMENT":
        return VariableType.TEXT_ALIGNMENT
    else:
        exit_with_error(f"VariableType not supported: {text}")
        return None
