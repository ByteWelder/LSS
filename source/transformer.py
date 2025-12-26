from typing import List

from lark import Transformer
from lark import Token
from lark import Tree
from source.models import *

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
    def style_declaration(self, items: List[Token]):
        name_token: Token = items[0]
        name = name_token.value
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
        return Style(name = name, properties = properties)
    def class_declaration(self, items: List[Token]):
        name_token: Token = items[0]
        style_dict = dict()
        return Class(name_token, style_dict)
