import os

from source.files import read_file, write_file

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

