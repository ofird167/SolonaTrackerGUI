# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-06-13

### Changed
- **Release Directory Packaging**: Configured `build.bat` to package the compiled standalone executables (`configurator.exe` and `tracker.exe`) into a dedicated, self-contained `release/` folder rather than dumping them in the repository root directory.
- **Dynamic Executable Path Resolution**: Updated `configurator.py` and `tracker.py` to resolve their base directories dynamically using `sys.frozen`. This ensures configuration and state files (like `secrets/.env`, `secrets/tracked.json`, and `logs/tracker.log`) are correctly loaded and written relative to the executable's directory when packaged, rather than being lost in PyInstaller's temporary execution folders.
- **Release Environment Template**: Automatically copies `example.env` into `release/secrets/example.env` as a clean starter configuration.
- **Windows Taskbar & Minimizing**: Fixed taskbar visibility and minimizing behavior on Windows. When compiling, Tkinter's `winfo_id()` is now updated and mapped before registering the app window. A delayed initialization strategy via `<Map>` bindings and dynamic style adjustments allows borderless executables to minimize to the taskbar and restore properly without losing focus.

## [1.1.2] - 2026-06-13

### Fixed
- **Windows Taskbar Visibility**: Patched the borderless window (`overrideredirect`) logic on Windows to register it with the OS taskbar so it can be focused/selected.
- **Topmost Modal Focus**: Added topmost layers, window raising (`lift()`), and input focus checks on all borderless modal dialog windows to prevent them from rendering behind the parent window and freezing inputs.

## [1.1.1] - 2026-06-13

### Fixed
- **Telegram `/name` Command**: Allowed renaming tracked wallets using their current custom name/nickname as the identifier (e.g. `/name Trader Wallet 1 wallet1`).

## [1.1.0] - 2026-06-13

### Added
- **Tabbed Interface Layout**: Replaced the scrolling configuration canvas with a modern, dark-themed `ttk.Notebook` dividing controls into four panels: *Settings & Credentials*, *Wallet Manager*, *Live Console & Logs*, and *Backup & License*.
- **RPC Latency (Ping) Meter**: Measures connection round-trip latency in milliseconds during JSON-RPC slot updates and reports response speed directly in tests.
- **Import/Export Backups**: Integrated JSON import/export dialog files to quickly backup and restore tracked configuration lists.
- **Custom Names in Commands**: Extended `/add u <address> [CUSTOM NAME]` to support naming wallets immediately upon addition.
- **Nickname-linked Deletions**: Upgraded `/remove <address_or_nickname>` to support deleting wallets by their custom name case-insensitively.
- **Log Nicknames**: Logs printed in the console and stdout now display custom nicknames instead of raw base58 prefixes.
- **MIT License**: Added standard `LICENSE` file at the repository root.

### Changed
- **Modular Refactoring**: Restructured `configurator.py` by splitting style tokens into `gui_styles.py` and custom dialog modules into `gui_dialogs.py`.
- **Log Rotation**: Switched standard `FileHandler` logging to `RotatingFileHandler` to cap log files at 10MB across a maximum of 3 rotation backups.

### Fixed
- **Linux Emojis Rendering**: Replaced default colored emoticons with standard text symbols (`[✓]`, `[✗]`, `[i]`) preventing square box rendering on Linux window managers.

---

## [1.0.0] - 2026-06-13

### Added
- Initial release of the Solana Wallet Tracker Bot and Configurator.
- Standard Telegram commands (`/start`, `/stop`, `/interval`, `/currency`, `/show`, `/balance`).
- Double-click copy, background tracker process monitor, and basic GUI configurations.
