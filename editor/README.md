# Editor support

`lss.tmbundle` is a [TextMate](https://macromates.com/manual/en/bundles) bundle with syntax highlighting for `.lss` files. It highlights comments, `@` rules, variables (`@name`), config references (`$name`), colours, `dp` and `%` values, strings, functions, `state.*`/`part.*` targets and operators.

## CLion and other JetBrains IDEs

1. Open **Settings → Plugins** and make sure **TextMate Bundles** is enabled (it's bundled).
2. Open **Settings → Editor → TextMate Bundles**, click **+** and select the `editor/lss.tmbundle` folder.
3. Open **Settings → Editor → File Types**, and make sure `*.lss` isn't registered for another file type (e.g. Less or Text). The TextMate bundle registers it itself.

## VS Code

Create a local extension with this `package.json`, next to a copy of `lss.tmbundle/Syntaxes/lss.tmLanguage.json`:

```json
{
  "name": "lss",
  "version": "0.1.0",
  "engines": { "vscode": "^1.60.0" },
  "contributes": {
    "languages": [{ "id": "lss", "extensions": [".lss"] }],
    "grammars": [{ "language": "lss", "scopeName": "source.lss", "path": "./lss.tmLanguage.json" }]
  }
}
```

Copy the folder into `~/.vscode/extensions/` and restart VS Code.
