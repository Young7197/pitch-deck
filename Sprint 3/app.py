#Libraries needed
from pathlib import Path
from flask import Flask, request, render_template, redirect, jsonify, send_from_directory
import random

# Initialize Flask
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

app = Flask(
    __name__,
    template_folder=str(CURRENT_DIR),
    static_folder=str(PROJECT_ROOT / "static"),
    static_url_path="/static",
)

#Initializing global variables
game = None
deck = None
game_controller = None


#Deck Object
class Deck:
    #Constructor
    def __init__(self):
        #Defining suits and their corresponding ranks
        self.suits = ["Spades", "Clubs", "Hearts", "Diamonds"]
        self.spades = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
        self.clubs = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
        self.hearts = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
        self.diamonds = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]

        #Defining Players (Player1, Player2, Player3, Dealer)
        self.player1 = Player("Player 1") #User
        self.player2 = Bot("Player 2")    #Bot
        self.player3 = Bot("Player 3")    #Bot
        self.player4 = Bot("Player 4")    #Bot

        self.players = [self.player1, self.player2, self.player3, self.player4]

        #Defining the list to keep track of played cards
        self.played_cards = []

        #Defining the game state
        self.round = Round(
            round_number=1,
            players=self.players,
        )

    #Task: Deals 6 random cards to each player
    #Precondition: Round must start
    #Postcondition: Each player will have 6 random cards in their hand
    def deal(self):
        #Loop to deal cards
        for i in range(24):
            #Choosing suit to pick from
            randomSuit = random.choice(self.suits)

            #Selects card based on suit
            if randomSuit == "Spades":
                randomCard = random.choice(self.spades)
                self.spades.remove(randomCard)
            elif randomSuit == "Clubs":
                randomCard = random.choice(self.clubs)
                self.clubs.remove(randomCard)
            elif randomSuit == "Hearts":
                randomCard = random.choice(self.hearts)
                self.hearts.remove(randomCard)
            else:
                randomCard = random.choice(self.diamonds)
                self.diamonds.remove(randomCard)

            #Placing card with correct player
            if i in list(range(0, 3)) + list(range(12, 15)):
                self.player1.add_card(randomSuit, randomCard)

            if i in list(range(3, 6)) + list(range(15, 18)):
                self.player2.add_card(randomSuit, randomCard)

            if i in list(range(6, 9)) + list(range(18, 21)):
                self.player3.add_card(randomSuit, randomCard)

            if i in list(range(9, 12)) + list(range(21, 24)):
                self.player4.add_card(randomSuit, randomCard)


#Player Object
class Player:
    #Constructor
    def __init__(self, name):
        self.name = name       #Player Name (Player1, Player2, Player3, Dealer)
        self.hand = []         #Player's cards
        self.bid = None        #Player's bid (default None)
        self.is_dealer = False #Is player the dealer?

    #Task: Adds card to a player's hand
    #Precondition: Round must start
    #Postcondition: Each player will have a random card in their hand
    def add_card(self, suit, card):
        self.hand.append((suit, card))

    #Task: Visually shows the cards in a player's hand
    #Precondition: Cards must have been randomly distributed to each player
    #Postcondition: The cards in the player's hand will be visable
    def show_hand(self):
        return self.hand

    #Task: Allows player to play a card of their choice
    #Precondition: Cards have been dealt & it's the player's turn
    #Postcondition: Card that has been selected will be played and removed from player's hand
    def play_card(self, index):
        return self.hand.pop(index)

    def calculate_points(self):
        return 0


