from typing import Dict, List, Optional

PALETTES = [
    "red", "pink", "purple", "deep-purple", "indigo", "blue", "light-blue", "cyan", "teal",
    "green", "light-green", "lime", "yellow", "amber", "orange", "deep-orange", "brown",
    "blue-grey", "grey",
]

PARTS = {
    "main": "LV_PART_MAIN",
    "scrollbar": "LV_PART_SCROLLBAR",
    "indicator": "LV_PART_INDICATOR",
    "knob": "LV_PART_KNOB",
    "selected": "LV_PART_SELECTED",
    "items": "LV_PART_ITEMS",
    "cursor": "LV_PART_CURSOR",
    "customFirst": "LV_PART_CUSTOM_FIRST",
    "textareaPlaceholder": "LV_PART_TEXTAREA_PLACEHOLDER",
    "any": "LV_PART_ANY",
}

STATES = {
    "default": "LV_STATE_DEFAULT",
    "checked": "LV_STATE_CHECKED",
    "focused": "LV_STATE_FOCUSED",
    "focusKey": "LV_STATE_FOCUS_KEY",
    "edited": "LV_STATE_EDITED",
    "hovered": "LV_STATE_HOVERED",
    "pressed": "LV_STATE_PRESSED",
    "scrolled": "LV_STATE_SCROLLED",
    "disabled": "LV_STATE_DISABLED",
    "user1": "LV_STATE_USER_1",
    "user2": "LV_STATE_USER_2",
    "user3": "LV_STATE_USER_3",
    "user4": "LV_STATE_USER_4",
    "any": "LV_STATE_ANY",
}

# Identifiers that are valid for any property
GLOBAL_IDENTS = {
    "true": "true",
    "false": "false",
    "circle": "LV_RADIUS_CIRCLE",
    "content": "LV_SIZE_CONTENT",
    "white": "lv_color_white()",
    "black": "lv_color_black()",
    "transp": "LV_OPA_TRANSP",
    "cover": "LV_OPA_COVER",
    "dpi-def": "LV_DPI_DEF",
}

# Identifiers that are only valid for specific properties
PROPERTY_ENUMS: Dict[str, Dict[str, str]] = {
    "borderSide": {name: f"LV_BORDER_SIDE_{name.upper()}" for name in ["none", "bottom", "top", "left", "right", "full", "internal"]},
    "textAlign": {name: f"LV_TEXT_ALIGN_{name.upper()}" for name in ["auto", "left", "center", "right"]},
    "textDecor": {name: f"LV_TEXT_DECOR_{name.upper()}" for name in ["none", "underline", "strikethrough"]},
    "baseDir": {name: f"LV_BASE_DIR_{name.upper()}" for name in ["ltr", "rtl", "auto"]},
    "bgGradDir": {name: f"LV_GRAD_DIR_{name.upper()}" for name in ["none", "ver", "hor"]},
    "blendMode": {name: f"LV_BLEND_MODE_{name.upper()}" for name in ["normal", "additive", "subtractive", "multiply", "difference"]},
}


def resolve_enum(name: str, property_name: Optional[str]) -> Optional[str]:
    """Resolve an identifier to a C constant. Without a property, an identifier is only resolved when unambiguous."""
    if property_name is not None and property_name in PROPERTY_ENUMS:
        value = PROPERTY_ENUMS[property_name].get(name)
        if value is not None:
            return value
    if name in GLOBAL_IDENTS:
        return GLOBAL_IDENTS[name]
    if property_name is None:
        matches = {table[name] for table in PROPERTY_ENUMS.values() if name in table}
        if len(matches) == 1:
            return matches.pop()
    return None


def widget_macros(widget_type: str, custom_widgets: Dict[str, str]) -> List[str]:
    """The LV_USE_* macros that must be enabled for a widget class to exist."""
    if widget_type == "obj" or widget_type in custom_widgets:
        return []
    if widget_type == "dropdownlist":
        return ["LV_USE_DROPDOWN"]
    if widget_type in ("calendar_header_arrow", "calendar_header_dropdown"):
        return ["LV_USE_CALENDAR", f"LV_USE_{widget_type.upper()}"]
    if widget_type == "tileview_tile":
        return ["LV_USE_TILEVIEW"]
    for prefix in ("list", "menu", "msgbox"):
        if widget_type.startswith(prefix + "_"):
            return [f"LV_USE_{prefix.upper()}"]
    return [f"LV_USE_{widget_type.upper()}"]


def widget_class(widget_type: str, custom_widgets: Dict[str, str]) -> str:
    return custom_widgets.get(widget_type, f"lv_{widget_type}_class")
