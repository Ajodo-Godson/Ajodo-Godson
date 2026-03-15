import os
import chess
import chess.svg
import chess.pgn
import io
from urllib.parse import quote_plus
from github import Github

# Initialize Environment
g = Github(os.environ["GITHUB_TOKEN"])
repo = g.get_repo("Ajodo-Godson/Ajodo-Godson")
issue_title = os.environ.get("ISSUE_TITLE", "")
ISSUES_NEW_URL = f"{repo.html_url}/issues/new"

GAME_STATE_FILE = "data/game_state.pgn"
BOARD_SVG_PATH = "data/chess_board.svg"
README_PATH = "README.md"
# Delimiters for the README section that is rewritten each run.
START_TAG = "<!-- CHESS-START -->"
END_TAG = "<!-- CHESS-END -->"

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
next_move_title = quote_plus("Game: Move YOUR_MOVE")
reset_title = quote_plus("Game: Reset")
next_move_link = f"[Next Move]({ISSUES_NEW_URL}?title={next_move_title})"
reset_link = f"[Reset]({ISSUES_NEW_URL}?title={reset_title})"

if issue_title.startswith("Game: Move "):
    move_san = issue_title.replace("Game: Move ", "", 1).strip()
    try:
        move = board.parse_san(move_san)
        if move in board.legal_moves:
            board.push(move)
            turn = "Black" if board.turn == chess.BLACK else "White"
            status = f"Last move: {move_san}. Next turn: {turn}."
        else:
            status = f"Illegal move: {move_san}."
    except ValueError:
        status = "Invalid syntax. Use SAN (e.g., e4, Nf3)."
elif issue_title.strip() == "Game: Reset":
    board.reset()
    status = "Game reset. White to move."

# Save State
with open(GAME_STATE_FILE, "w") as f:
    print(chess.pgn.Game.from_board(board), file=f)

# Render board SVG as a tracked file GitHub can display in README.
svg_data = chess.svg.board(board=board, size=400)
with open(BOARD_SVG_PATH, "w") as f:
    f.write(svg_data)

board_render = "![Chess Board](data/chess_board.svg)"

# Update README
with open(README_PATH, "r") as f:
    content = f.read()

start_idx = content.find(START_TAG)
end_idx = content.find(END_TAG)

if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
    raise ValueError(
        "README markers not found. Add <!-- CHESS-START --> and <!-- CHESS-END --> markers."
    )

start_idx += len(START_TAG)

new_content = content[:start_idx] + \
              f"\n\n{board_render}\n\n**SESSION_LOG:** {status}\n\n" + \
              f"{next_move_link} | {reset_link}\n" + \
              content[end_idx:]

with open(README_PATH, "w") as f:
    f.write(new_content)