#Bot object (extends off Player class)
class Bot(Player):
    #Constructor
    def __init__(self, name):
        super().__init__(name)

    def choose_card(self, round_state):
        points = {
            "1": 1, "2": 2, "3": 3, "4": 4,
            "5": 5, "6": 6, "7": 7, "8": 8,
            "9": 9, "10": 10, "Jack": 11,
            "Queen": 12, "King": 13, "Ace": 14,
        }

        #If there's nothing in the bot's hand
        if not self.hand:
            return None

        #If there's no lead suit yet, play first card
        lead_suit = round_state.lead_suit
        if lead_suit is None:
            return self.hand.pop(0)

        #Find all cards matching lead suit
        valid_cards = [card for card in self.hand if card[0] == lead_suit]

        #If bots have a matching suit, they play it
        if valid_cards:
            # Find the most valuable card already in the current trick.
            current_trick_cards = [entry["card"] for entry in round_state.current_trick]
            if current_trick_cards:
                best_on_table = max(current_trick_cards, key=lambda c: points[c[1]])
                power_on_table = points[best_on_table[1]]
            else:
                power_on_table = 0

            #Filter the cards that can win
            winning_cards = [card for card in valid_cards if points[card[1]] > power_on_table]

            if winning_cards:
                # Throw the least valuable winning card.
                chosen_card = min(winning_cards, key=lambda card: points[card[1]])
            else:
                # Cannot win, throw the worst card of the lead suit.
                chosen_card = min(valid_cards, key=lambda card: points[card[1]])
        else:
            chosen_card = self.hand[0]

        #Remove chosen card from hand
        self.hand.remove(chosen_card)
        return chosen_card


#Game object
class Game:
    def __init__(self, players, winning_score):
        self.players = players
        self.winning_score = winning_score
        self.scores = {player.name: 0 for player in players}
        self.round_number = 1
        self.current_round = None

    #Creates a new Round object
    def start_round(self):
        self.current_round = Round(self.round_number, self.players)

    #Player scores is updated at the end of each round
    def end_round(self):
        if self.current_round is None:
            return

        results = self.current_round.get_results()

        for player, points in results.items():
            self.scores[player] += points

        self.round_number += 1

    #The game will check if there is a winner each round
    def check_winner(self):
        for player, score in self.scores.items():
            if score >= self.winning_score:
                return player
        return None


#Round object
class Round:
    #Constructor
    def __init__(self, round_number, players):
        self.roundNumber = round_number  #Number of the round
        self.players = players
        self.trumpSuit = None            #Trump suit for round
        self.current_trick = []          #Cards played in a sub-round
        self.lead_suit = None            #Leading card in a sub-round
        self.trick_complete = False
        self.bids = {}
        self.dealer = None
        self.winning_bidder = None
        self.winning_bid = None
        self.lead_player = None
        self.turn_order = []
        self.opening_trick_pending = False
        self.pending_auto_plays = []
        self.round_lead_order_active = False

    #Passes round information to the Game object
    def get_results(self):
        results = {}

        for player in self.players:
            results[player.name] = player.calculate_points()

        return results


#Handles dealer selection
#First dealer is chosen randomly
#Dealer moves left each new round
class DealerManager:
    def __init__(self, players):
        self.players = players
        self.dealer_index = None

    #Choose the first dealer randomly
    def new_dealer(self):
        self.dealer_index = random.randint(0, len(self.players) - 1)
        return self.dealer_index

    #Move dealer to the player on the left
    def left_dealer(self):
        if self.dealer_index is None:
            raise ValueError("Dealer has not been chosen yet.")
        self.dealer_index = (self.dealer_index + 1) % len(self.players)
        return self.dealer_index

    def get_dealer_index(self):
        return self.dealer_index


