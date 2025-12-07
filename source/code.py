# Create C code
from source.models import *

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
