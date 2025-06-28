# Guidelines for Repository Contributors

This repository hosts **Catanatron**, a high–performance Settlers of Catan simulator with optional web and UI components.

## Development Environment
- Use Python 3.11 or newer.
- Install dependencies with the optional extras to run tests and the web server:
  ```bash
  pip install .[web,gym,dev]
  ```
- Format Python code with **black** before committing:
  ```bash
  black catanatron catanatron_experimental
  ```
- Run the full test suite with coverage:
  ```bash
  coverage run --source=catanatron -m pytest tests/ && coverage report
  ```
- The frontend lives in `ui/` and requires Node.js `$(cat ui/.nvmrc)` (currently 24). Install dependencies and run tests with:
  ```bash
  npm ci
  npm run test
  ```

## Documentation
- Sphinx documentation is under `docs/`. Build it with:
  ```bash
  make -C docs html
  ```

## Pull Requests
- Keep commits focused and descriptive.
- Ensure all tests pass and code is formatted prior to opening a PR.
