import os
from typing import List, Dict

from lark import Lark

from source import code
from source.files import *
from source.models import *
from source.transformer import LssTransformer

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

    def __init__(self):
        # Raw data buckets
        self.__styles = list()
        self.__variables = dict()
        self.__theme = None
        # Outputs
        self.defines_code = ""
        self.style_declarations_code = ""
        self.style_init_code = ""
        self.theme_name = None

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
            lines.append(f"#define {code.variable_name(variable)} {code.variable_value(variable)}")
        self.defines_code = "\n".join(lines)

    def __generate_style_declarations_code(self):
        # Style declarations
        style_declaration_list = list()
        for style in self.__styles:
            if style.state is None:
                style_declaration_list.append(f"\tlv_style_t {style.name};")
        self.style_declarations_code = "\n".join(style_declaration_list)

    def __generate_style_init_code(self):
        for style in self.__styles:
            # TODO
            None

    def process(self, transformed: list):
        self.__fill_cache(transformed)
        self.__generate_defines_code()
        self.__generate_style_declarations_code()
        self.__generate_style_init_code()
        self.theme_name = self.__theme.name

def templatize(text: str, parameters: dict):
    result = text
    for key in parameters.keys():
        result = result.replace(key, parameters[key])
    return result


def write_templates(code_generator, output_folder):
    theme_h_template = read_file("templates/theme.h.tpl")
    theme_c_template = read_file("templates/theme.c.tpl")
    template_parameters = {
        "{{DEFINE_CONSTANTS}}" : code_generator.defines_code,
        "{{THEME_NAME_LOWER}}" : code_generator.theme_name.lower(),
        "{{THEME_NAME_UPPER}}" : code_generator.theme_name.upper(),
        "{{STYLE_DECLARATIONS}}" : code_generator.style_declarations_code,
        "{{STYLE_INIT}}" : code_generator.style_init_code,
        "{{INIT_FUNCTION_BODY}}" : "// TODO"
    }
    theme_h_processed = templatize(theme_h_template, template_parameters)
    theme_c_processed = templatize(theme_c_template, template_parameters)
    if not os.path.isdir(output_folder):
        os.mkdir(output_folder)
    write_file(f"{output_folder}/theme.h", theme_h_processed)
    write_file(f"{output_folder}/theme.c", theme_c_processed)


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
    # Parse the transformed tree and generate code
    code_generator = CodeGenerator()
    code_generator.process(transformed)
    write_templates(code_generator, "build")
