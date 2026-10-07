from lark import Transformer

from source.models import *
from source.printing import exit_with_error


def _flatten(items) -> list:
    result = []
    for item in items:
        if isinstance(item, list):
            result.extend(item)
        else:
            result.append(item)
    return result


class LssTransformer(Transformer):

    # Top level

    def start(self, items):
        return _flatten(items)

    def theme_decl(self, items):
        return Theme(name=str(items[0]))

    def widget_decl(self, items):
        return CustomWidget(type=str(items[0]), class_symbol=str(items[1]))

    def config_decl(self, items):
        return Config(fields=list(items))

    def config_field(self, items):
        return ConfigField(name=str(items[0]), type=str(items[1]), default=items[2])

    def variable_decl(self, items):
        return Variable(name=str(items[0]), value=items[1])

    def transition_decl(self, items):
        return Transition(name=str(items[0]), properties=list(items[1:]))

    def cif_entries(self, items):
        macro = str(items[0])
        entries = _flatten(items[1:])
        for entry in entries:
            if isinstance(entry, (Theme, Config, CustomWidget)):
                exit_with_error(f"@cif ({macro}) can't contain @theme, @config or @widget")
            entry.guards.insert(0, macro)
        return entries

    # Styles

    def style_decl(self, items):
        return Style(name=str(items[0]), items=list(items[1:]))

    def property(self, items):
        return Property(name=str(items[0]), values=list(items[1:]))

    def style_if(self, items):
        else_items = items[-1] if items[-1] is not None else []
        return StyleIf(condition=items[0], then_items=list(items[1:-1]), else_items=else_items)

    def style_else(self, items):
        return list(items)

    def style_cif(self, items):
        return StyleCif(macro=str(items[0]), items=list(items[1:]))

    # Apply rules

    def apply_decl(self, items):
        selectors = [item for item in items if isinstance(item, Selector)]
        rule_items = [item for item in items if not isinstance(item, Selector)]
        return ApplyRule(selectors=selectors, items=rule_items)

    def selector(self, items):
        return Selector(compounds=list(items))

    def _index(self, token):
        if token is None:
            return None
        if "." in str(token):
            exit_with_error(f"Child index must be a whole number: {token}")
        return int(str(token))

    def compound_named(self, items):
        return Compound(type=str(items[0]), index=self._index(items[1]))

    def compound_any(self, items):
        return Compound(type=None, index=self._index(items[0]))

    def apply_style(self, items):
        return ApplyStyle(style=str(items[0]), targets=list(items[1:]))

    def target(self, items):
        kind = str(items[0])
        name = str(items[1]) if items[1] is not None else None
        if kind == "default":
            if name is not None:
                exit_with_error(f"Unexpected target: default.{name}")
        elif kind not in ("part", "state") or name is None:
            exit_with_error(f"Invalid target '{kind}{'.' + name if name else ''}': expected default, part.<name> or state.<name>")
        return Target(kind=kind, name=name)

    def apply_include(self, items):
        return ApplyInclude(selector=items[0])

    def apply_if(self, items):
        else_items = items[-1] if items[-1] is not None else []
        return ApplyIf(condition=items[0], then_items=list(items[1:-1]), else_items=else_items)

    def apply_else(self, items):
        return list(items)

    def apply_cif(self, items):
        return ApplyCif(macro=str(items[0]), items=list(items[1:]))

    # Expressions

    def or_op(self, items):
        return BinOp("||", items[0], items[1])

    def and_op(self, items):
        return BinOp("&&", items[0], items[1])

    def eq(self, items):
        return BinOp("==", items[0], items[1])

    def ne(self, items):
        return BinOp("!=", items[0], items[1])

    def bitor(self, items):
        return BinOp("|", items[0], items[1])

    def add(self, items):
        return BinOp("+", items[0], items[1])

    def sub(self, items):
        return BinOp("-", items[0], items[1])

    def mul(self, items):
        return BinOp("*", items[0], items[1])

    def div(self, items):
        return BinOp("/", items[0], items[1])

    def neg(self, items):
        return Unary("-", items[0])

    def not_op(self, items):
        return Unary("!", items[0])

    def dp(self, items):
        return Dp(int(str(items[0])[:-2]))

    def percent(self, items):
        return Percent(int(str(items[0])[:-1]))

    def number(self, items):
        return Number(str(items[0]))

    def color(self, items):
        hex_value = str(items[0])[1:]
        if len(hex_value) == 3:
            hex_value = "".join(c * 2 for c in hex_value)
        return Color(hex_value.upper())

    def var_ref(self, items):
        return VarRef(str(items[0]))

    def config_ref(self, items):
        return ConfigRef(str(items[0])[1:])

    def string(self, items):
        return String(str(items[0])[1:-1])

    def call(self, items):
        args = [item for item in items[1:] if item is not None]
        return Call(name=str(items[0]), args=args)

    def ident(self, items):
        return Ident(str(items[0]))
