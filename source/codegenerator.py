from typing import Dict, List, Optional

from source.expressions import EmitContext, config_member, emit, variable_macro
from source.models import *
from source.printing import camel_to_snake, exit_with_error, print_warning
from source.selectors import ApplyGenerator, emit_guarded, guard_condition

CONFIG_TYPES = {
    "bool": "bool",
    "color": "lv_color_t",
    "int": "int32_t",
    "opa": "lv_opa_t",
    "font": "const lv_font_t *",
}

# Config fields with these names are also stored in lv_theme_t, so lv_theme_get_*() works
CONFIG_BASE_FIELDS = {
    "colorPrimary": ["color_primary"],
    "colorSecondary": ["color_secondary"],
    "font": ["font_small", "font_normal", "font_large"],
    "fontSmall": ["font_small"],
    "fontNormal": ["font_normal"],
    "fontLarge": ["font_large"],
}

TRANSITION_PROPERTIES = {"props", "path", "duration", "delay"}


def _style_guard_condition(explicit: List[str], usages: Optional[list]) -> Optional[str]:
    """Combine explicit @cif guards (AND) with the guards of all places that apply the style (OR)."""
    terms = []
    if explicit:
        terms.append(guard_condition(explicit))
    if usages:
        # Macros that are already required by the explicit guards are redundant
        usages = [usage - frozenset(explicit) for usage in usages]
    if usages and all(usages):
        # Drop guards that are implied by a weaker guard
        unique = sorted(set(usages), key=lambda g: (len(g), sorted(g)))
        minimal = [g for g in unique if not any(other < g for other in unique)]
        alternatives = [guard_condition(g) for g in minimal]
        if len(alternatives) == 1:
            terms.append(alternatives[0])
        else:
            terms.append(" || ".join(f"({a})" if " && " in a else a for a in alternatives))
    if not terms:
        return None
    if len(terms) == 1:
        return terms[0]
    return " && ".join(f"({t})" if " || " in t else t for t in terms)


def _emit_if_guarded(lines: List[str], condition: Optional[str], body: List[str]):
    if condition:
        lines.append(f"#if {condition}")
    lines.extend(body)
    if condition:
        lines.append("#endif")


