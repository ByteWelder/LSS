import os

from lark import Lark

from source import code
from source.files import *
from source.models import *
from source.transformer import LssTransformer

def templatize(text: str, parameters: dict):
    result = text
    for key in parameters.keys():
        result = result.replace(key, parameters[key])
    return result

# Convert a Variable name to C code

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
            defines += f"#define {code.variable_name(item)} {code.variable_value(item)}\n"
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
