
from math import inf

WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
]

def new_board():
    return [""] * 9

def winning_line(board):
    for line in WIN_LINES:
        a, b, c = line
        if board[a] and board[a] == board[b] == board[c]:
            return line
    return None

def winner(board):
    line = winning_line(board)
    return board[line[0]] if line else ""

def is_draw(board):
    return not winner(board) and all(board)

def game_over(board):
    return bool(winner(board)) or is_draw(board)

def legal_moves(board):
    return [i for i, cell in enumerate(board) if not cell]

def make_move(board, index, symbol):
    if symbol not in ("X", "O"):
        raise ValueError("Symbol must be X or O.")
    if index not in range(9) or board[index]:
        raise ValueError("Invalid move.")
    if game_over(board):
        raise ValueError("The game is over.")
    result = board.copy()
    result[index] = symbol
    return result

def minimax(board, ai, turn, alpha=-inf, beta=inf, depth=0):
    won = winner(board)
    if won == ai:
        return 10 - depth
    if won:
        return depth - 10
    if is_draw(board):
        return 0

    opponent = "O" if ai == "X" else "X"

    if turn == ai:
        best = -inf
        for move in legal_moves(board):
            child = board.copy()
            child[move] = turn
            best = max(
                best,
                minimax(child, ai, opponent, alpha, beta, depth + 1),
            )
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return int(best)

    best = inf
    for move in legal_moves(board):
        child = board.copy()
        child[move] = turn
        best = min(
            best,
            minimax(child, ai, opponent, alpha, beta, depth + 1),
        )
        beta = min(beta, best)
        if beta <= alpha:
            break
    return int(best)

def score_move(board, move, ai="O"):
    child = board.copy()
    child[move] = ai
    opponent = "O" if ai == "X" else "X"
    return minimax(child, ai, opponent, depth=1)

def choose_move(board, ai="O", difficulty="Unbeatable"):
    moves = legal_moves(board)
    if not moves or game_over(board):
        return None

    opponent = "O" if ai == "X" else "X"
    difficulty = difficulty.lower()

    # Easy: take an immediate win, otherwise choose a simple move.
    if difficulty == "easy":
        for move in moves:
            child = board.copy()
            child[move] = ai
            if winner(child) == ai:
                return move
        return moves[0]

    # Medium: win, block, then use a positional preference.
    if difficulty == "medium":
        for move in moves:
            child = board.copy()
            child[move] = ai
            if winner(child) == ai:
                return move
        for move in moves:
            child = board.copy()
            child[move] = opponent
            if winner(child) == opponent:
                return move
        preference = [4, 0, 2, 6, 8, 1, 3, 5, 7]
        return next(move for move in preference if move in moves)

    # Unbeatable: maximise the Minimax score.
    scores = [(score_move(board, move, ai), move) for move in moves]
    best_score = max(score for score, _ in scores)
    best_moves = [move for score, move in scores if score == best_score]
    preference = [4, 0, 2, 6, 8, 1, 3, 5, 7]
    return next(move for move in preference if move in best_moves)

def explain_move(board, move, ai="O"):
    if move not in legal_moves(board):
        return "That cell is not available."

    child = board.copy()
    child[move] = ai
    if winner(child) == ai:
        return f"Cell {move + 1} completes a winning line."

    score = score_move(board, move, ai)
    if score > 0:
        result = "can force a win against optimal play"
    elif score < 0:
        result = "eventually loses against optimal opposition"
    else:
        result = "can secure a draw against optimal play"

    return f"Cell {move + 1} {result}, according to Minimax search."
