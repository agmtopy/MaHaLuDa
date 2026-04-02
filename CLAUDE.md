# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MaHaLuDa is a Windows screenshot tool that captures screen regions and uploads them to GitHub. It provides:
- Global hotkey (Ctrl+Shift+A) for screenshot capture
- Region selection with mouse drag
- Multi-monitor support
- Preview window before upload
- Automatic Git commit/push to GitHub
- Clipboard copy of GitHub Raw URL

**Requirements**: Python 3.10+ (uses union type syntax `Path | str`)

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application (requires admin on Windows for global hotkey)
python src/main.py

# Run tests
pytest tests/

# Run single test file
pytest tests/test_config_manager.py

# Code formatting
black src/

# Type checking
mypy src/

# Build executable
pyinstaller build.spec

# Diagnose environment issues
python diagnose.py
```

## Architecture

### Module Structure

```
src/
├── main.py                    # Application entry point (MaHaLuDaApp class)
├── core/                      # Core business logic
│   ├── config_manager.py      # YAML configuration (dataclass, validation)
│   ├── hotkey_manager.py      # Global hotkey registration (keyboard library)
│   ├── screenshot_capture.py  # Multi-monitor capture (mss library)
│   ├── image_processor.py     # Image processing and saving
│   ├── git_operations.py      # Git add/commit/push automation
│   └── link_generator.py      # GitHub Raw URL generation
├── gui/                       # PyQt6 user interface
│   ├── overlay_window.py      # Fullscreen region selection overlay
│   ├── preview_window.py      # Preview dialog with upload/cancel
│   ├── tray_icon.py           # System tray icon and menu
│   ├── settings_dialog.py     # Configuration settings dialog
│   └── notification.py        # Desktop notifications
└── utils/                     # Utilities
    ├── clipboard.py           # pyperclip wrapper
    ├── file_utils.py          # File operations
    ├── naming.py              # Filename generation with timestamp
    └── logger.py              # loguru configuration
```

**Important Notes:**
- **Admin Required on Windows**: The `keyboard` library requires administrator privileges to register global hotkeys
- **WSL Environment**: The application detects and handles WSL runtime differences
- **Git Lock Handling**: `GitOperations` automatically cleans up stale `.git/index.lock` files from crashed processes

### Configuration System

Configuration is managed via `Config` dataclass in `core/config_manager.py`:
- Config file location: `%LOCALAPPDATA%/MaHaLuDa/config.yaml` (Windows) or `~/.mahaluda/config.yaml`
- Default config template: `config/config.yaml`
- Config sections: hotkey, git, github, naming, image, ui, logging
- Validation: `Config.validate()` checks required fields and path existence

**Required user configuration:**
```yaml
git:
  repo_path: "E:/Project/BlogImages"  # Absolute path to local Git repo
  target_folder: "screenshots"         # Subfolder in the repo
  branch: "main"                       # Git branch name

github:
  username: "your-username"            # GitHub username
  repo_name: "BlogImages"              # GitHub repository name
```

**Key optional settings:**
- `git.auto_pull`: Pull before push (default: false)
- `naming.format`: Filename timestamp format (default: `%Y-%m-%d_%H-%M-%S`)
- `ui.show_preview`: Show preview window before upload (default: false)
- `ui.confirm_before_upload`: Confirmation dialog when preview disabled (default: true)

### Key Dependencies

- **PyQt6**: GUI framework for screenshot overlay, preview window, system tray
- **keyboard**: Global hotkey listening (requires admin on Windows)
- **mss**: High-performance multi-screen screenshot capture
- **Pillow**: Image processing and format conversion
- **loguru**: Structured logging with rotation
- **pyperclip**: Cross-platform clipboard operations
- **PyYAML**: Configuration file parsing
- **pystray**: System tray icon management

### Data Flow

1. Hotkey triggers `HotkeyManager` callback
2. Screenshot capture using `mss` with region selection overlay
3. Preview window displays captured image
4. On confirm: Save to `git.repo_path/target_folder/`
5. Git add/commit/push to configured branch
6. Generate GitHub Raw URL via `LinkGenerator`
7. Copy URL to clipboard via `pyperclip`

## Testing Notes

- Tests use `pytest` and `pytest-qt` for Qt application testing
- Test files located in `tests/` directory
- GUI tests require a display (may not work in headless environments)
- Main test files:
  - `test_config_manager.py`: Configuration loading and validation
  - `test_hotkey_manager.py`: Hotkey registration
  - `test_screenshot_capture.py`: Screenshot functionality
  - `test_git_operations.py`: Git automation
  - `test_integration.py`: End-to-end workflows
  - `test_settings_dialog.py`: Settings dialog UI

## Development Notes

**Administrator Privileges on Windows:**
- Required for global hotkey registration via `keyboard` library
- Application will show warning if hotkey registration fails
- Alternative: Run without admin (hotkey will not work, use tray menu)

**Environment Diagnostics:**
- Use `python diagnose.py` to check dependencies and runtime environment
- Detects WSL vs native Windows runtime
- Verifies all required dependencies are installed

**Git Lock File Handling:**
- Application automatically cleans up stale `.git/index.lock` files
- Only removes lock files older than 5 seconds to avoid conflicts
- Helps recover from crashed Git processes