class CodeGenerator:

    def __init__(self, entries: list, name_override: Optional[str] = None):
        self.__theme_name: Optional[str] = None
        self.__config_fields: Dict[str, ConfigField] = {}
        self.__variables: Dict[str, Variable] = {}
        self.__transitions: Dict[str, Transition] = {}
        self.__styles: Dict[str, Style] = {}
        self.__rules: List[ApplyRule] = []
        self.__custom_widgets: Dict[str, str] = {}
        self.__collect(entries)
        if name_override is not None:
            self.__theme_name = name_override
        if self.__theme_name is None:
            exit_with_error("Missing theme name. Add: @theme <name>;")
        self.__context = EmitContext(
            variables=self.__variables,
            config_fields=self.__config_fields,
            transitions=set(self.__transitions)
        )
        self.__static_context = EmitContext(
            variables=self.__variables,
            config_fields=self.__config_fields,
            has_theme=False
        )
        # Outputs
        self.theme_name = self.__theme_name.replace("-", "_").lower()
        apply_generator = ApplyGenerator(self.__rules, self.__styles, self.__context, self.__custom_widgets)
        self.apply_code = apply_generator.generate()
        self.__style_guards = {style.name: self.__compute_style_guard(style, apply_generator.style_usages) for style in self.__styles.values()}
        self.defines_code = self.__generate_defines()
        self.config_fields_code = self.__generate_config_fields()
        self.config_init_code = self.__generate_config_init()
        self.config_equals_code = self.__generate_config_equals()
        self.config_base_code = self.__generate_config_base()
        self.style_fields_code = self.__generate_style_fields()
        self.transition_fields_code = self.__generate_transition_fields()
        self.style_init_code = self.__generate_style_init()

    def __collect(self, entries: list):
        for entry in entries:
            if isinstance(entry, Theme):
                if self.__theme_name is not None:
                    exit_with_error("Duplicate @theme declaration")
                self.__theme_name = entry.name
            elif isinstance(entry, Config):
                for config_field in entry.fields:
                    if config_field.name in self.__config_fields:
                        exit_with_error(f"Duplicate config field: {config_field.name}")
                    if config_field.type not in CONFIG_TYPES:
                        exit_with_error(f"Unknown type '{config_field.type}' for config field '{config_field.name}' (expected one of: {', '.join(CONFIG_TYPES)})")
                    self.__config_fields[config_field.name] = config_field
            elif isinstance(entry, Variable):
                if entry.name in self.__variables:
                    exit_with_error(f"Duplicate variable: {entry.name}")
                self.__variables[entry.name] = entry
            elif isinstance(entry, Transition):
                if entry.name in self.__transitions:
                    exit_with_error(f"Duplicate transition: {entry.name}")
                self.__transitions[entry.name] = entry
            elif isinstance(entry, Style):
                if entry.name in self.__styles:
                    exit_with_error(f"Duplicate style: {entry.name}")
                self.__styles[entry.name] = entry
            elif isinstance(entry, ApplyRule):
                self.__rules.append(entry)
            elif isinstance(entry, CustomWidget):
                if entry.type in self.__custom_widgets:
                    exit_with_error(f"Duplicate widget: {entry.type}")
                self.__custom_widgets[entry.type] = entry.class_symbol
            else:
                exit_with_error(f"Unexpected entry: {entry}")

    # Defines

    def __generate_defines(self) -> str:
        lines = []
        for class_symbol in self.__custom_widgets.values():
            lines.append(f"extern const lv_obj_class_t {class_symbol};")
        if lines:
            lines.append("")
        for variable in self.__variables.values():
            value = emit(variable.value, self.__context)
            if not isinstance(variable.value, (Number, Color, Ident, VarRef)):
                value = f"({value})"
            emit_guarded(lines, variable.guards, [f"#define {variable_macro(variable.name)} {value}"])
        return "\n".join(lines)

    # Config

    def __generate_config_fields(self) -> str:
        if not self.__config_fields:
            return "    char reserved;"
        lines = []
        for config_field in self.__config_fields.values():
            lines.append(f"    {CONFIG_TYPES[config_field.type]} {config_member(config_field.name)};")
        return "\n".join(lines)

    def __generate_config_init(self) -> str:
        lines = ["    lv_memzero(config, sizeof(*config));"]
        for config_field in self.__config_fields.values():
            if config_field.default is not None:
                value = emit(config_field.default, self.__static_context)
                lines.append(f"    config->{config_member(config_field.name)} = {value};")
        return "\n".join(lines)

    def __generate_config_equals(self) -> str:
        terms = []
        for config_field in self.__config_fields.values():
            member = config_member(config_field.name)
            if config_field.type == "color":
                terms.append(f"lv_color_eq(a->{member}, b->{member})")
            else:
                terms.append(f"a->{member} == b->{member}")
        if not terms:
            return "    LV_UNUSED(a);\n    LV_UNUSED(b);\n    return true;"
        return "    return " + " &&\n           ".join(terms) + ";"

    def __generate_config_base(self) -> str:
        lines = []
        assigned = set()
        for name, base_fields in CONFIG_BASE_FIELDS.items():
            config_field = self.__config_fields.get(name)
            if config_field is None:
                continue
            for base_field in base_fields:
                lines.append(f"    theme->base.{base_field} = config->{config_member(name)};")
                assigned.add(base_field)
        for base_field in ("font_small", "font_normal", "font_large"):
            if base_field not in assigned:
                lines.append(f"    theme->base.{base_field} = LV_FONT_DEFAULT;")
        return "\n".join(lines)

    # Styles

    @staticmethod
    def __compute_style_guard(style: Style, style_usages: dict) -> Optional[str]:
        usages = style_usages.get(style.name)
        if usages is None:
            print_warning(f"Style '{style.name}' is never applied")
        return _style_guard_condition(style.guards, usages)

    def __generate_style_fields(self) -> str:
        lines = []
        for style in self.__styles.values():
            _emit_if_guarded(lines, self.__style_guards[style.name], [f"    lv_style_t {style.name};"])
        return "\n".join(lines)

    def __emit_style_items(self, style_variable: str, items: list, indent: str) -> List[str]:
        lines = []
        for item in items:
            if isinstance(item, Property):
                setter = camel_to_snake(item.name)
                context = self.__context.with_property(item.name)
                args = ", ".join(emit(value, context) for value in item.values)
                lines.append(f"{indent}lv_style_set_{setter}({style_variable}, {args});")
            elif isinstance(item, StyleIf):
                condition = emit(item.condition, self.__context)
                lines.append(f"{indent}if({condition}) {{")
                lines.extend(self.__emit_style_items(style_variable, item.then_items, indent + "    "))
                if item.else_items:
                    lines.append(f"{indent}}}")
                    lines.append(f"{indent}else {{")
                    lines.extend(self.__emit_style_items(style_variable, item.else_items, indent + "    "))
                lines.append(f"{indent}}}")
            elif isinstance(item, StyleCif):
                emit_guarded(lines, [item.macro], self.__emit_style_items(style_variable, item.items, indent))
            else:
                exit_with_error(f"Unexpected style item: {item}")
        return lines

    # Transitions

    def __generate_transition_fields(self) -> str:
        lines = []
        for transition in self.__transitions.values():
            name = transition.name.replace("-", "_")
            emit_guarded(lines, transition.guards, [f"    lv_style_transition_dsc_t trans_{name};"])
        return "\n".join(lines)

    def __generate_transition_init(self, transition: Transition) -> List[str]:
        properties = {}
        for transition_property in transition.properties:
            if transition_property.name not in TRANSITION_PROPERTIES:
                exit_with_error(f"Unknown transition property '{transition_property.name}' (expected one of: {', '.join(sorted(TRANSITION_PROPERTIES))})")
            properties[transition_property.name] = transition_property.values
        if "props" not in properties or "duration" not in properties:
            exit_with_error(f"Transition '{transition.name}' requires 'props' and 'duration'")
        name = transition.name.replace("-", "_")
        style_props = []
        for value in properties["props"]:
            if not isinstance(value, Ident):
                exit_with_error(f"Transition '{transition.name}': props must be style property names")
            style_props.append("LV_STYLE_" + camel_to_snake(value.name).upper())
        path = properties.get("path", [Ident("linear")])
        if len(path) != 1 or not isinstance(path[0], Ident):
            exit_with_error(f"Transition '{transition.name}': path must be an animation path name, e.g. linear")
        path_cb = "lv_anim_path_" + path[0].name.replace("-", "_")
        duration = emit(properties["duration"][0], self.__context)
        delay = emit(properties.get("delay", [Number("0")])[0], self.__context)
        props_variable = f"trans_{name}_props"
        body = [
            f"    static const lv_style_prop_t {props_variable}[] = {{",
            f"        {', '.join(style_props)},",
            "        0",
            "    };",
            f"    lv_style_transition_dsc_init(&theme->trans_{name}, {props_variable}, {path_cb}, {duration}, {delay}, NULL);",
        ]
        lines = []
        emit_guarded(lines, transition.guards, body)
        return lines

    def __generate_style_init(self) -> str:
        blocks = []
        for transition in self.__transitions.values():
            blocks.append("\n".join(self.__generate_transition_init(transition)))
        for style in self.__styles.values():
            style_variable = f"&theme->styles.{style.name}"
            body = [f"    style_init_reset({style_variable});"]
            body.extend(self.__emit_style_items(style_variable, style.items, "    "))
            lines = []
            _emit_if_guarded(lines, self.__style_guards[style.name], body)
            blocks.append("\n".join(lines))
        return "\n\n".join(blocks)
