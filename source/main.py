import os
from enum import Enum
from typing import List

from lark import Lark, Token, Tree
from lark import Transformer
from dataclasses import dataclass

from source.files import *
from source.printing import *

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
    state: str
    properties: list

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
    ESCAPED_STRING = 5

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
    else:
        exit_with_error(f"VariableType not supported: {text}")
        return None

@dataclass
class Variable:
    name: str
    type: VariableType
    value: object

class LssTransformer(Transformer):
    # Flatten the start node into a list
    def start(self, items):
        return items
    def variable_declaration(self, items: List[Token]):
        name_variable_token: Token = items[0]
        name = name_variable_token.value
        value_token: Token = items[1]
        value_type = to_variable_type(value_token.type)
        return Variable(name = name, type = value_type, value = value_token.value)
    def class_declaration(self, items):
        name_token: Token = items[0]
        name = name_token.value
        if name == "theme":
            # Parse properties
            properties = list()
            theme = Theme()
            if len(items) > 2:
                for item in items[2:]:
                    tree: Tree = item
                    property_name_token = tree.children[0]
                    property_value_token = tree.children[1]
                    if property_name_token.value == "name" and property_value_token.type == "ESCAPED_STRING":
                        theme.name = property_value_token.value[1:-1]
            return theme
        else:
            # Parse state
            state_token: Token  = items[1]
            if state_token == None:
                state = None
            else:
                state = state_token.value
            # Parse properties
            properties = list()
            if len(items) > 2:
                for item in items[2:]:
                    tree: Tree = item
                    property_name_token = tree.children[0]
                    property_value_token = tree.children[1]
                    property = Property(name = property_name_token.value, type = property_value_token.type, value = property_value_token.value)
                    properties.append(property)
            # Combine
            return Style(name = name, state = state, properties = properties)

def templatize(text: str, parameters: dict):
    result = text
    for key in parameters.keys():
        result = result.replace(key, parameters[key])
    return result

# Convert a Variable name to C code
def variable_name(variable: Variable):
    return variable.name[1:].replace("-", "_")

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

def main(lss_file_path: str, verbose: bool):
    lark_data = read_file("grammar.lark")
    lss_data = read_file(lss_file_path)
    lark = Lark(lark_data)
    lss_parsed = lark.parse(lss_data)
    if verbose:
        print(lss_parsed.pretty())
    transformed = LssTransformer().transform(lss_parsed)
    if verbose:
        for entry in transformed:
            print(entry)
    # Template
    defines = ""
    style_declarations = list()
    styles = list()
    theme: Theme = None
    for item in transformed:
        item_type = type(item)
        if item_type is Variable:
            defines += f"#define {variable_name(item)} {variable_value(item)}\n"
        elif item_type is Style:
            styles.append(item)
        elif item_type is Theme:
            theme = item
    for style in styles:
        if style.state is None:
            style_declarations.append(f"\tlv_style_t {style.name};")
    theme_h_template = read_file("templates/theme.h.tpl")
    theme_c_template = read_file("templates/theme.c.tpl")
    template_parameters = {
        "{{DEFINES}}" : defines,
        "{{STYLE_DECLARATIONS}}" : "\n".join(style_declarations),
        "{{THEME_NAME_LOWERCASE}}" : theme.name.lower(),
        "{{THEME_NAME_UPPERCASE}}" : theme.name.upper(),
        "{{INIT_FUNCTION_BODY}}" : "// TODO"
    }
    theme_h_template = templatize(theme_h_template, template_parameters)
    theme_c_template = templatize(theme_c_template, template_parameters)
    if not os.path.isdir("build"):
        os.mkdir("build")
    write_file("build/theme.h", theme_h_template)
    write_file("build/theme.c", theme_c_template)
