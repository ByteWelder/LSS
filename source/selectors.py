from typing import Dict, FrozenSet, List, Optional

from source.expressions import EmitContext, emit
from source.lvgl_tables import PARTS, STATES, widget_class, widget_macros
from source.models import *
from source.printing import exit_with_error

# A guard is a set of macros that must all be enabled. An empty set means "always enabled".
Guard = FrozenSet[str]


def guard_condition(macros) -> str:
    return " && ".join(sorted(macros))


def emit_guarded(lines: List[str], macros, body: List[str]):
    if macros:
        lines.append(f"#if {guard_condition(macros)}")
    lines.extend(body)
    if macros:
        lines.append("#endif")


def target_selector(targets: List[Target]) -> str:
    values = []
    for target in targets:
        if target.kind == "default":
            continue
        table = PARTS if target.kind == "part" else STATES
        value = table.get(target.name)
        if value is None:
            exit_with_error(f"Unknown {target.kind}: {target.name} (expected one of: {', '.join(table)})")
        values.append(value)
    return " | ".join(values) if values else "0"


def selector_macros(selector: Selector, custom_widgets: Dict[str, str]) -> Guard:
    macros = set()
    for compound in selector.compounds:
        if compound.type is not None and compound.type != "null":
            macros.update(widget_macros(compound.type, custom_widgets))
    return frozenset(macros)


def _ancestor(depth: int) -> str:
    if depth == 0:
        return "obj"
    if depth == 1:
        return "parent"
    return f"lss_ancestor(obj, {depth})"


def selector_condition(selector: Selector, custom_widgets: Dict[str, str]) -> Optional[str]:
    """C condition for everything except the target's type, which is checked by the enclosing branch."""
    compounds = selector.compounds
    last = len(compounds) - 1
    conditions = []
    for i, compound in enumerate(compounds):
        depth = last - i
        ancestor = _ancestor(depth)
        if compound.type == "null":
            if i != 0:
                exit_with_error(f"'null' must be the first part of a selector: {selector.text()}")
            if compound.index is not None:
                exit_with_error(f"'null' can't have a child index: {selector.text()}")
            conditions.append(f"{ancestor} == NULL")
        elif compound.type is None:
            # A typed outer compound already implies this ancestor exists
            has_typed_outer = any(c.type not in (None, "null") for c in compounds[:i])
            if depth > 0 and not has_typed_outer:
                conditions.append(f"{ancestor} != NULL")
        elif depth > 0:
            conditions.append(f"lv_obj_check_type({ancestor}, &{widget_class(compound.type, custom_widgets)})")
        if compound.index is not None:
            conditions.append(f"lss_is_child({_ancestor(depth + 1)}, {compound.index}, {ancestor})")
    return " && ".join(conditions) if conditions else None


