import os
from typing import Optional

from lark import Lark
from lark.exceptions import UnexpectedInput

from source.codegenerator import CodeGenerator
from source.files import read_file
from source.printing import exit_with_error
from source.templates import write_templates
from source.transformer import LssTransformer

GRAMMAR_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "grammar.lark")


def parse(lss_data: str, verbose: bool = False) -> list:
    lark = Lark(read_file(GRAMMAR_PATH), parser="lalr")
    try:
        lss_parsed = lark.parse(lss_data)
    except UnexpectedInput as error:
        exit_with_error(f"Syntax error at line {error.line}, column {error.column}:\n{error.get_context(lss_data)}")
    if verbose:
        print(lss_parsed.pretty())
    transformed = LssTransformer().transform(lss_parsed)
    if verbose:
        for entry in transformed:
            print(entry)
    return transformed


def main(lss_file_path: str, verbose: bool, output_folder: str = "build", name_override: Optional[str] = None):
    transformed = parse(read_file(lss_file_path), verbose)
    code_generator = CodeGenerator(transformed, name_override)
    write_templates(code_generator, output_folder)
