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

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python -m src.main

# Run tests
pytest tests/

# Code formatting
black src/

# Type checking
mypy src/

# Build executable
pyinstaller build.spec
```

## Architecture

### Module Structure

```
src/
├── main.py                 # Application entry point
├── core/                   # Core business logic
│   ├── config_manager.py   # YAML configuration management (dataclasses)
│   ├── hotkey_manager.py   # Global hotkey registration (keyboard library)
│   └── link_generator.py   # GitHub URL generation
├── gui/                    # PyQt6 user interface (modules to be implemented)
└── utils/                  # Utilities
    ├── clipboard.py        # pyperclip wrapper
    ├── file_utils.py       # File operations
    └── logger.py           # loguru configuration
```

### Configuration System

Configuration is managed via `Config` dataclass in `core/config_manager.py`:
- Config file location: `%LOCALAPPDATA%/MaHaLuDa/config.yaml` (Windows) or `~/.mahaluda/config.yaml`
- Default config template: `config/config.yaml`
- Sections: hotkey, git, github, naming, image, ui, logging

Required user configuration:
- `git.repo_path`: Local Git repository absolute path
- `github.username`: GitHub username
- `github.repo_name`: GitHub repository name

### Key Dependencies

- **PyQt6**: GUI framework for screenshot overlay, preview window, system tray
- **keyboard**: Global hotkey listening (requires admin on Windows)
- **mss**: High-performance multi-screen screenshot capture
- **Pillow**: Image processing and format conversion
- **loguru**: Structured logging with rotation

### Data Flow

1. Hotkey triggers `HotkeyManager` callback
2. Screenshot capture using `mss` with region selection overlay
3. Preview window displays captured image
4. On confirm: Save to `git.repo_path/target_folder/`
5. Git add/commit/push to configured branch
6. Generate GitHub Raw URL via `LinkGenerator`
7. Copy URL to clipboard via `pyperclip`

## Testing Notes

- Tests use `pytest-qt` for Qt application testing
- GUI tests require a display (may not work in headless environments)