#Handles bidding and trump suit selection
#Every player must either bid higher than the current high bid or pass (0)
class BidManager:
    VALID_SUITS = ["clubs", "diamonds", "hearts", "spades"]

    def __init__(self, players):
        self.players = players
        self.reset_round_bidding()

    #Reset all bidding data for a new round
    def reset_round_bidding(self):
        self.bids = {player: 0 for player in self.players}
        self.high_bid = 0
        self.high_bidder_index = None
        self.high_bidder_name = None
        self.trump_suit = None

    #Validate any bid
    def validate_bid(self, bid, current_high_bid):
        if not isinstance(bid, int):
            raise ValueError("Bid must be an integer.")

        if bid < 0 or bid > 18:
            raise ValueError("Bid must be between 0 and 18.")

        if bid != 0 and bid <= current_high_bid:
            raise ValueError(
                f"Bid must be higher than the current high bid ({current_high_bid}) or 0 to pass."
            )

        return bid

    #Give the bot a random valid bid
    def get_bot_bid(self, current_high_bid):
        valid_choices = [0] + list(range(current_high_bid + 1, 19))
        return random.choice(valid_choices)

    #Run the full bidding phase
    #Turn order starts with the player to the left of the dealer
    def collect_bids(self, dealer_index, player_bid):
        self.reset_round_bidding()

        start_index = (dealer_index + 1) % len(self.players)

        print(f"Dealer: {self.players[dealer_index]}")

        for turn in range(len(self.players)):
            player_index = (start_index + turn) % len(self.players)
            player_name = self.players[player_index]

            if player_index == 0:
                # Use the player's submitted bid
                bid = player_bid
            else:
                # Bots generate a bid
                bid = self.get_bot_bid(self.high_bid)

            bid = self.validate_bid(bid, self.high_bid)
            print(f"{player_name} bids: {bid}")

            self.bids[player_name] = bid

            if bid > self.high_bid:
                self.high_bid = bid
                self.high_bidder_index = player_index
                self.high_bidder_name = player_name

        # If everyone passes with 0, dealer is forced to 2
        if all(bid == 0 for bid in self.bids.values()):
            dealer_name = self.players[dealer_index]
            self.bids[dealer_name] = 2
            self.high_bid = 2
            self.high_bidder_index = dealer_index
            self.high_bidder_name = dealer_name
            print(f"All players passed. Dealer rule applied: {dealer_name}'s bid becomes 2.")

        return self.bids, self.high_bidder_name, self.high_bid

    #Passes on the trump suit of the winner of the bid
    def choose_trump_suit(self, player_trump_suit=None):
        if self.high_bidder_index is None:
            raise ValueError("No winning bidder found. Run collect_bids() first.")

        # Player 1 wins -> use provided suit
        if self.high_bidder_index == 0:
            if player_trump_suit is None:
                # Don't assign anything yet; UI will prompt player
                return None
            self.trump_suit = player_trump_suit
            print(f"Player 1 chooses trump: {self.trump_suit}")
        else:
            # Bot wins -> random suit
            self.trump_suit = random.choice(self.VALID_SUITS)
            print(f"{self.high_bidder_name} chooses trump: {self.trump_suit}")

        return self.trump_suit


#Controls round flow by coordinating DealerManager and BidManager
class GameController:
    def __init__(self):
        self.players = ["Player 1", "Player 2", "Player 3", "Player 4"]
        self.dealer_manager = DealerManager(self.players)
        self.bid_manager = BidManager(self.players)
        self.round_number = 0

    #Start the game and choose the first dealer
    def start_game(self):
        self.round_number = 1
        first_dealer_index = self.dealer_manager.new_dealer()
        print(f"First dealer: {self.players[first_dealer_index]}")

    #Start one round of bidding and trump selection
    def start_round(self, player_bid, player_trump_suit=None):
        dealer_index = self.dealer_manager.get_dealer_index()

        if dealer_index is None:
            raise ValueError("Dealer has not been selected. Call start_game() first.")

        print(f"Dealer: {self.players[dealer_index]}")

        bids, winning_player, winning_bid = self.bid_manager.collect_bids(dealer_index, player_bid)

        print("\nFinal Bids:")
        for player, bid in bids.items():
            print(f"{player}: {bid}")

        print(f"\nWinning bidder: {winning_player} with {winning_bid}")

        trump_suit = self.bid_manager.choose_trump_suit(player_trump_suit)
        print(f"Trump suit for this round: {trump_suit}")

        return {
            "round_number": self.round_number,
            "dealer": self.players[dealer_index],
            "bids": bids,
            "winning_bidder": winning_player,
            "winning_bid": winning_bid,
            "trump_suit": trump_suit,
        }

    #End the current round and rotate dealer left
    def end_round(self):
        next_dealer_index = self.dealer_manager.left_dealer()
        self.round_number += 1
        print(f"\nNext dealer will be: {self.players[next_dealer_index]}")


#Task: Connects the card to their appropiate image
#Precondition: Cards are created
#Postcondition: Visible cards will have an associated image attached
def card_to_image(card):
    suit, rank = card
    return f"{suit}_{rank}.png"


def card_to_path(card):
    return f"/static/cards/{card_to_image(card)}"


def trick_entry_to_payload(entry):
    return {
        "player": entry["player"],
        "card_image": card_to_path(entry["card"]),
    }


def build_table_cards():
    return [trick_entry_to_payload(entry) for entry in deck.round.current_trick]


