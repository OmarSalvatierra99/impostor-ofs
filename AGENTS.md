# Repository Guidelines

## Project Structure & Module Organization
- `app.py` contains the Flask app, routes, and in-memory room state.
- `templates/` holds Jinja templates (`index.html`, `room.html`, `monitor.html`, etc.).
- `static/` contains `style.css` and images under `static/images/`.
- `requirements.txt` pins Python dependencies.

## Build, Test, and Development Commands
- `python app.py` starts the development server on `0.0.0.0:5014` with debug enabled.
- `pip install -r requirements.txt` installs runtime dependencies.
- Example: `FLASK_SECRET_KEY=dev-secret python app.py` to override the default secret.

## Coding Style & Naming Conventions
- Python: follow PEP 8; use 4-space indentation and `snake_case` for functions/variables.
- Templates: keep Jinja control blocks aligned and minimal; HTML IDs/classes should be `kebab-case`.
- Static assets: place new images in `static/images/` and reference via `url_for('static', filename='images/...')`.

## Testing Guidelines
- No automated test suite is configured yet.
- If you add tests, prefer `pytest` and name files `test_*.py`.
- Keep any future tests close to `app.py`-level behavior (route handlers and state transitions).

## Commit & Pull Request Guidelines
- Recent history uses short, imperative messages (e.g., "Clean project", "Improve portfolio").
- Auto-generated sync commits exist; avoid mixing manual changes into those.
- PRs should include a concise summary, manual test notes (what you clicked or ran), and screenshots for UI changes.

## Configuration & Runtime Notes
- Session security: set `FLASK_SECRET_KEY` in production.
- Room state is in-memory only; restarting the server clears active rooms.
