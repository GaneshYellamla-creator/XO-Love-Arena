
import secrets
import string
import threading
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from game_engine import new_board, make_move, winner, is_draw, game_over
from storage import save_match, get_stats, get_recent_matches

app = FastAPI(title="XO Love Arena API")
rooms = {}
rooms_lock = threading.RLock()


class CreateRoom(BaseModel):
    name: str = Field(min_length=1, max_length=24)


class JoinRoom(BaseModel):
    name: str = Field(min_length=1, max_length=24)


class MoveRequest(BaseModel):
    token: str
    index: int = Field(ge=0, le=8)


def create_code():
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "".join(secrets.choice(alphabet) for _ in range(6))
        if code not in rooms:
            return code


def public_state(room):
    board = room["board"]
    won_by = winner(board)

    return {
        "code": room["code"],
        "board": board,
        "turn": room["turn"],
        "players": room["players"],
        "occupied": len(room["tokens"]),
        "status": (
            "won" if won_by else
            "draw" if is_draw(board) else
            "playing"
        ),
        "winner": won_by,
        "winning_line": (
            next(
                (
                    list(line) for line in [
                        (0, 1, 2), (3, 4, 5), (6, 7, 8),
                        (0, 3, 6), (1, 4, 7), (2, 5, 8),
                        (0, 4, 8), (2, 4, 6),
                    ]
                    if board[line[0]]
                    and board[line[0]] == board[line[1]] == board[line[2]]
                ),
                None,
            )
        ),
        "last_move": room["last_move"],
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "XO Love Arena"}


@app.post("/rooms")
def create_room(data: CreateRoom):
    name = data.name.strip()
    if not name:
        raise HTTPException(400, "Please enter a player name.")

    with rooms_lock:
        code = create_code()
        token = secrets.token_urlsafe(24)

        rooms[code] = {
            "code": code,
            "board": new_board(),
            "turn": "X",
            "players": {"X": name, "O": ""},
            "tokens": {token: "X"},
            "last_move": None,
            "saved": False,
        }

        return {
            "code": code,
            "token": token,
            "symbol": "X",
            "state": public_state(rooms[code]),
        }


@app.post("/rooms/{code}/join")
def join_room(code: str, data: JoinRoom):
    name = data.name.strip()
    code = code.upper()

    if not name:
        raise HTTPException(400, "Please enter a player name.")

    with rooms_lock:
        room = rooms.get(code)
        if not room:
            raise HTTPException(404, "Room not found. Check the room code.")
        if len(room["tokens"]) >= 2:
            raise HTTPException(409, "This room already has two players.")
        if game_over(room["board"]):
            raise HTTPException(409, "This match has already finished.")

        token = secrets.token_urlsafe(24)
        room["tokens"][token] = "O"
        room["players"]["O"] = name

        return {
            "code": code,
            "token": token,
            "symbol": "O",
            "state": public_state(room),
        }


@app.get("/rooms/{code}")
def get_room(code: str):
    with rooms_lock:
        room = rooms.get(code.upper())
        if not room:
            raise HTTPException(404, "Room not found.")
        return public_state(room)


@app.post("/rooms/{code}/move")
def play_move(code: str, data: MoveRequest):
    with rooms_lock:
        room = rooms.get(code.upper())
        if not room:
            raise HTTPException(404, "Room not found.")

        symbol = room["tokens"].get(data.token)
        if symbol is None:
            raise HTTPException(403, "Invalid player session.")
        if len(room["tokens"]) < 2:
            raise HTTPException(409, "Waiting for the other player to join.")
        if game_over(room["board"]):
            raise HTTPException(409, "This match is already over.")
        if symbol != room["turn"]:
            raise HTTPException(409, "It is not your turn.")

        try:
            room["board"] = make_move(room["board"], data.index, symbol)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

        room["last_move"] = {
            "symbol": symbol,
            "index": data.index,
        }
        room["turn"] = "O" if symbol == "X" else "X"

        won_by = winner(room["board"])
        result = won_by if won_by else "Draw" if is_draw(room["board"]) else None

        if result and not room["saved"]:
            save_match(
                room["code"],
                room["players"]["X"],
                room["players"]["O"],
                result,
            )
            room["saved"] = True

        return public_state(room)


@app.get("/stats")
def stats():
    return {
        "totals": get_stats(),
        "recent_matches": get_recent_matches(),
    }


@app.post("/rooms/{code}/rematch")
def rematch(code: str, data: MoveRequest):
    # Any player can request a fresh board after the previous game.
    with rooms_lock:
        room = rooms.get(code.upper())
        if not room:
            raise HTTPException(404, "Room not found.")
        if data.token not in room["tokens"]:
            raise HTTPException(403, "Invalid player session.")
        if not game_over(room["board"]):
            raise HTTPException(409, "Finish the current match first.")

        room["board"] = new_board()
        room["turn"] = "X"
        room["last_move"] = None
        room["saved"] = False
        return public_state(room)
