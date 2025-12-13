import sys
import re

if sys.platform == "win32":
    SHELL_COLOR_RED = ""
    SHELL_COLOR_ORANGE = ""
    SHELL_COLOR_RESET = ""
else:
    SHELL_COLOR_RED = "\033[91m"
    SHELL_COLOR_ORANGE = "\033[93m"
    SHELL_COLOR_RESET = "\033[m"

def print_warning(message):
    print(f"{SHELL_COLOR_ORANGE}WARNING: {message}{SHELL_COLOR_RESET}")

def print_error(message):
    print(f"{SHELL_COLOR_RED}ERROR: {message}{SHELL_COLOR_RESET}")

def exit_with_error(message):
    print_error(message)
    sys.exit(1)


def camel_to_snake(text: str) -> str:
    """Convert a camelCase or PascalCase string to snake_case.

    Also converts hyphens to underscores. Examples:
    - "bgColor" -> "bg_color"
    - "alphaLayerMask" -> "alpha_layer_mask"
    - "RGBValue" -> "rgb_value"
    """
    if text is None:
        return text
    # Normalize existing separators
    text = text.replace("-", "_")
    # Insert underscores between camel case boundaries
    s1 = re.sub(r"(.)([A-Z][a-z0-9]+)", r"\1_\2", text)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.lower()

