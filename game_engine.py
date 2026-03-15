import os
import chess
import chess.svg
import chess.pgn
import io
import base64
from github import Github

# Initialize Environment
g = Github(os.environ["GITHUB_TOKEN"])
repo = g.get_repo("Ajodo-Godson/Ajodo-Godson")
issue_title = os.environ.get("ISSUE_TITLE", "")

GAME_STATE_FILE = "data/game_state.pgn"
README_PATH = "README.md"
START_TAG = ""
END_TAG = ""

if not os.path.exists("data"):
    os.makedirs("data")

# State Management
board = chess.Board()
if os.path.exists(GAME_STATE_FILE):
    with open(GAME_STATE_FILE, "r") as f:
        pgn_content = f.read()
    if pgn_content:
        game = chess.pgn.read_game(io.StringIO(pgn_content))
        if game:
            board = game.end().board()

# Process Input
status = "White to move."
if "Move" in issue_title:
    move_san = issue_title.split("Move ")[-1].strip()
    try:
        move = board.parse_san(move_san)
        if move in board.legal_moves:
            board.push(move)
            turn = "Black" if board.turn == chess.BLACK else "White"
            status = f"Last move: {move_san}. Next turn: {turn}."
        else:
            status = f"Illegal move: {move_san}."
    except:
        status = "Invalid syntax. Use SAN (e.g., e4, Nf3)."
elif "Reset" in issue_title:
    board.reset()
    status = "Game reset. White to move."

# Save State
with open(GAME_STATE_FILE, "w") as f:
    print(chess.pgn.Game.from_board(board), file=f)

# Render SVG to Base64
svg_data = chess.svg.board(board=board, size=400).encode("utf-8")
encoded = base64.b64encode(svg_data).decode("utf-8")
board_render = f'<img src="data:image/svg+xml;base64,{encoded}" width="400" />'

# Update README
with open(README_PATH, "r") as f:
    content = f.read()

start_idx = content.find(START_TAG) + len(START_TAG)
end_idx = content.find(END_TAG)

new_content = content[:start_idx] + \
              f"\n\n{board_render}\n\n**SESSION_LOG:** {status}\n\n" + \
              f"[Next Move](https://github.com/Ajodo-Godson/Ajodo-Godson/issues/new?title=Game:+Move+YOUR_MOVE) | " + \
              f"[Reset](https://github.com/Ajodo-Godson/Ajodo-Godson/issues/new?title=Game:+Reset)\n" + \
              content[end_idx:]

with open(README_PATH, "w") as f:
    f.write(new_content)