from lark import Lark

from source.codegenerator import CodeGenerator
from source.files import *
from source.templates import write_templates
from source.transformer import LssTransformer

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
    code_generator = CodeGenerator(transformed)
    write_templates(code_generator, "build")
