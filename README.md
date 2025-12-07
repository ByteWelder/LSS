# LSS

LSS stands for "LVGL Style Sheets"

It's a content-driven theme generator for LVGL.

## Usage

### Environment setup
Ensure Lark is installed. Preferably in a Python venv:

```asm
pip install lark
```

### Compiling

Compile a theme:

```shell
python compile.py themes/theme.lss 
```

Output can be found in the `build/` folder.

## Development

### Lark

[Lark](https://github.com/lark-parser/lark) is used to describe the grammar for LSS in [grammar.lark](grammar.lark)

### References

- Lark syntax highlight for JetBrains IDEs: https://github.com/lark-parser/intellij-syntax-highlighting

## License

[MIT License](LICENSE.txt)