class ApplyGenerator:

    def __init__(self, rules: List[ApplyRule], styles: Dict[str, Style], context: EmitContext, custom_widgets: Dict[str, str]):
        self.__rules = rules
        self.__custom_widgets = custom_widgets
        self.__styles = styles
        self.__context = context
        # Maps a style name to all guards under which it is applied
        self.style_usages: Dict[str, List[Guard]] = {}

    # Include resolution

    def __find_rule(self, selector: Selector) -> ApplyRule:
        text = selector.text()
        for rule in self.__rules:
            if any(candidate.text() == text for candidate in rule.selectors):
                return rule
        exit_with_error(f"@include: no rule found for selector '{text}'")

    def __resolve_items(self, items: list, include_stack: List[str]) -> list:
        resolved = []
        for item in items:
            if isinstance(item, ApplyInclude):
                text = item.selector.text()
                if text in include_stack:
                    exit_with_error(f"@include cycle: {' -> '.join(include_stack + [text])}")
                rule = self.__find_rule(item.selector)
                included = self.__resolve_items(rule.items, include_stack + [text])
                for macro in reversed(rule.guards):
                    included = [ApplyCif(macro=macro, items=included)]
                resolved.extend(included)
            elif isinstance(item, ApplyIf):
                resolved.append(ApplyIf(
                    condition=item.condition,
                    then_items=self.__resolve_items(item.then_items, include_stack),
                    else_items=self.__resolve_items(item.else_items, include_stack)
                ))
            elif isinstance(item, ApplyCif):
                resolved.append(ApplyCif(macro=item.macro, items=self.__resolve_items(item.items, include_stack)))
            else:
                resolved.append(item)
        return resolved

    # Code generation

    def __emit_items(self, items: list, guard: Guard, indent: str) -> List[str]:
        lines = []
        for item in items:
            if isinstance(item, ApplyStyle):
                if item.style not in self.__styles:
                    exit_with_error(f"Unknown style: {item.style}")
                self.style_usages.setdefault(item.style, []).append(guard)
                lines.append(f"{indent}lv_obj_add_style(obj, &theme->styles.{item.style}, {target_selector(item.targets)});")
            elif isinstance(item, ApplyIf):
                condition = emit(item.condition, self.__context)
                lines.append(f"{indent}if({condition}) {{")
                lines.extend(self.__emit_items(item.then_items, guard, indent + "    "))
                if item.else_items:
                    lines.append(f"{indent}}}")
                    lines.append(f"{indent}else {{")
                    lines.extend(self.__emit_items(item.else_items, guard, indent + "    "))
                lines.append(f"{indent}}}")
            elif isinstance(item, ApplyCif):
                emit_guarded(lines, {item.macro}, self.__emit_items(item.items, guard | {item.macro}, indent))
            else:
                exit_with_error(f"Unexpected apply item: {item}")
        return lines

    def __emit_conditional(self, selector: Selector, rule: ApplyRule, outer_guard: Guard, indent: str) -> List[str]:
        guard = outer_guard | selector_macros(selector, self.__custom_widgets) | frozenset(rule.guards)
        items = self.__resolve_items(rule.items, [selector.text()])
        body = [f"{indent}/* {selector.text()} */"]
        condition = selector_condition(selector, self.__custom_widgets)
        if condition is not None:
            body.append(f"{indent}if({condition}) {{")
            body.extend(self.__emit_items(items, guard, indent + "    "))
            body.append(f"{indent}    return;")
            body.append(f"{indent}}}")
        else:
            body.extend(self.__emit_items(items, guard, indent))
            body.append(f"{indent}return;")
        lines = []
        emit_guarded(lines, guard - outer_guard, body)
        return lines

    def generate(self) -> str:
        lines = []
        wildcard_entries = []
        typed_entries: Dict[str, list] = {}
        for rule in self.__rules:
            for selector in rule.selectors:
                target = selector.target()
                if target.type == "null":
                    exit_with_error(f"A selector can't target 'null': {selector.text()}")
                if target.type is None:
                    wildcard_entries.append((selector, rule))
                else:
                    typed_entries.setdefault(target.type, []).append((selector, rule))

        for selector, rule in wildcard_entries:
            if selector_condition(selector, self.__custom_widgets) is None:
                exit_with_error(f"Selector matches every object: {selector.text()}")
            lines.extend(self.__emit_conditional(selector, rule, frozenset(), "    "))

        for widget_type, entries in typed_entries.items():
            unconditional = [(s, r) for s, r in entries if selector_condition(s, self.__custom_widgets) is None]
            conditional = [(s, r) for s, r in entries if selector_condition(s, self.__custom_widgets) is not None]
            if len(unconditional) > 1:
                exit_with_error(f"Multiple rules for '{widget_type}'. Merge them or use @include.")
            branch_guard = frozenset(widget_macros(widget_type, self.__custom_widgets))
            body = [f"    if(lv_obj_check_type(obj, &{widget_class(widget_type, self.__custom_widgets)})) {{"]
            for selector, rule in conditional:
                body.extend(self.__emit_conditional(selector, rule, branch_guard, "        "))
            if unconditional:
                selector, rule = unconditional[0]
                body.extend(self.__emit_conditional(selector, rule, branch_guard, "        "))
            else:
                body.append("        return;")
            body.append("    }")
            emit_guarded(lines, branch_guard, body)
        return "\n".join(lines)
