# Inspector en el OFS

A playful, in-room party game where one player is the impostor and everyone else gets the real word. Run the monitor on a big screen, scan the QR, and let the accusations begin.

## What it does

- Creates a shared room with a 4-letter code and a big-screen monitor.
- Hands out a secret word to everyone except the impostor.
- Collects clues, runs a vote, and shows the results live.
- Includes QR-based joining, so phones jump straight in.

## How to play (fast)

1. Open the monitor on a laptop or TV screen.
2. Players scan the QR or enter the room code.
3. Start the round. Everyone submits a clue.
4. Vote for the impostor. Revelations ensue.

## Run it locally

```bash
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:5014`.

Optional secret key:

```bash
FLASK_SECRET_KEY=dev-secret python app.py
```

## Project layout

- `app.py` - Flask app, routes, and in-memory room state.
- `templates/` - Jinja pages for lobby, room, monitor, and results.
- `static/` - CSS and images.

## Notes

- Rooms live in memory. Restarting the server wipes active sessions.
- The monitor view is blocked on mobile for best results.

Have fun and accuse responsibly.
