# Agent Guidelines for Tidal Project

## Build/Test Commands
- **Install dependencies**: `uv sync`
- **Run application**: `uv run main.py`
- **Lint code**: `flake8`
- **Deploy**: `./deploy.sh` (creates lambda-bundle.zip)

## Code Style Guidelines
- **Python version**: Requires Python 3.10+
- **Line length**: Max 120 characters (setup.cfg)
- **Imports**: Group standard library, third-party, local imports separately
- **Function signatures**: Use type hints (e.g., `api_key: str, lat: float`)
- **String formatting**: Use `.format()` method for string interpolation
- **Naming**: snake_case for functions/variables, UPPER_CASE for constants
- **Error handling**: Use simple conditionals and early returns
- **Comments**: Minimal - code should be self-documenting
- **File structure**: Keep main logic in main.py, utilities in tidal_functions.py

## Environment Setup
- Use `.env` file for API keys and configuration
- Virtual environment: `uv venv` (or let `uv sync` create it automatically)
- Required env vars: `NIWA_API_KEY`, `VISUAL_CROSSING_API_KEY`, `LAT`, `LONG`