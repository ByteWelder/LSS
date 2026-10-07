from dataclasses import dataclass, field
from typing import List, Optional, Union

# Expressions

@dataclass
class Number:
    value: str

@dataclass
class Dp:
    value: int

@dataclass
class Percent:
    value: int

@dataclass
class Color:
    hex: str  # 6 hex digits, no prefix

@dataclass
class VarRef:
    name: str  # includes "@"

@dataclass
class ConfigRef:
    name: str  # without "$"

@dataclass
class String:
    value: str  # unquoted

@dataclass
class Ident:
    name: str

@dataclass
class Call:
    name: str
    args: list

@dataclass
class BinOp:
    op: str
    left: object
    right: object

@dataclass
class Unary:
    op: str
    operand: object

Expr = Union[Number, Dp, Percent, Color, VarRef, ConfigRef, String, Ident, Call, BinOp, Unary]

# Declarations

@dataclass
class Theme:
    name: str

@dataclass
class CustomWidget:
    type: str
    class_symbol: str

@dataclass
class ConfigField:
    name: str
    type: str
    default: Optional[object]

@dataclass
class Config:
    fields: List[ConfigField]

@dataclass
class Variable:
    name: str
    value: object
    guards: List[str] = field(default_factory=list)

@dataclass
class Property:
    name: str
    values: list

@dataclass
class StyleIf:
    condition: object
    then_items: list
    else_items: list

@dataclass
class StyleCif:
    macro: str
    items: list

@dataclass
class Style:
    name: str
    items: list
    guards: List[str] = field(default_factory=list)

@dataclass
class Transition:
    name: str
    properties: List[Property]
    guards: List[str] = field(default_factory=list)

@dataclass
class Compound:
    type: Optional[str]  # None matches any object
    index: Optional[int]

@dataclass
class Selector:
    compounds: List[Compound]

    def target(self) -> Compound:
        return self.compounds[-1]

    def text(self) -> str:
        parts = []
        for compound in self.compounds:
            name = compound.type if compound.type is not None else "*"
            if compound.index is not None:
                name += f"[{compound.index}]"
            parts.append(name)
        return " > ".join(parts)

@dataclass
class Target:
    kind: str  # "default", "part" or "state"
    name: Optional[str]

@dataclass
class ApplyStyle:
    style: str
    targets: List[Target]

@dataclass
class ApplyInclude:
    selector: Selector

@dataclass
class ApplyIf:
    condition: object
    then_items: list
    else_items: list

@dataclass
class ApplyCif:
    macro: str
    items: list

@dataclass
class ApplyRule:
    selectors: List[Selector]
    items: list
    guards: List[str] = field(default_factory=list)