def default_turn_order():
    return ["Player 1", "Player 2", "Player 3", "Player 4"]


def build_turn_order(lead_player):
    order = default_turn_order()
    lead_index = order.index(lead_player)
    return order[lead_index:] + order[:lead_index]


def get_player_by_name(player_name):
    if deck is None:
        return None

    for player in deck.players:
        if player.name == player_name:
            return player

    return None


def setup_first_trick_lead(lead_player):
    # The winning bidder becomes the leader for the whole round, not only for
    # the opening trick. Every new trick starts again from this same player.
    deck.round.lead_player = lead_player
    deck.round.turn_order = build_turn_order(lead_player)
    deck.round.round_lead_order_active = True
    deck.round.pending_auto_plays = []
    deck.round.opening_trick_pending = lead_player != "Player 1"


def get_active_turn_order():
    # Keep the bid winner at the head of the order for the full round so every
    # new trick restarts from that same player until a future round reset happens.
    if deck.round.round_lead_order_active and deck.round.turn_order:
        return deck.round.turn_order

    return default_turn_order()


def get_next_player_name():
    active_order = get_active_turn_order()
    trick_position = len(deck.round.current_trick)

    if trick_position >= len(active_order):
        return None

    return active_order[trick_position]


def can_player_play_now():
    # The user can only interact when the round is ready and Player 1 is the next
    # expected actor in the current trick order.
    return (
        deck is not None
        and deck.player1.bid is not None
        and deck.round.trumpSuit is not None
        and not deck.round.trick_complete
        and get_next_player_name() == "Player 1"
    )


def should_queue_bot_opening():
    return (
        deck is not None
        and deck.round.trumpSuit is not None
        and not deck.round.trick_complete
        and get_next_player_name() is not None
        and get_next_player_name() != "Player 1"
    )


def record_trick_play(player_name, card):
    # The first card of the trick establishes the lead suit for follow-suit logic.
    if not deck.round.current_trick:
        deck.round.lead_suit = card[0]

    deck.played_cards.append(card)
    trick_entry = {"player": player_name, "card": card}
    deck.round.current_trick.append(trick_entry)
    return trick_entry


def update_trick_completion():
    deck.round.trick_complete = len(deck.round.current_trick) == 4

    if deck.round.trick_complete:
        deck.round.lead_suit = None


def play_bot_turns_until_user_or_end(store_as_pending=False):
    # This helper is reused in two moments:
    # 1. immediately after bidding when a bot should open the first trick;
    # 2. after the user plays, to let the remaining bots finish their turn sequence.
    bot_plays = []

    while True:
        next_player_name = get_next_player_name()

        if next_player_name is None or next_player_name == "Player 1":
            break

        bot_player = get_player_by_name(next_player_name)
        if bot_player is None:
            break

        bot_card = bot_player.choose_card(deck.round)
        if bot_card is None:
            break

        bot_entry = record_trick_play(bot_player.name, bot_card)
        bot_payload = {
            **trick_entry_to_payload(bot_entry),
            "remaining_hand_count": len(bot_player.hand),
        }
        bot_plays.append(bot_payload)
        print(f"{bot_player.name} played {bot_card}")

    update_trick_completion()

    if store_as_pending:
        # The frontend uses this list to animate opening bot plays after the page renders.
        deck.round.pending_auto_plays = list(bot_plays)
        deck.round.opening_trick_pending = bool(bot_plays)

    return bot_plays


def build_bot_hand_counts():
    return {
        "player2": len(deck.player2.hand),
        "player3": len(deck.player3.hand),
        "player4": len(deck.player4.hand),
    }


def can_player_play():
    return can_player_play_now()


def clear_completed_trick():
    deck.round.current_trick = []
    deck.round.lead_suit = None
    deck.round.trick_complete = False
    deck.round.opening_trick_pending = False
    deck.round.pending_auto_plays = []

    # Do not reset the round leader order here: clearing a trick only resets the
    # table state, while the bid winner must keep opening every trick in the round.


def queue_next_trick_if_bot_leads():
    # After a trick is cleared, the same round leader may need to open the next
    # trick automatically again. This keeps the bid winner at the front of every
    # trick until the round is reset.
    if not should_queue_bot_opening():
        return []

    return play_bot_turns_until_user_or_end(store_as_pending=True)


