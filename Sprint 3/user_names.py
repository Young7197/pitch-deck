import importlib.util
from flask import request, redirect, render_template_string, session


# -----------------------------
# Load existing Flask app
# -----------------------------
APP_FILE = "app.py"

spec = importlib.util.spec_from_file_location("pitch_app", APP_FILE)
pitch_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pitch_app)

app = pitch_app.app
app.secret_key = "pitch-game-secret-key"


# -----------------------------
# Bot names
# -----------------------------
BOT_NAMES = ["Maverick", "Ace", "Bandit"]


def apply_player_names():
    """
    Rename Player 1 to the username and give bots custom names.
    """
    if pitch_app.deck is None:
        return

    username = session.get("username", "Player 1")

    pitch_app.deck.player1.name = username
    pitch_app.deck.player2.name = BOT_NAMES[0]
    pitch_app.deck.player3.name = BOT_NAMES[1]
    pitch_app.deck.player4.name = BOT_NAMES[2]

    pitch_app.deck.players = [
        pitch_app.deck.player1,
        pitch_app.deck.player2,
        pitch_app.deck.player3,
        pitch_app.deck.player4,
    ]

    if pitch_app.deck.round:
        pitch_app.deck.round.players = pitch_app.deck.players


# -----------------------------
# Username page
# -----------------------------
USERNAME_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Enter Username</title>
    <style>
        body {
            background-color: lightgreen;
            font-family: Georgia, serif;
            text-align: center;
            padding-top: 120px;
        }

        h1 {
            font-size: 48px;
        }

        input {
            width: 260px;
            height: 40px;
            font-size: 20px;
            padding: 5px;
            border-radius: 8px;
            border: 2px solid darkgreen;
            text-align: center;
        }

        button {
            margin-top: 20px;
            width: 200px;
            height: 55px;
            font-size: 20px;
            background-color: darkgreen;
            color: white;
            border-radius: 8px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <h1>Enter Your Username</h1>

    <form method="POST" action="/set_username">
        <input 
            type="text" 
            name="username" 
            placeholder="Username" 
            maxlength="20" 
            required
        >
        <br>
        <button type="submit">Continue</button>
    </form>
</body>
</html>
"""


@app.route("/")
def username_screen():
    return render_template_string(USERNAME_PAGE)


@app.route("/set_username", methods=["POST"])
def set_username():
    username = request.form.get("username", "").strip()

    if not username:
        username = "Player 1"

    session["username"] = username
    return redirect("/new_game")


# -----------------------------
# Patch start_game
# -----------------------------
original_start_game = pitch_app.app.view_functions["start_game"]


def named_start_game():
    """
    Runs original start_game, then applies username and bot names.
    """
    response = original_start_game()
    apply_player_names()
    return response


pitch_app.app.view_functions["start_game"] = named_start_game


# -----------------------------
# Patch game page
# -----------------------------
original_home = pitch_app.app.view_functions["home"]


def named_home():
    """
    Make sure names are applied whenever /game loads.
    """
    apply_player_names()
    return original_home()


pitch_app.app.view_functions["home"] = named_home


# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    pitch_app.app.run(debug=True)