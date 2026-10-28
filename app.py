
import os
import requests
import streamlit as st
from dotenv import load_dotenv

from game_engine import (
    new_board, make_move, winner, winning_line, is_draw,
    game_over, choose_move, explain_move,
)
from llm_coach import AICoach

load_dotenv()

st.set_page_config(
    page_title="XO Love Arena 💕",
    page_icon="💗",
    layout="centered",
)

API_URL = os.getenv("ARENA_API_URL", "http://127.0.0.1:8000").rstrip("/")

st.markdown("""
<style>
/* Main app: deep black background with a subtle purple glow */
.stApp {
    background: radial-gradient(ellipse at top, #21102a 0%, #0b0910 48%, #050507 100%);
    color: #f8eaf4;
}
.block-container { max-width: 900px; padding-top: 1.5rem; }
.hero {
    background: linear-gradient(120deg, #ff4f9a, #8b5cf6);
    color: white; padding: 24px; border-radius: 24px;
    text-align: center; box-shadow: 0 8px 28px #d6338455;
}
.hero h1 {font-size: 2.3rem; margin: 0;}
.hero p {margin: 8px 0 0 0;}

/* Readable text on dark background */
.stMarkdown, .stMarkdown p, .stCaption, label,
div[data-testid="stMetricLabel"], div[data-testid="stMetricValue"],
div[data-testid="stRadio"] label, div[data-testid="stSelectbox"] label {
    color: #f8eaf4;
}

/* Dark inputs and dropdowns */
div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
div[data-baseweb="textarea"] > div {
    background: #17121d !important;
    color: #fff !important;
    border-color: #a83d7b !important;
}
input, textarea { color: #fff !important; caret-color: #ff83b5 !important; }
div[data-baseweb="select"] * { color: #fff !important; }

/* Buttons */
div.stButton > button, div.stFormSubmitButton > button {
    border-radius: 14px; border: 1px solid #d94c9b;
    font-weight: 700; background: #211522; color: #ffe8f5;
}
div.stButton > button:hover, div.stFormSubmitButton > button:hover {
    border-color: #b79aff; background: #38203c; color: white;
}

/* Style only the nine Tic-Tac-Toe squares */
div.st-key-tic_tac_toe_board div.stButton > button {
    border-radius: 14px !important; min-height: 90px !important;
    border: 3px solid #ff4f9a !important; font-size: 28px !important;
    font-weight: 900 !important; background: #151019 !important;
    color: #ffd5eb !important; box-shadow: 0 3px 12px #d6338430;
    transition: all 0.15s ease-in-out;
}
div.st-key-tic_tac_toe_board div.stButton > button:hover:not(:disabled) {
    border-color: #a78bfa !important; background: #2a1930 !important;
    color: #ffffff !important; transform: scale(1.02);
}
div.st-key-tic_tac_toe_board div.stButton > button:disabled {
    opacity: 1 !important; background: #151019 !important;
    color: #ffd5eb !important; border-color: #ff4f9a !important;
}

/* Dark coach chat cards */
div[data-testid="stChatMessage"] {
    background: #17121d; color: #f8eaf4;
    border: 1px solid #74345f; border-radius: 16px;
}
div[data-testid="stChatMessage"] p { color: #f8eaf4; }
div[data-testid="stExpander"] details,
div[data-testid="stDataFrame"] {
    background: #100d15; border-color: #74345f;
}
hr { border-color: #633052; }
</style>
<div class="hero">
    <h1>💗 XO LOVE ARENA 💗</h1>
    <p>Two hearts · One board · Endless fun</p>
</div>
""", unsafe_allow_html=True)


@st.cache_resource
def get_coach():
    return AICoach()


coach = get_coach()


def api_request(method, path, **kwargs):
    response = requests.request(
        method, API_URL + path, timeout=5, **kwargs
    )
    if not response.ok:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise RuntimeError(str(detail))
    return response.json()