def is_json_request():
    accept_header = request.headers.get("Accept", "")
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in accept_header
    )


def build_game_context():
    user_hand = deck.player1.show_hand()
    user_bid = deck.player1.bid

    # Convert each card to its image path
    hand_images = [card_to_path(card) for card in user_hand]
    card_back_image = "/static/cards/card_back.png"
    bot_hand_counts = build_bot_hand_counts()
    table_cards = build_table_cards()
    can_play_now = can_player_play_now()

    return {
        "winning_score": getattr(game, "winning_score", None),
        "hand_images": hand_images,
        "card_back_image": card_back_image,
        "bot_hand_counts": bot_hand_counts,
        "table_cards": table_cards,
        "user_bid": user_bid,
        "show_bid_modal": user_bid is None,
        "can_play_now": can_play_now,
        "opening_trick_pending": deck.round.opening_trick_pending,
        "bids": getattr(deck.round, "bids", {}),
        "dealer": getattr(deck.round, "dealer", None),
        "winning_bidder": getattr(deck.round, "winning_bidder", None),
        "winning_bid": getattr(deck.round, "winning_bid", None),
        "lead_player": deck.round.lead_player,
        "turn_order": deck.round.turn_order,
        "trump_suit": deck.round.trumpSuit,
        "initial_state": {
            "hand_images": hand_images,
            "card_back_image": card_back_image,
            "bot_hand_counts": bot_hand_counts,
            "table_cards": table_cards,
            "can_play_now": can_play_now,
            "trick_complete": deck.round.trick_complete,
            "lead_player": deck.round.lead_player,
            "turn_order": deck.round.turn_order,
            "opening_trick_pending": deck.round.opening_trick_pending,
            "pending_auto_plays": deck.round.pending_auto_plays,
        },
    }


@app.route("/assets/<path:filename>")
def sprint_asset(filename):
    return send_from_directory(CURRENT_DIR, filename)


@app.route("/")
def index():
    return redirect("/game")


#First Page: Where the user starts a new game
@app.route("/new_game")
def new_game():
    return redirect("/game")


#Second Page: Where the user selects a winning value
@app.route("/winning_value")
def winning_value():
    return redirect("/game")


#Task: API call to define starting a new game
#Precondition: All associated objects have been created
#Postcondition: The user can restart the game
@app.route("/start_game", methods=["GET", "POST"])
def start_game():
    global deck, game_controller, game

    winning_score = getattr(game, "winning_score", None)

    if request.method == "POST":
        score = request.form.get("score", "").strip()

        try:
            winning_score = int(score)
        except ValueError:
            return redirect("/winning_value")

    #Reset the game state
    deck = Deck()
    deck.deal()

    players = [deck.player1, deck.player2, deck.player3, deck.player4]

    if winning_score is not None:
        game = Game(players, winning_score)
    else:
        game = None

    game_controller = GameController()
    game_controller.start_game()

    return redirect("/game")


#Task: API call to define the gameboard screen and functions
#Precondition: All associated objects have been initialized
#Postcondition: The gameboard screen is displayed
@app.route("/game")
def home():
    global deck, game_controller

    if deck is None:
        deck = Deck()
        deck.deal()

    if game_controller is None:
        game_controller = GameController()
        game_controller.start_game()

    return render_template("game.html", round=deck.round, **build_game_context())


