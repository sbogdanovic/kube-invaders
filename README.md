# Pod Shooter 2

A neon-styled Space Invaders-inspired game built with pygame.

All ships are drawn using lines with neon glow effects. Alien ships are
geometric shapes filled with animated liquid.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

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
python -m pod_shooter

# Or via the console entry point after install
pod-shooter
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

## License

MIT — see [LICENSE](LICENSE) for details.
