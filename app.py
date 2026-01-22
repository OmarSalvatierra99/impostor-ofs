from __future__ import annotations

import os
import random
import string
from typing import Dict, Tuple
from io import BytesIO

import qrcode
from flask import Flask, jsonify, redirect, render_template, request, session, url_for, send_file

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "impostor-secret")

MOBILE_UA_KEYWORDS = ("android", "iphone", "ipad", "ipod", "webos", "blackberry", "windows phone")


CATEGORIES = {
    "Oficina": {
        "image": "images/oficina.svg",
        "words": [
            "mesa",
            "silla",
            "lapiz",
            "libro",
            "taza",
            "reloj",
            "puerta",
            "ventana",
            "caja",
            "bolsa",
        ],
    },
    "Trabajo": {
        "image": "images/proyecto.svg",
        "words": [
            "correo",
            "tarea",
            "nota",
            "agenda",
            "equipo",
            "reunion",
            "oficina",
            "telefono",
            "pantalla",
            "archivo",
        ],
    },
    "Fiesta": {
        "image": "images/convivio.svg",
        "words": [
            "pizza",
            "pastel",
            "globo",
            "musica",
            "regalo",
            "vela",
            "risa",
            "baile",
            "foto",
            "juego",
        ],
    },
}

RoomState = Dict[str, object]
ROOMS: Dict[str, RoomState] = {}


def _pick_category() -> Tuple[str, Dict[str, object]]:
    name = random.choice(list(CATEGORIES.keys()))
    return name, CATEGORIES[name]


def _generate_code(length: int = 4) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    while True:
        code = "".join(random.choice(alphabet) for _ in range(length))
        if code not in ROOMS:
            return code


def _ensure_room(code: str) -> RoomState | None:
    return ROOMS.get(code.upper())


def _find_player(room: RoomState, player_id: str) -> Dict[str, str] | None:
    for player in room["players"]:
        if player["id"] == player_id:
            return player
    return None


def _all_submitted(room: RoomState) -> bool:
    players = room["players"]
    if not players:
        return False
    return all(player["id"] in room["submissions"] for player in players)


def _all_voted(room: RoomState) -> bool:
    players = room["players"]
    if not players:
        return False
    return all(player["id"] in room["votes"] for player in players)


def _tally_votes(room: RoomState) -> Tuple[Dict[str, str] | None, list[Dict[str, object]]]:
    counts: Dict[str, int] = {}
    for target_id in room["votes"].values():
        counts[target_id] = counts.get(target_id, 0) + 1
    leaderboard = []
    for player in room["players"]:
        leaderboard.append(
            {"id": player["id"], "name": player["name"], "votes": counts.get(player["id"], 0)}
        )
    leaderboard.sort(key=lambda entry: (-entry["votes"], entry["name"].lower()))
    top_player = _find_player(room, leaderboard[0]["id"]) if leaderboard else None
    return top_player, leaderboard


def _is_mobile_user_agent(user_agent: str | None) -> bool:
    if not user_agent:
        return False
    user_agent = user_agent.lower()
    return any(keyword in user_agent for keyword in MOBILE_UA_KEYWORDS)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", error=None)


@app.route("/join", methods=["POST"])
def join():
    code = request.form.get("code", "").strip().upper()
    if not code:
        return render_template("index.html", error="Escribe el codigo de la sala.")
    if code not in ROOMS:
        return render_template("index.html", error="No encuentro esa sala. Pide el QR del monitor.")
    return redirect(url_for("room", code=code))


@app.route("/create", methods=["POST"])
def create_room():
    code = _generate_code()
    category_name, category_data = _pick_category()
    ROOMS[code] = {
        "code": code,
        "category_name": category_name,
        "category_data": category_data,
        "players": [],
        "submissions": {},
        "votes": {},
        "phase": "lobby",
        "real_word": None,
        "impostor_id": None,
        "notice": None,
        "host_id": None,
    }
    session.pop("player_id", None)
    session["room_code"] = code
    return redirect(url_for("room", code=code))


@app.route("/room/<code>", methods=["GET", "POST"])
def room(code: str):
    room_state = _ensure_room(code)
    if not room_state:
        return render_template("index.html", error="Ese enlace ya no existe. Crea una sala nueva.")

    player_id = session.get("player_id")
    player = _find_player(room_state, player_id) if player_id else None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if len(name) < 2:
            room_state["notice"] = "Escribe un nombre real, minimo 2 letras."
            return redirect(url_for("room", code=room_state["code"]))
        if not player and room_state["phase"] != "lobby":
            room_state["notice"] = "La partida ya empezo. Espera la siguiente ronda."
            return redirect(url_for("room", code=room_state["code"]))
        if not player:
            new_id = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(12))
            player = {"id": new_id, "name": name}
            room_state["players"].append(player)
            if not room_state.get("host_id"):
                room_state["host_id"] = new_id
            session["player_id"] = new_id
            session["room_code"] = room_state["code"]
        return redirect(url_for("room", code=room_state["code"]))

    notice = room_state.pop("notice", None)
    is_impostor = bool(player and room_state.get("impostor_id") == player["id"])
    is_host = bool(player and room_state.get("host_id") == player["id"])
    impostor, leaderboard = _tally_votes(room_state) if room_state["phase"] == "results" else (None, [])
    return render_template(
        "room.html",
        room=room_state,
        player=player,
        notice=notice,
        category_name=room_state["category_name"],
        category_data=room_state["category_data"],
        submission=room_state["submissions"].get(player_id) if player_id else None,
        has_voted=bool(player_id and room_state["votes"].get(player_id)),
        is_impostor=is_impostor,
        is_host=is_host,
        secret_word=room_state.get("real_word"),
        submissions_count=len(room_state["submissions"]),
        votes_count=len(room_state["votes"]),
        impostor=impostor,
        leaderboard=leaderboard,
    )

