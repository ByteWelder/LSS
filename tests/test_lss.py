import contextlib
import io
import os
import unittest

from source.codegenerator import CodeGenerator
from source.expressions import EmitContext, emit
from source.main import parse
from source.models import *
from source.selectors import selector_condition
from source.templates import render_templates

LSS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generate(source: str) -> CodeGenerator:
    with contextlib.redirect_stdout(io.StringIO()):
        return CodeGenerator(parse(source))


def emit_value(value: str, property_name: str = "width", config: str = "") -> str:
    entries = parse(f"@theme t; @config {{ {config} }} @v: {value};")
    config_fields = {f.name: f for entry in entries if isinstance(entry, Config) for f in entry.fields}
    variable = next(entry for entry in entries if isinstance(entry, Variable))
    context = EmitContext(variables={}, config_fields=config_fields, property_name=property_name)
    return emit(variable.value, context)


def assert_fails(test: unittest.TestCase, function):
    with contextlib.redirect_stdout(io.StringIO()):
        with test.assertRaises(SystemExit):
            function()


class ExpressionTest(unittest.TestCase):

    def test_dp(self):
        self.assertEqual(emit_value("12dp"), "LV_DPX_CALC(theme->disp_dpi, 12)")

    def test_colors(self):
        self.assertEqual(emit_value("#15171a"), "lv_color_hex(0x15171A)")
        self.assertEqual(emit_value("#FFF"), "lv_color_hex(0xFFFFFF)")
        self.assertEqual(emit_value("white"), "lv_color_white()")
        self.assertEqual(emit_value("palette(blue-grey)"), "lv_palette_main(LV_PALETTE_BLUE_GREY)")
        self.assertEqual(emit_value("lighten(grey, 4)"), "lv_palette_lighten(LV_PALETTE_GREY, 4)")
        self.assertEqual(emit_value("darken(red, 2)"), "lv_palette_darken(LV_PALETTE_RED, 2)")

    def test_opacity(self):
        self.assertEqual(emit_value("40%"), "LV_OPA_40")
        self.assertEqual(emit_value("opa(50)"), "LV_OPA_50")
        self.assertEqual(emit_value("35%"), "89")
        self.assertEqual(emit_value("cover"), "LV_OPA_COVER")

    def test_property_enums(self):
        self.assertEqual(emit_value("top | bottom", "borderSide"), "LV_BORDER_SIDE_TOP | LV_BORDER_SIDE_BOTTOM")
        self.assertEqual(emit_value("center", "textAlign"), "LV_TEXT_ALIGN_CENTER")
        self.assertEqual(emit_value("underline", "textDecor"), "LV_TEXT_DECOR_UNDERLINE")
        self.assertEqual(emit_value("circle", "radius"), "LV_RADIUS_CIRCLE")

    def test_ambiguous_enum_without_property(self):
        # "left" exists for both borderSide and textAlign
        assert_fails(self, lambda: emit_value("left", None))
        self.assertEqual(emit_value("underline", None), "LV_TEXT_DECOR_UNDERLINE")

    def test_unknown_identifier(self):
        assert_fails(self, lambda: emit_value("bogus"))

    def test_arithmetic(self):
        self.assertEqual(emit_value("-2dp * 2"), "(-LV_DPX_CALC(theme->disp_dpi, 2)) * 2")
        self.assertEqual(emit_value("dpi / 4 * 256"), "(theme->disp_dpi / 4) * 256")
        self.assertEqual(emit_value("1 - (2 - 3)"), "1 - (2 - 3)")
        self.assertEqual(emit_value("dpi-def * 2"), "LV_DPI_DEF * 2")

    def test_functions(self):
        self.assertEqual(emit_value("symbol(ok)"), "LV_SYMBOL_OK")
        self.assertEqual(emit_value('raw("LV_DPX(4)")'), "LV_DPX(4)")
        self.assertEqual(emit_value("pct(50)"), "lv_pct(50)")
        self.assertEqual(
            emit_value("by-size(1, 2, 3)"),
            "theme->disp_size == DISP_LARGE ? 3 : theme->disp_size == DISP_MEDIUM ? 2 : 1"
        )
        self.assertEqual(emit_value("display(small)"), "theme->disp_size == DISP_SMALL")

    def test_config_reference(self):
        config = "isDark: bool;"
        self.assertEqual(emit_value("$isDark", config=config), "theme->config.is_dark")
        self.assertEqual(emit_value("if(!$isDark, 1, 2)", config=config), "!theme->config.is_dark ? 1 : 2")
        assert_fails(self, lambda: emit_value("$missing", config=config))

    def test_strings_only_in_raw(self):
        assert_fails(self, lambda: emit_value('"text"'))


