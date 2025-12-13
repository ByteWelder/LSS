# Create C code
from typing import List, Dict
from source.printing import camel_to_snake

from source.models import *

def variable_name_str(name: str):
    return name[1:].replace("-", "_").upper()

def variable_name(variable: Variable):
    return variable_name_str(variable.name)

# Convert a Variable value to C code
def variable_value(variable: Variable):
    if variable.type == VariableType.BOOLEAN:
        return variable.value
    elif variable.type == VariableType.SIGNED_INT:
        return variable.value
    elif variable.type == VariableType.SIGNED_NUMBER:
        return variable.value
    elif variable.type == VariableType.COLOR:
        hex_value = variable.value.lstrip("#")
        hex_value_len = len(hex_value)
        if hex_value_len == 6:
            red = f"0x{hex_value[:2]}"
            green = f"0x{hex_value[2:4]}"
            blue = f"0x{hex_value[4:]}"
        elif hex_value_len == 3:
            red = f"0x{hex_value[:1]}0"
            green = f"0x{hex_value[1:2]}0"
            blue = f"0x{hex_value[2:]}0"
        else:
            exit_with_error(f"Incorrect color format for {variable.value}")
        return f"lv_color_make({red}, {green}, {blue})"
    elif variable.type == VariableType.VARIABLE:
        return variable.value[1:].replace("-", "_")
    elif variable.type == VariableType.ESCAPED_STRING:
        return variable.value[1:-1]
    exit_with_error(f"Unsupported variable type: {variable.type}")
    return None


class CodeGenerator:
    # Raw data buckets
    __styles: List[Style]
    __variables: Dict[str, Variable]
    __theme: Theme
    # Outputs
    defines_code: str
    style_declarations_code: str
    style_init_code: str
    theme_name: str

    def __init__(self, transformed: list):
        # Raw data buckets
        self.__styles = list()
        self.__variables = dict()
        self.__theme = None
        # Outputs
        self.defines_code = ""
        self.style_declarations_code = ""
        self.style_init_code = ""
        self.theme_name = None
        # Run
        self.__process(transformed)

    def __resolve_value(self, value: str):
        if value.startswith("@"):
            return variable_name_str(value)
        else:
            return value

    def __fill_cache(self, transformed: list):
        for item in transformed:
            item_type = type(item)
            if item_type is Variable:
                self.__variables[item.name] = item
            elif item_type is Style:
                self.__styles.append(item)
            elif item_type is Theme:
                self.__theme = item

    def __generate_defines_code(self):
        lines = list()
        for variable in self.__variables.values():
            lines.append(f"#define {variable_name(variable)} {variable_value(variable)}")
        self.defines_code = "\n".join(lines)

    def __generate_style_declarations_code(self):
        # Style declarations
        lines = list()
        for style in self.__styles:
            if style.state is None:
                lines.append(f"\tlv_style_t {style.name};")
        self.style_declarations_code = "\n".join(lines)

    def __generate_style_code(self, style: Style) -> str:
        lines = list()
        lines.append(f"\t// {style.name}")
        style_variable = f"&theme->styles.{style.name}"
        lines.append(f"\tstyle_init_reset({style_variable});")
        for property in style.properties:
            property_name = camel_to_snake(property.name)
            resolved_value = self.__resolve_value(property.value)
            lines.append(f"\tlv_style_set_{property_name}({style_variable}, {resolved_value});")
        return "\n".join(lines)

    def __generate_style_init_code(self):
        lines = list()
        for style in self.__styles:
            if style.state is None:
                lines.append(self.__generate_style_code(style))
        self.style_init_code = "\n\n".join(lines)

    def __process(self, transformed: list):
        self.__fill_cache(transformed)
        self.__generate_defines_code()
        self.__generate_style_declarations_code()
        self.__generate_style_init_code()
        self.theme_name = self.__theme.name