import os
import io
from urllib.parse import quote_plus, unquote_plus

import chess
import chess.pgn
import chess.svg
from github import Github


# ----------------------------
# Config
# ----------------------------
REPO_FULL_NAME = "Ajodo-Godson/Ajodo-Godson"
GAME_STATE_FILE = "data/game_state.pgn"
BOARD_SVG_PATH = "data/chess_board.svg"
README_PATH = "README.md"

START_TAG = "<!-- CHESS-START -->"
END_TAG = "<!-- CHESS-END -->"


# ----------------------------
# Helpers
# ----------------------------
def ensure_data_dir() -> None:
    os.makedirs("data", exist_ok=True)


def load_board() -> chess.Board:
    board = chess.Board()
    if not os.path.exists(GAME_STATE_FILE):
        return board

    with open(GAME_STATE_FILE, "r", encoding="utf-8") as f:
        pgn_content = f.read().strip()

    if not pgn_content:
        return board

    game = chess.pgn.read_game(io.StringIO(pgn_content))
    if game:
        board = game.end().board()
    return board


def normalize_issue_title(raw_title: str) -> str:
    # Accept normal or URL-style titles
    # e.g., "Game: Reset", "Game:+Reset", "Game%3A+Reset"
    t = raw_title.strip()
    t = unquote_plus(t)
    t = " ".join(t.split())  # normalize repeated whitespace
    return t


def process_issue(board: chess.Board, issue_title_raw: str) -> str:
    title = normalize_issue_title(issue_title_raw)
    status = "White to move."

    if title.startswith("Game: Move "):
        move_san = title.replace("Game: Move ", "", 1).strip()
        if not move_san:
            return "Invalid syntax. Use: Game: Move <SAN> (e.g., Game: Move e4)."

        try:
            move = board.parse_san(move_san)
            if move in board.legal_moves:
                board.push(move)
                turn = "Black" if board.turn == chess.BLACK else "White"
                status = f"Last move: {move_san}. Next turn: {turn}."
            else:
                status = f"Illegal move: {move_san}."
        except ValueError:
            status = "Invalid syntax. Use SAN (e.g., e4, Nf3, O-O)."

    elif title == "Game: Reset":
        board.reset()
        status = "Game reset. White to move."

    return status


def save_state(board: chess.Board) -> None:
    with open(GAME_STATE_FILE, "w", encoding="utf-8") as f:
        print(chess.pgn.Game.from_board(board), file=f)

    svg_data = chess.svg.board(board=board, size=400)
    with open(BOARD_SVG_PATH, "w", encoding="utf-8") as f:
        f.write(svg_data)


def build_links(repo_html_url: str) -> tuple[str, str]:
    issues_new_url = f"{repo_html_url}/issues/new"

    # GitHub prefill works reliably with + for spaces
    next_move_title = quote_plus("Game: Move YOUR_MOVE")
    reset_title = quote_plus("Game: Reset")

    next_move_link = f"[Next Move]({issues_new_url}?title={next_move_title})"
    reset_link = f"[Reset]({issues_new_url}?title={reset_title})"
    return next_move_link, reset_link


def update_readme(status: str, next_move_link: str, reset_link: str) -> None:
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    start_idx = content.find(START_TAG)
    end_idx = content.find(END_TAG)

    if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
        raise ValueError(
            "README markers not found. Add <!-- CHESS-START --> and <!-- CHESS-END -->."
        )

    start_idx += len(START_TAG)

    board_render = "![Chess Board](data/chess_board.svg)"
    replacement = (
        f"\n\n{board_render}\n\n"
        f"**SESSION_LOG:** {status}\n\n"
        f"{next_move_link} | {reset_link}\n"
    )

    new_content = content[:start_idx] + replacement + content[end_idx:]

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


# ----------------------------
# Main
# ----------------------------
def main() -> None:
    ensure_data_dir()

    token = os.environ.get("GITHUB_TOKEN")
    issue_title = os.environ.get("ISSUE_TITLE", "")

    if not token:
        raise RuntimeError("GITHUB_TOKEN is required.")

    g = Github(token)
    repo = g.get_repo(REPO_FULL_NAME)

    board = load_board()
    status = process_issue(board, issue_title)
    save_state(board)

    next_move_link, reset_link = build_links(repo.html_url)
    update_readme(status, next_move_link, reset_link)


if __name__ == "__main__":
    main()