#Store the bid selected in the opening modal.
@app.route("/set_bid", methods=["POST"])
def set_bid():
    global deck, game_controller

    if deck is None:
        return redirect("/game")

    if game_controller is None:
        game_controller = GameController()
        game_controller.start_game()

    #Bid is submitted by the popup form as plain text. Parse and validate it defensively.
    raw_bid = request.form.get("bid", "").strip()

    try:
        #Try to parse it into integer.
        selected_bid = int(raw_bid)
    except ValueError:
        #Ignore invalid payloads and return to the game view.
        return redirect("/game")

    if selected_bid < 0 or selected_bid > 18:
        #Keep the existing value unchanged when the range is invalid.
        return redirect("/game")

    # Save the bid so the popup does not appear again during this game state.
    deck.player1.bid = selected_bid

    # Run bidding phase
    dealer_index = game_controller.dealer_manager.get_dealer_index()
    bids, winning_player, winning_bid = game_controller.bid_manager.collect_bids(
        dealer_index,
        player_bid=deck.player1.bid,
    )

    # Store bidding results
    deck.round.bids = bids
    deck.round.winning_bidder = winning_player
    deck.round.winning_bid = winning_bid
    setup_first_trick_lead(winning_player)

    # If player won bid, just go back to game and let UI prompt for trump
    if winning_player == "Player 1":
        # Trump not assigned yet -> let user pick
        deck.round.trumpSuit = None
        deck.round.opening_trick_pending = False
        return redirect("/game")

    # Bot wins -> pick random trump immediately
    trump_suit = game_controller.bid_manager.choose_trump_suit()
    deck.round.trumpSuit = trump_suit
    play_bot_turns_until_user_or_end(store_as_pending=True)
    return redirect("/game")


@app.route("/set_trump", methods=["POST"])
def set_trump():
    global deck, game_controller
    if deck is None or game_controller is None:
        return redirect("/game")

    selected_suit = request.form.get("trump_suit", "").strip().lower()
    if selected_suit not in ["clubs", "diamonds", "hearts", "spades"]:
        return redirect("/game")

    # Player finalizes trump
    deck.round.trumpSuit = game_controller.bid_manager.choose_trump_suit(
        player_trump_suit=selected_suit
    )
    return redirect("/game")


@app.route("/clear_trick", methods=["POST"])
def clear_trick():
    global deck

    if deck is None:
        if is_json_request():
            return jsonify({"ok": False, "error": "Game not started."}), 400
        return redirect("/game")

    if deck.round.trick_complete:
        clear_completed_trick()
        queue_next_trick_if_bot_leads()

    payload = {
        "ok": True,
        "table_cards": build_table_cards(),
        "trick_complete": deck.round.trick_complete,
        "can_play_now": can_player_play_now(),
        "opening_trick_pending": deck.round.opening_trick_pending,
        "pending_auto_plays": deck.round.pending_auto_plays,
        "bot_hand_counts": build_bot_hand_counts(),
    }

    if is_json_request():
        return jsonify(payload)

    return redirect("/game")


#Task: API call to define the card selection function
#Precondition: The cards have been dealt & it's the player's turn
#Postcondition: The selected card will be removed from the player's hand and moved to the discard pile
@app.route("/play_card", methods=["GET", "POST"])
def play_card():
    global deck
    if deck is None:
        if is_json_request():
            return jsonify({"ok": False, "error": "Game not started."}), 400
        return "Game not started."

    if not can_player_play_now():
        if is_json_request():
            return jsonify({"ok": False, "error": "It is not the player's turn yet."}), 409
        return redirect("/game")

    if deck.round.trick_complete:
        clear_completed_trick()

    try:
        index = int(request.form["index"])
    except (KeyError, TypeError, ValueError):
        if is_json_request():
            return jsonify({"ok": False, "error": "Invalid card selection."}), 400
        return redirect("/game")

    if index < 0 or index >= len(deck.player1.hand):
        if is_json_request():
            return jsonify({"ok": False, "error": "Selected card is out of range."}), 400
        return redirect("/game")

    #User plays a card
    card = deck.player1.play_card(index)
    print(f"User played {card}")

    # Once the user acts, the opening bot animation has been fully consumed.
    deck.round.opening_trick_pending = False
    deck.round.pending_auto_plays = []
    user_entry = record_trick_play(deck.player1.name, card)

    # Continue following the active turn order until the user is reached again or the trick ends.
    bot_plays = play_bot_turns_until_user_or_end()

    payload = {
        "ok": True,
        "player_card": trick_entry_to_payload(user_entry),
        "player_card_image": card_to_path(card),
        "bot_plays": bot_plays,
        "hand_images": [card_to_path(hand_card) for hand_card in deck.player1.show_hand()],
        "bot_hand_counts": build_bot_hand_counts(),
        "table_cards": build_table_cards(),
        "trick_complete": deck.round.trick_complete,
        "can_play_now": can_player_play_now(),
    }

    if is_json_request():
        return jsonify(payload)

    return redirect("/game")


if __name__ == "__main__":
    app.run(debug=True)