@app.route("/room/<code>/submit", methods=["POST"])
def submit_word(code: str):
    room_state = _ensure_room(code)
    if not room_state:
        return redirect(url_for("index"))

    player_id = session.get("player_id")
    player = _find_player(room_state, player_id) if player_id else None
    if not player or room_state["phase"] != "collect":
        return redirect(url_for("room", code=room_state["code"]))

    word = request.form.get("word", "").strip()
    if word:
        room_state["submissions"][player_id] = word
        if _all_submitted(room_state):
            room_state["phase"] = "voting"
    return redirect(url_for("room", code=room_state["code"]))

@app.route("/room/<code>/start", methods=["POST"])
def start_game(code: str):
    room_state = _ensure_room(code)
    if not room_state:
        return redirect(url_for("index"))
    player_id = session.get("player_id")
    if not player_id or room_state.get("host_id") != player_id:
        room_state["notice"] = "Solo el primer jugador puede iniciar la partida."
        return redirect(url_for("room", code=room_state["code"]))
    if not room_state["players"]:
        room_state["notice"] = "Necesitas al menos un jugador para iniciar."
        return redirect(url_for("room", code=room_state["code"]))

    room_state["real_word"] = random.choice(room_state["category_data"]["words"])
    room_state["impostor_id"] = random.choice(room_state["players"])["id"]
    room_state["phase"] = "collect"
    room_state["submissions"] = {}
    room_state["votes"] = {}
    return redirect(url_for("room", code=room_state["code"]))


@app.route("/room/<code>/vote", methods=["POST"])
def vote(code: str):
    room_state = _ensure_room(code)
    if not room_state:
        return redirect(url_for("index"))

    player_id = session.get("player_id")
    player = _find_player(room_state, player_id) if player_id else None
    if not player or room_state["phase"] != "voting":
        return redirect(url_for("room", code=room_state["code"]))

    target_id = request.form.get("vote", "").strip()
    if _find_player(room_state, target_id):
        room_state["votes"][player_id] = target_id
        if _all_voted(room_state):
            room_state["phase"] = "results"
    return redirect(url_for("room", code=room_state["code"]))


@app.route("/room/<code>/monitor", methods=["GET", "POST"])
def monitor(code: str):
    room_state = _ensure_room(code)
    if not room_state:
        return redirect(url_for("index"))

    if _is_mobile_user_agent(request.user_agent.string):
        return render_template("monitor_blocked.html", room=room_state)

    player_id = session.get("player_id")
    player = _find_player(room_state, player_id) if player_id else None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if len(name) < 2:
            room_state["notice"] = "Escribe un nombre real, minimo 2 letras."
            return redirect(url_for("monitor", code=room_state["code"]))
        if not player and room_state["phase"] != "lobby":
            room_state["notice"] = "La partida ya empezo. Espera la siguiente ronda."
            return redirect(url_for("monitor", code=room_state["code"]))
        if not player:
            new_id = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(12))
            player = {"id": new_id, "name": name}
            room_state["players"].append(player)
            session["player_id"] = new_id
            session["room_code"] = room_state["code"]
        return redirect(url_for("monitor", code=room_state["code"]))

    notice = room_state.pop("notice", None)
    impostor, leaderboard = _tally_votes(room_state) if room_state["phase"] == "results" else (None, [])
    return render_template(
        "monitor.html",
        room=room_state,
        category_name=room_state["category_name"],
        category_data=room_state["category_data"],
        submissions_count=len(room_state["submissions"]),
        votes_count=len(room_state["votes"]),
        impostor=impostor,
        leaderboard=leaderboard,
        notice=notice,
        monitor_player=player,
        main_class="monitor-card",
    )


@app.route("/room/<code>/state", methods=["GET"])
def room_state(code: str):
    room_state = _ensure_room(code)
    if not room_state:
        return jsonify({"error": "not found"}), 404
    submissions_list = []
    for player in room_state["players"]:
        if player["id"] in room_state["submissions"]:
            submissions_list.append(
                {"name": player["name"], "word": room_state["submissions"][player["id"]]}
            )
    return jsonify(
        {
            "phase": room_state["phase"],
            "players_count": len(room_state["players"]),
            "submissions_count": len(room_state["submissions"]),
            "votes_count": len(room_state["votes"]),
            "submissions": submissions_list,
        }
    )


@app.route("/room/<code>/reset", methods=["POST"])
def reset_round(code: str):
    room_state = _ensure_room(code)
    if not room_state:
        return redirect(url_for("index"))

    category_name, category_data = _pick_category()
    room_state["category_name"] = category_name
    room_state["category_data"] = category_data
    room_state["phase"] = "lobby"
    room_state["submissions"] = {}
    room_state["votes"] = {}
    room_state["real_word"] = None
    room_state["impostor_id"] = None
    room_state["notice"] = "Nueva ronda lista. Puedes iniciar de nuevo."
    return redirect(url_for("room", code=room_state["code"]))


@app.route("/room/<code>/qr", methods=["GET"])
def room_qr(code: str):
    room_state = _ensure_room(code)
    if not room_state:
        return redirect(url_for("index"))

    join_url = url_for("room", code=room_state["code"], _external=True)
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(join_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return send_file(buffer, mimetype="image/png")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5011, debug=True)
