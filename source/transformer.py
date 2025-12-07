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
    def class_declaration(self, items):
        name_token: Token = items[0]
        name = name_token.value
        if name == "theme":
            # Parse properties
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