# Initialise local game state.
defaults = {
    "mode": "Play with AI",
    "local_board": new_board(),
    "local_turn": "X",
    "difficulty": "Unbeatable",
    "local_scores": {"You": 0, "AI": 0, "Draws": 0},
    "local_result_counted": False,
    "online": None,
    "chat": [],
    "last_ai_explanation": "",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy() if isinstance(value, dict) else value


def reset_local():
    st.session_state.local_board = new_board()
    st.session_state.local_turn = "X"
    st.session_state.local_result_counted = False
    st.session_state.last_ai_explanation = ""


def local_finish():
    board = st.session_state.local_board
    if not game_over(board) or st.session_state.local_result_counted:
        return

    won_by = winner(board)
    if won_by == "X":
        st.session_state.local_scores["You"] += 1
    elif won_by == "O":
        st.session_state.local_scores["AI"] += 1
    else:
        st.session_state.local_scores["Draws"] += 1

    st.session_state.local_result_counted = True


def ai_turn():
    board = st.session_state.local_board
    if (
        st.session_state.mode == "Play with AI"
        and st.session_state.local_turn == "O"
        and not game_over(board)
    ):
        move = choose_move(
            board, "O", st.session_state.difficulty
        )
        if move is not None:
            st.session_state.last_ai_explanation = explain_move(
                board, move, "O"
            )
            st.session_state.local_board = make_move(board, move, "O")
            st.session_state.local_turn = "X"
            local_finish()


# Select game mode.
mode = st.radio(
    "Choose your adventure 💕",
    ["Play with AI", "Couple Mode (online)", "Two players (same device)"],
    horizontal=False,
)
if mode != st.session_state.mode:
    st.session_state.mode = mode
    st.session_state.online = None
    reset_local()
    st.rerun()

if mode == "Play with AI":
    st.selectbox(
        "Choose AI difficulty",
        ["Easy", "Medium", "Unbeatable"],
        key="difficulty",
    )
    st.caption("You are X 💗 The AI is O 🤖")

elif mode == "Couple Mode (online)":
    st.markdown("### 💌 Play together from separate phones")
    st.caption(
        "One person creates a room and shares the code. "
        "The other joins using that code."
    )

    with st.form("create_room_form"):
        host_name = st.text_input("Your name", value="", max_chars=24)
        create = st.form_submit_button("💗 Create a room")
    if create:
        if not host_name.strip():
            st.error("Please enter your name.")
        else:
            try:
                result = api_request(
                    "POST", "/rooms", json={"name": host_name.strip()}
                )
                st.session_state.online = {
                    "code": result["code"],
                    "token": result["token"],
                    "symbol": result["symbol"],
                }
                st.rerun()
            except Exception as exc:
                st.error(f"Could not create room: {exc}")

    with st.form("join_room_form"):
        join_name = st.text_input("Your name ", max_chars=24)
        room_code = st.text_input("Room code", max_chars=6).upper().strip()
        join = st.form_submit_button("💞 Join your room")
    if join:
        if not join_name.strip() or not room_code:
            st.error("Enter your name and room code.")
        else:
            try:
                result = api_request(
                    "POST", f"/rooms/{room_code}/join",
                    json={"name": join_name.strip()},
                )
                st.session_state.online = {
                    "code": result["code"],
                    "token": result["token"],
                    "symbol": result["symbol"],
                }
                st.rerun()
            except Exception as exc:
                st.error(f"Could not join room: {exc}")

    if st.session_state.online:
        online = st.session_state.online
        st.success(f"Your room code: **{online['code']}**")
        st.info(
            f"You are **{online['symbol']}**. "
            "Share the room code with the other player."
        )
        st.code(online["code"])
        if st.button("Leave room"):
            st.session_state.online = None
            st.rerun()

elif mode == "Two players (same device)":
    st.caption("Take turns: X goes first, followed by O.")


# Load current online room state and refresh while playing.
room = None
if mode == "Couple Mode (online)" and st.session_state.online:
    try:
        from streamlit_autorefresh import st_autorefresh

        st_autorefresh(interval=2000, key="online_refresh")
    except ImportError:
        st.caption("Auto-refresh unavailable; use Refresh game below.")

    try:
        room = api_request(
            "GET", f"/rooms/{st.session_state.online['code']}"
        )
    except Exception as exc:
        st.error(f"Cannot reach the game server: {exc}")
        st.caption("Check ARENA_API_URL and make sure the API is running.")

def draw_board(board, mode_name, online_room=None):
    line = winning_line(board)
    winner_symbol = winner(board)

    if winner_symbol:
        st.success(f"🏆 {winner_symbol} wins! Sending extra hugs! 💗")
    elif is_draw(board):
        st.info("🤝 A draw! Perfect excuse for a rematch. 💞")
    else:
        st.info(f"Next turn: **{online_room['turn'] if online_room else st.session_state.local_turn}**")

    if online_room:
        players = online_room["players"]
        st.markdown(
            f"💗 **X:** {players.get('X') or 'Waiting for player'}"
            f" &nbsp;&nbsp; 💜 **O:** {players.get('O') or 'Waiting for player'}"
        )

    with st.container(key="tic_tac_toe_board"):
        for row in range(3):
            columns = st.columns(3, gap="small")
            for col in range(3):
                index = row * 3 + col
                symbol = board[index]
                if line and index in line:
                    label = f"💖 {symbol} 💖"
                elif symbol == "X":
                    label = "💗 X"
                elif symbol == "O":
                    label = "💜 O"
                else:
                    label = "♡"

                disabled = bool(symbol) or game_over(board)

                if online_room:
                    online = st.session_state.online
                    disabled = (
                        disabled
                        or online_room["occupied"] < 2
                        or online_room["turn"] != online["symbol"]
                        or online_room["status"] != "playing"
                    )
                elif mode_name == "Play with AI":
                    disabled = disabled or st.session_state.local_turn != "X"

                if columns[col].button(
                    label,
                    key=f"board_{mode_name}_{index}",
                    disabled=disabled,
                    use_container_width=True,
                ):
                    if online_room:
                        try:
                            api_request(
                                "POST",
                                f"/rooms/{online_room['code']}/move",
                                json={
                                    "token": st.session_state.online["token"],
                                    "index": index,
                                },
                            )
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Move rejected: {exc}")
                    else:
                        symbol_to_play = st.session_state.local_turn
                        st.session_state.local_board = make_move(
                            st.session_state.local_board, index, symbol_to_play
                        )
                        st.session_state.local_turn = (
                            "O" if symbol_to_play == "X" else "X"
                        )
                        local_finish()
                        ai_turn()
                        st.rerun()


if mode == "Couple Mode (online)":
    if room:
        draw_board(room["board"], mode, room)

        if room["occupied"] < 2:
            st.warning("Waiting for your favourite person to join... 💌")

        if room["status"] != "playing":
            st.balloons()
            if st.button("💞 Play another round"):
                try:
                    api_request(
                        "POST",
                        f"/rooms/{room['code']}/rematch",
                        json={
                            "token": st.session_state.online["token"],
                            "index": 0,
                        },
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not start rematch: {exc}")

elif mode in ("Play with AI", "Two players (same device)"):
    board = st.session_state.local_board
    draw_board(board, mode)

    if mode == "Play with AI" and st.session_state.last_ai_explanation:
        with st.expander("🧠 Why did the AI choose that move?"):
            st.write(st.session_state.last_ai_explanation)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Restart round", use_container_width=True):
            reset_local()
            st.rerun()
    with col2:
        if st.button("🧹 Reset scores", use_container_width=True):
            st.session_state.local_scores = {
                "You": 0, "AI": 0, "Draws": 0
            }
            reset_local()
            st.rerun()

    score_cols = st.columns(3)
    for column, (name, score) in zip(
        score_cols, st.session_state.local_scores.items()
    ):
        column.metric(name, score)


# RAG + LLM assistant.
st.divider()
st.markdown("## 🧸 Ask the XO Love Coach")
st.caption("Ask about strategies, the rules, Minimax, RAG, or the AI project.")

for item in st.session_state.chat:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])
        if item.get("sources"):
            st.caption("Knowledge sources: " + ", ".join(item["sources"]))

question = st.chat_input("Ask your game coach something...")
if question:
    st.session_state.chat.append({"role": "user", "content": question})

    board_context = ""
    if room:
        board_context = (
            f"Online board: {room['board']}; "
            f"turn: {room['turn']}; status: {room['status']}"
        )
    elif mode != "Couple Mode (online)":
        board_context = (
            f"Local board: {st.session_state.local_board}; "
            f"turn: {st.session_state.local_turn}"
        )

    with st.spinner("Looking through the game guide..."):
        result = coach.answer(question, board_context)

    st.session_state.chat.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"],
    })
    st.rerun()

with st.expander("📈 Multiplayer match statistics"):
    try:
        stats = api_request("GET", "/stats")
        st.json(stats["totals"])
        if stats["recent_matches"]:
            st.dataframe(stats["recent_matches"], use_container_width=True)
    except Exception:
        st.caption("Statistics are available when the multiplayer server is running.")
