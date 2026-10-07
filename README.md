# LSS

LSS stands for "LVGL Style Sheets"

It's a content-driven theme generator for LVGL.

## Usage

### Environment setup
Ensure Lark is installed. Preferably in a Python venv:

```asm
pip install lark
```

### Editor support

See [editor/README.md](editor/README.md) for syntax highlighting in CLion and VS Code.

### Compiling

Compile a theme:

```shell
python compile.py themes/default.lss
```

Output can be found in the `build/` folder as `lv_theme_<name>.c` and `lv_theme_<name>.h`.
Use `--output <folder>` to change the output folder and `--name <name>` to override the theme name.

### Using a generated theme

```c
lv_theme_default_config_t config;
lv_theme_default_config_init(&config); // Applies the defaults from @config
config.is_dark = true;
lv_display_set_theme(display, lv_theme_default_init(display, &config));
```

## Syntax

See [themes/default.lss](themes/default.lss) and [themes/mono.lss](themes/mono.lss) for complete examples.

```
@theme default;                       // Theme name: lv_theme_default_init(), etc.

@config {                             // Generates lv_theme_default_config_t
    isDark: bool = false;             // Types: bool, color, int, opa, font
    colorPrimary: color = palette(blue);
    font: font = raw("LV_FONT_DEFAULT");
}

@widget toolbar: my_toolbar_class;    // A widget class that isn't part of LVGL (declared extern)

@pad: by-size(16dp, 20dp, 24dp);      // Variables become #defines

@transition normal {                  // lv_style_transition_dsc_t
    props: bgOpa, bgColor;
    path: linear;
    duration: 200;
    delay: 0;
}

card {                                // A style: lv_style_set_<property>() for each property
    bgColor: if($isDark, #282B30, white);
    padAll: @pad;
    size: 8dp, 8dp;                   // Multiple arguments
    transition: normal;
    @if (!$isDark) { shadowWidth: 3dp; } @else { shadowWidth: 0; }
}

@cif (LV_THEME_DEFAULT_GROW) {        // Compile-time #if, also allowed inside styles and apply rules
    grow { transformWidth: 3dp; }
}

apply(null > *) { card: default; }    // Screens (objects without a parent)
apply(tabview > obj[0]) { }           // Child at index 0 of a tabview: no styles
apply(button) {                       // lv_obj_add_style() for every button
    card: default;
    grow: part.indicator, state.pressed;
}
apply(list > button) {                // More specific rules are checked first
    @include button;                  // Reuse the styles of another rule
    @if (display(large)) { grow: state.focusKey; }
}
```

### Values

| LSS                                   | C                                                  |
|---------------------------------------|----------------------------------------------------|
| `12dp`                                | `LV_DPX_CALC(theme->disp_dpi, 12)`                 |
| `#15171A`, `#FFF`                     | `lv_color_hex(0x15171A)`, `lv_color_hex(0xFFFFFF)` |
| `white`, `black`                      | `lv_color_white()`, `lv_color_black()`             |
| `palette(grey)`, `lighten(grey, 4)`, `darken(grey, 2)` | `lv_palette_main(LV_PALETTE_GREY)`, ...  |
| `contrast(#00BBFF)`                   | Black or white text for that background color      |
| `mix(white, #6750A4, 10%)`            | `lv_color_mix(...)`: 10% of the first color        |
| `40%`, `opa(40)`, `transp`, `cover`   | `LV_OPA_40`, `LV_OPA_TRANSP`, `LV_OPA_COVER`       |
| `pct(50)`                             | `lv_pct(50)`                                       |
| `circle`, `content`                   | `LV_RADIUS_CIRCLE`, `LV_SIZE_CONTENT`              |
| `top \| bottom`, `center`, `underline` | Property-specific enums, e.g. `LV_BORDER_SIDE_TOP` |
| `symbol(ok)`                          | `LV_SYMBOL_OK`                                     |
| `dpi`, `dpi-def`                      | `theme->disp_dpi`, `LV_DPI_DEF`                    |
| `$isDark`                             | `theme->config.is_dark`                            |
| `@pad * 2`, `-@pad`, `(a + b) / 2`    | C arithmetic                                       |
| `by-size(small, medium, large)`       | Value depending on the display size                |
| `display(small)`                      | `theme->disp_size == DISP_SMALL`                   |
| `if(condition, a, b)`                 | `condition ? a : b`                                |
| `raw("LV_DPX(4)")`                    | Verbatim C code                                    |

Identifiers may contain hyphens, so subtraction needs spaces: `@a - 2`.

### Apply rules

Rules are grouped by the widget type they target. For each type, rules with conditions (parents, child indices) are checked first in source order, and the first match wins. The plain rule (e.g. `apply(button)`) is the fallback. Rules are guarded with the relevant `LV_USE_*` macros, and so are the styles that are only used by guarded rules.

Config fields named `colorPrimary`, `colorSecondary`, `font`, `fontSmall`, `fontNormal` and `fontLarge` are also stored in `lv_theme_t`, so `lv_theme_get_color_primary()` and similar functions keep working.

## Development

### Lark

[Lark](https://github.com/lark-parser/lark) is used to describe the grammar for LSS in [grammar.lark](grammar.lark)

### Tests

Integration tests are in [tests/cases](tests/cases): each `<name>.lss` file is compiled and the output is compared with the expected `<name>.h` and `<name>.c` files. There is a test for each syntax feature.

```shell
python tests/run_tests.py           # Run all tests
python tests/run_tests.py --update  # Overwrite the expected files with the current output
```

All tests are run, and each failure shows the first mismatching line with the lines around it.
Review the changes in the expected files after using `--update`.

Unit tests (mostly for error handling):

```shell
python -m unittest tests.test_lss
```

### References

- Lark syntax highlight for JetBrains IDEs: https://github.com/lark-parser/intellij-syntax-highlighting

## License

[MIT License](LICENSE.txt)