class ConfigTest(unittest.TestCase):

    def test_config_code(self):
        generator = generate("""
            @theme t;
            @config { isDark: bool = true; colorPrimary: color; font: font = raw("LV_FONT_DEFAULT"); }
        """)
        self.assertIn("bool is_dark;", generator.config_fields_code)
        self.assertIn("lv_color_t color_primary;", generator.config_fields_code)
        self.assertIn("const lv_font_t * font;", generator.config_fields_code)
        self.assertIn("lv_memzero(config, sizeof(*config));", generator.config_init_code)
        self.assertIn("config->is_dark = true;", generator.config_init_code)
        self.assertNotIn("color_primary", generator.config_init_code)
        self.assertIn("lv_color_eq(a->color_primary, b->color_primary)", generator.config_equals_code)
        self.assertIn("theme->base.color_primary = config->color_primary;", generator.config_base_code)
        self.assertIn("theme->base.font_normal = config->font;", generator.config_base_code)

    def test_default_must_not_depend_on_theme(self):
        assert_fails(self, lambda: generate("@theme t; @config { size: int = 4dp; }"))
        assert_fails(self, lambda: generate("@theme t; @v: 4dp; @config { size: int = @v; }"))

    def test_unknown_type(self):
        assert_fails(self, lambda: generate("@theme t; @config { size: float; }"))

    def test_missing_theme_name(self):
        assert_fails(self, lambda: generate("@config { isDark: bool; }"))


class StyleTest(unittest.TestCase):

    def test_style_code(self):
        generator = generate("""
            @theme t;
            @config { isDark: bool; }
            s {
                size: 8dp, 4;
                @if (!$isDark) { shadowWidth: 3; } @else { shadowWidth: 0; }
                @cif (MY_FLAG) { borderPost: true; }
            }
            apply(obj) { s: default; }
        """)
        self.assertIn("lv_style_set_size(&theme->styles.s, LV_DPX_CALC(theme->disp_dpi, 8), 4);", generator.style_init_code)
        self.assertIn("if(!theme->config.is_dark) {", generator.style_init_code)
        self.assertIn("else {", generator.style_init_code)
        self.assertIn("#if MY_FLAG\n    lv_style_set_border_post(&theme->styles.s, true);\n#endif", generator.style_init_code)

    def test_transition(self):
        generator = generate("""
            @theme t;
            @transition fast { props: bgOpa, transformScaleX; duration: 100; delay: 5; }
            s { transition: fast; }
            apply(obj) { s: default; }
        """)
        self.assertIn("LV_STYLE_BG_OPA, LV_STYLE_TRANSFORM_SCALE_X,", generator.style_init_code)
        self.assertIn("lv_style_transition_dsc_init(&theme->trans_fast, trans_fast_props, lv_anim_path_linear, 100, 5, NULL);", generator.style_init_code)
        self.assertIn("lv_style_set_transition(&theme->styles.s, &theme->trans_fast);", generator.style_init_code)
        self.assertIn("lv_style_transition_dsc_t trans_fast;", generator.transition_fields_code)

    def test_unknown_transition(self):
        assert_fails(self, lambda: generate("@theme t; s { transition: missing; } apply(obj) { s: default; }"))

    def test_style_guards(self):
        generator = generate("""
            @theme t;
            shared { radius: 0; }
            only_button { radius: 0; }
            in_tabview { radius: 0; }
            @cif (MY_FLAG) { flagged { radius: 0; } }
            apply(obj) { shared: default; }
            apply(button) { shared: default; only_button: default; flagged: default; }
            apply(tabview > button) { in_tabview: default; }
        """)
        fields = generator.style_fields_code
        self.assertIn("    lv_style_t shared;", fields)
        self.assertNotIn("#if LV_USE_BUTTON\n    lv_style_t shared;", fields)
        self.assertIn("#if LV_USE_BUTTON\n    lv_style_t only_button;", fields)
        self.assertIn("#if LV_USE_BUTTON && LV_USE_TABVIEW\n    lv_style_t in_tabview;", fields)
        self.assertIn("#if MY_FLAG && LV_USE_BUTTON\n    lv_style_t flagged;", fields)


