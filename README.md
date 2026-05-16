# Kube Invaders

A neon-styled Space Invaders-inspired game built with pygame.

All ships are drawn using lines with neon glow effects. Alien ships are
geometric shapes filled with animated liquid.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License: AGPL v3](https://img.shields.io/badge/license-AGPLv3-blue)



## System Dependencies for Audio (macOS/Linux)

To enable MP3 music playback with pygame, you may need to install additional system libraries:

### macOS (Homebrew)

```bash
brew install sdl2 sdl2_mixer
```

### Ubuntu/Debian

```bash
sudo apt-get install libsdl2-2.0-0 libsdl2-mixer-2.0-0
```

If you encounter errors related to audio or music playback (e.g., "pygame.error: Unable to open file" or "mixer not initialized"), ensure these libraries are installed and restart your terminal after installation.

---

## Installation

```bash
pip install .
```

Or install in development mode:

```bash
pip install -e .
```

## Running

```bash
# As a module
python -m kube_invaders

# Or via the console entry point after install
kube-invaders
```

## Controls

| Key | Action |
|---|---|
| `A` / `←` | Move left |
| `D` / `→` | Move right |
| `Space` | Shoot |
| `Space` / `Enter` | Start / Restart |

## Development

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install in editable mode
pip install -e .
```

## Pre-commit Hooks

This repository includes a pre-commit configuration for automated code quality checks.

Install and enable hooks:

```bash
pip install -e .[dev]
pre-commit install
```

If `pre-commit` is not found in your shell, use:

```bash
.venv/bin/python -m pre_commit install
```

Run hooks on all files:

```bash
pre-commit run --all-files
```

Included checks:

- Basic repository hygiene checks (YAML/TOML validation, trailing whitespace, EOF fix, merge conflict markers, large file checks)
- Ruff linting (with auto-fix)
- Ruff formatting

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPLv3). See [LICENSE](LICENSE) for details.
