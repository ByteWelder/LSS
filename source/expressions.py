from dataclasses import dataclass, field
from typing import Dict, Optional, Set

from source.lvgl_tables import PALETTES, resolve_enum
from source.models import *
from source.printing import camel_to_snake, exit_with_error

DISPLAY_SIZES = {
    "small": "DISP_SMALL",
    "medium": "DISP_MEDIUM",
    "large": "DISP_LARGE",
}


def variable_macro(name: str) -> str:
    return name[1:].replace("-", "_").upper()


def config_member(name: str) -> str:
    return camel_to_snake(name)


@dataclass
class EmitContext:
    variables: Dict[str, Variable]
    config_fields: Dict[str, ConfigField]
    transitions: Set[str] = field(default_factory=set)
    # The style property the expression is assigned to, used to resolve identifiers like "top" or "center"
    property_name: Optional[str] = None
    # False when the expression is evaluated without a theme instance (e.g. config defaults)
    has_theme: bool = True

    def with_property(self, property_name: Optional[str]) -> "EmitContext":
        return EmitContext(self.variables, self.config_fields, self.transitions, property_name, self.has_theme)


def _require_theme(context: EmitContext, what: str):
    if not context.has_theme:
        exit_with_error(f"{what} can't be used here because it depends on the theme instance")


def _wrap(expr, text: str) -> str:
    if isinstance(expr, (BinOp, Unary)) or (isinstance(expr, Call) and expr.name in ("if", "by-size", "contrast")):
        return f"({text})"
    return text


def _palette(name_expr, function_name: str) -> str:
    if not isinstance(name_expr, Ident) or name_expr.name not in PALETTES:
        exit_with_error(f"{function_name}() expects a palette name ({', '.join(PALETTES)})")
    return "LV_PALETTE_" + name_expr.name.replace("-", "_").upper()


def _expect_args(call: Call, count: int):
    if len(call.args) != count:
        exit_with_error(f"{call.name}() expects {count} argument(s), got {len(call.args)}")


def _opa(value: int) -> str:
    if value < 0 or value > 100:
        exit_with_error(f"Opacity out of range: {value}%")
    if value % 10 == 0:
        return f"LV_OPA_{value}"
    return str(round(value * 255 / 100))


def _emit_call(call: Call, context: EmitContext) -> str:
    name = call.name
    if name == "palette":
        _expect_args(call, 1)
        return f"lv_palette_main({_palette(call.args[0], name)})"
    if name in ("lighten", "darken"):
        _expect_args(call, 2)
        return f"lv_palette_{name}({_palette(call.args[0], name)}, {emit(call.args[1], context)})"
    if name == "mix":
        # The amount is the share of the first color
        _expect_args(call, 3)
        first, second, amount = (emit(arg, context) for arg in call.args)
        return f"lv_color_mix({first}, {second}, {amount})"
    if name == "contrast":
        # Black or white, whichever is readable on the given background color
        _expect_args(call, 1)
        return f"lv_color_luminance({emit(call.args[0], context)}) > 128 ? lv_color_black() : lv_color_white()"
    if name == "opa":
        _expect_args(call, 1)
        if not isinstance(call.args[0], Number) or "." in call.args[0].value:
            exit_with_error("opa() expects a whole number")
        return _opa(int(call.args[0].value))
    if name == "pct":
        _expect_args(call, 1)
        return f"lv_pct({emit(call.args[0], context)})"
    if name == "symbol":
        _expect_args(call, 1)
        if not isinstance(call.args[0], Ident):
            exit_with_error("symbol() expects a symbol name, e.g. symbol(ok)")
        return "LV_SYMBOL_" + call.args[0].name.replace("-", "_").upper()
    if name == "raw":
        _expect_args(call, 1)
        if not isinstance(call.args[0], String):
            exit_with_error('raw() expects a string, e.g. raw("LV_DPX(4)")')
        return call.args[0].value
    if name == "if":
        _expect_args(call, 3)
        condition, when_true, when_false = (emit(arg, context) for arg in call.args)
        return f"{condition} ? {when_true} : {when_false}"
    if name == "by-size":
        _expect_args(call, 3)
        _require_theme(context, "by-size()")
        small, medium, large = (_wrap(arg, emit(arg, context)) for arg in call.args)
        return f"theme->disp_size == DISP_LARGE ? {large} : theme->disp_size == DISP_MEDIUM ? {medium} : {small}"
    if name == "display":
        _expect_args(call, 1)
        _require_theme(context, "display()")
        size = call.args[0]
        if not isinstance(size, Ident) or size.name not in DISPLAY_SIZES:
            exit_with_error("display() expects small, medium or large")
        return f"theme->disp_size == {DISPLAY_SIZES[size.name]}"
    exit_with_error(f"Unknown function: {name}()")


def _emit_ident(ident: Ident, context: EmitContext) -> str:
    if ident.name == "dpi":
        _require_theme(context, "dpi")
        return "theme->disp_dpi"
    if context.property_name == "transition":
        if ident.name not in context.transitions:
            exit_with_error(f"Unknown transition: {ident.name}")
        return f"&theme->trans_{ident.name.replace('-', '_')}"
    value = resolve_enum(ident.name, context.property_name)
    if value is None:
        where = f" for property '{context.property_name}'" if context.property_name else ""
        exit_with_error(f"Unknown identifier{where}: {ident.name}")
    return value


def emit(expr, context: EmitContext) -> str:
    """Convert an expression to C code."""
    if isinstance(expr, Number):
        return expr.value
    if isinstance(expr, Dp):
        _require_theme(context, f"{expr.value}dp")
        return f"LV_DPX_CALC(theme->disp_dpi, {expr.value})"
    if isinstance(expr, Percent):
        return _opa(expr.value)
    if isinstance(expr, Color):
        return f"lv_color_hex(0x{expr.hex})"
    if isinstance(expr, VarRef):
        variable = context.variables.get(expr.name)
        if variable is None:
            exit_with_error(f"Unknown variable: {expr.name}")
        if not context.has_theme:
            # Validates that the variable doesn't depend on the theme instance
            emit(variable.value, context.with_property(None))
        return variable_macro(expr.name)
    if isinstance(expr, ConfigRef):
        if expr.name not in context.config_fields:
            exit_with_error(f"Unknown config field: ${expr.name}")
        _require_theme(context, f"${expr.name}")
        return f"theme->config.{config_member(expr.name)}"
    if isinstance(expr, String):
        exit_with_error(f'Strings are only allowed in raw(): "{expr.value}"')
    if isinstance(expr, Ident):
        return _emit_ident(expr, context)
    if isinstance(expr, Call):
        return _emit_call(expr, context)
    if isinstance(expr, Unary):
        return f"{expr.op}{_wrap(expr.operand, emit(expr.operand, context))}"
    if isinstance(expr, BinOp):
        left = _wrap(expr.left, emit(expr.left, context))
        right = _wrap(expr.right, emit(expr.right, context))
        return f"{left} {expr.op} {right}"
    exit_with_error(f"Unsupported expression: {expr}")
