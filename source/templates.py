import os

from source.files import read_file, write_file

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")


def templatize(text: str, parameters: dict):
    result = text
    for key in parameters.keys():
        result = result.replace(key, parameters[key])
    return result


def render_templates(code_generator) -> dict:
    """Returns a dict that maps output file names onto their content"""
    template_parameters = {
        "{{THEME_NAME_LOWER}}": code_generator.theme_name.lower(),
        "{{THEME_NAME_UPPER}}": code_generator.theme_name.upper(),
        "{{DEFINES}}": code_generator.defines_code,
        "{{CONFIG_FIELDS}}": code_generator.config_fields_code,
        "{{CONFIG_INIT}}": code_generator.config_init_code,
        "{{CONFIG_EQUALS}}": code_generator.config_equals_code,
        "{{CONFIG_BASE}}": code_generator.config_base_code,
        "{{STYLE_FIELDS}}": code_generator.style_fields_code,
        "{{TRANSITION_FIELDS}}": code_generator.transition_fields_code,
        "{{STYLE_INIT}}": code_generator.style_init_code,
        "{{APPLY}}": code_generator.apply_code,
    }
    file_name = f"lv_theme_{code_generator.theme_name}"
    return {
        f"{file_name}.h": templatize(read_file(os.path.join(TEMPLATES_DIR, "theme.h.tpl")), template_parameters),
        f"{file_name}.c": templatize(read_file(os.path.join(TEMPLATES_DIR, "theme.c.tpl")), template_parameters),
    }


def write_templates(code_generator, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    for file_name, content in render_templates(code_generator).items():
        write_file(os.path.join(output_folder, file_name), content)
