# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-06-27

### Added
- **Tkinter-to-Flet GUI Migration:** Fully refactored the desktop client to Flet (Flutter-based python framework), creating a modern responsive dark-themed sidebar dashboard matching high-fidelity mockups.
- **Asynchronous Real-Time Balance Loading:** Displays actual SOL balances of tracked user wallets directly on dashboard cards and row lists via background RPC queries, preventing GUI thread freezing.
- **Headless Local Browser Fallback:** Auto-detects headless Linux or WSL environments lacking a window display manager on boot, launching the panel as a local web page.
- **Unified Address Modal Dialog:** Added a single modal input popup that inspects Solana accounts on-chain, resolves token owner/mint parameters, and registers them.
- **On-Chain Address Auto-Classification & Verification:** Dynamically inspects account information via Solana RPC `getAccountInfo` to distinguish between User Wallets and Specific Token Accounts.
- **Interactive Telegram Confirmation Prompts:** Pasting a raw Solana address in the bot triggers an inline keyboard asking the user if they want to add it as a User Wallet or a Specific Token Account.
- **Simplified `/add` Command:** Deprecated `/add u` and `/add w` command prefixes. The simplified `/add <address> [name]` command automatically inspects the address on-chain and routes it to the correct watchlist category.
- **Pinned Control Panel Dashboard:** Added interactive inline buttons under the pinned start message to refresh portfolio balances, display live logs, view active parameters, and pause/resume alerts.
- **60-Second Alert Batching & USD Noise Filtering:** Merges multiple transaction events occurring within 60 seconds into a single grouped message and blocks alerts below a customizable USD threshold.
- **Auto-Delete Telegram Messages:** Automatically deletes outdated command responses to maintain a clean chat history on mobile.
- **Configurator Watchdog Monitor:** Background service that automatically restarts the tracker bot subprocess if it terminates unexpectedly.
- **System Tray Minimization:** Minimizes the configurator GUI window to a system tray icon via `pystray` and `pillow` (with graceful fallback for Linux systems without GTK bindings).
- **OS Theme Auto-Sync:** Auto-detects GNOME dark theme settings on Linux boot.
- **RPC presets & Premium builders:** Dropdown selections for free Solana RPCs and builder fields for Helius and QuickNode premium API endpoints.
- **GitHub Auto-Updater:** Asynchronously queries releases on startup and displays an update banner if a newer release exists.
- **Database Self-Repair Migration:** Auto-migrates and heals any mismatched address categories in `secrets/tracked.json` at bot startup, standardizing old `"wallet"` label records to `"token"`.

### Fixed
- **Live Console Log Truncation:** Truncates the physical `logs/tracker.log` log file when "Clear Console" is clicked, preventing log refreshes from re-displaying cleared events.
- **Solana RPC Rate-Limit Flood:** Fixed a bug where the scheduler thread triggered on-chain address classifications on every reload (every 2 seconds), flooding the RPC and causing rate limits (HTTP 429/403) and runtime locks. Address migrations now run exactly once at bot startup.
- **Solana RPC Failover Integration:** Integrated alternative RPC failover loops across all configurator network operations (balance checking, testing connections, and adding/verifying wallets) to prevent connection timeouts and `0.00 SOL` balance display failures.

## [1.3.0] - 2026-06-14

### Added
- **Dynamic Localization & Multi-Language Support**: Fully translated all GUI labels, tabs, status logs, error alerts, and info messages into English, Russian, and Arabic. Swapping the active language in the settings tab updates the interface immediately at runtime.
- **Localized Modal Windows & Popups**: Upgraded custom dialog modals (`CustomMessageDialog`, `CustomConfirmDialog`, `CustomAddAddressDialog`) and `MessageBoxWrapper` to inherit active translation helpers dynamically.
- **Release Documentation & Screenshots**: Copied visual screenshots into the repository structure (`assets/`) and updated the `README.md` to reference them.

### Fixed
- **Combobox Style Contrast**: Configured readonly state colors and listbox option database defaults in `gui_styles.py` to prevent white-on-white text rendering issues in Dark Mode.
- **Icon Sizing & Title Bar Inheritance**: Subsampled the Solana PhotoImage icon data down to 32x32 for better title bar mapping support on native window managers.

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