class SelectorTest(unittest.TestCase):

    def selector(self, text: str) -> Selector:
        rule = next(entry for entry in parse(f"apply({text}) {{ }}") if isinstance(entry, ApplyRule))
        return rule.selectors[0]

    def test_conditions(self):
        self.assertIsNone(selector_condition(self.selector("button"), {}))
        self.assertEqual(selector_condition(self.selector("null > *"), {}), "parent == NULL")
        self.assertEqual(selector_condition(self.selector("* > obj"), {}), "parent != NULL")
        self.assertEqual(
            selector_condition(self.selector("tabview > obj[1]"), {}),
            "lv_obj_check_type(parent, &lv_tabview_class) && lss_is_child(parent, 1, obj)"
        )
        self.assertEqual(
            selector_condition(self.selector("tabview > *[0] > button"), {}),
            "lv_obj_check_type(lss_ancestor(obj, 2), &lv_tabview_class) && lss_is_child(lss_ancestor(obj, 2), 0, parent)"
        )

    def test_invalid_null(self):
        assert_fails(self, lambda: selector_condition(self.selector("obj > null > obj"), {}))

    def test_apply_code(self):
        generator = generate("""
            @theme t;
            a { radius: 0; }
            b { radius: 1; }
            apply(null > *) { a: default; }
            apply(win > obj[0]) { }
            apply(obj) { a: default; b: part.scrollbar, state.scrolled; }
            apply(button) { a: default; @if (display(large)) { b: state.pressed; } @else { b: state.checked; } }
            apply(menu_main_header_cont > button) { @include button; b: state.focusKey; }
        """)
        code = generator.apply_code
        self.assertIn("    /* null > * */\n    if(parent == NULL) {", code)
        self.assertIn("#if LV_USE_WIN\n        /* win > obj[0] */\n        if(lv_obj_check_type(parent, &lv_win_class) && lss_is_child(parent, 0, obj)) {\n            return;\n        }\n#endif", code)
        self.assertIn("lv_obj_add_style(obj, &theme->styles.b, LV_PART_SCROLLBAR | LV_STATE_SCROLLED);", code)
        self.assertIn("if(theme->disp_size == DISP_LARGE) {", code)
        # The conditional rule comes before the unconditional one, and includes its styles
        include_position = code.index("/* menu_main_header_cont > button */")
        base_position = code.index("/* button */")
        self.assertLess(include_position, base_position)
        self.assertIn("LV_STATE_FOCUS_KEY", code[include_position:base_position])
        self.assertIn("LV_STATE_CHECKED", code[include_position:base_position])

    def test_include_cycle(self):
        assert_fails(self, lambda: generate("""
            @theme t;
            apply(obj) { @include button; }
            apply(button) { @include obj; }
        """))

    def test_duplicate_rule(self):
        assert_fails(self, lambda: generate("@theme t; apply(obj) { } apply(obj) { }"))

    def test_unknown_style_and_target(self):
        assert_fails(self, lambda: generate("@theme t; apply(obj) { missing: default; }"))
        assert_fails(self, lambda: generate("@theme t; s { radius: 0; } apply(obj) { s: part.bogus; }"))
        assert_fails(self, lambda: generate("@theme t; s { radius: 0; } apply(obj) { s: bogus; }"))


class ThemeTest(unittest.TestCase):

    def test_bundled_themes_generate(self):
        for theme in ("default", "mono", "benchmark"):
            with self.subTest(theme=theme):
                with open(os.path.join(LSS_DIR, "themes", f"{theme}.lss")) as file:
                    generator = generate(file.read())
                files = render_templates(generator)
                source = files[f"lv_theme_{generator.theme_name}.c"]
                self.assertNotIn("{{", source)
                self.assertIn(f"lv_theme_t * lv_theme_{generator.theme_name}_init(", source)


if __name__ == "__main__":
    unittest.main()
