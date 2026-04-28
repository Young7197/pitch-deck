#Libraries needed
from pathlib import Path
from flask import Flask, request, render_template, redirect, jsonify, send_from_directory
import random

# Initialize Flask
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR

app = Flask(
    __name__,
    template_folder=str(CURRENT_DIR / "templates"),
    static_folder=str(CURRENT_DIR / "static"),
    static_url_path="/static",
)

#Initializing global variables
game = None
deck = None
game_controller = None
last_score_state = None
round_finished = False


#Deck Object
class Deck:
    def __init__(self):
        self.suits = ["Spades", "Clubs", "Hearts", "Diamonds"]

        self.cards = [(s, r) for s in self.suits for r in
            ["1","2","3","4","5","6","7","8","9","10","Jack","Queen","King","Ace"]]

        random.shuffle(self.cards)

        self.player1 = Player("Player 1")
        self.player2 = Bot("Player 2")
        self.player3 = Bot("Player 3")
        self.player4 = Bot("Player 4")

        self.players = [self.player1, self.player2, self.player3, self.player4]

        self.player_map = {p.name: p for p in self.players}

        self.round = Round(1, self.players)

        self.deal()

    def deal(self):
        for i, card in enumerate(self.cards[:24]):
            self.players[i % 4].hand.append(card)

    #Task: Deals 6 random cards to each player
    #Precondition: Round must start
    #Postcondition: Each player will have 6 random cards in their hand


#Player Object
class Player:
    #Constructor
    def __init__(self, name):
        self.name = name       #Player Name (Player1, Player2, Player3, Dealer)
        self.hand = []         #Player's cards
        self.bid = None        #Player's bid (default None)
        self.is_dealer = False #Is player the dealer?
        self.cards_won = []
        self.points = 0

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
    def __init__(self, round_number, players):
        self.round_number = round_number
        self.players = players

        self.trump_suit = None
        self.lead_suit = None

        self.current_trick = []
        self.trick_complete = False

        self.bids = {}
        self.winning_bidder = None
        self.winning_bid = None

        self.current_player_index = 0
        self.bids_finalized = False

    def add_play(self, player_name, card):
        if not self.current_trick:
            self.lead_suit = card[0]

        self.current_trick.append({
            "player": player_name,
            "card": card
        })

    def is_trick_full(self):
        return len(self.current_trick) == 4

    def reset_trick(self):
        self.current_trick = []
        self.lead_suit = None
        self.trick_complete = False

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

            if player_name == "Player 1":
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

#Class calculates score
class calcScore:

    def __init__(self, deck, trump):
        self.deck = deck
        self.trump = trump

    def game(self, player):

        #sets game points for round at 0
        gamePoints = 0

        #goes through each card value to calculate the points
        for suit, card in player.cards_won:
            
            #cards the are worth points towards game
            if card == "10":
                gamePoints = gamePoints + 10
            elif card == "Jack":
                gamePoints = gamePoints + 1
            elif card == "Queen":
                gamePoints = gamePoints + 2
            elif card == "King":
                gamePoints = gamePoints + 3
            elif card == "Ace":
                gamePoints = gamePoints + 4

        return gamePoints
    
    #filters all trump cards into player array 
    def trumpCardsOnly(self, player, trump):
        trumpCards = []

        for suit, rank in player.cards_won:
            if suit == trump:
                trumpCards.append(rank)

        return trumpCards

    #finds what each players high and low card of trump is
    def HighLow(self, player, trump):

        #runs function to only get trump cards
        valuesTrump = self.trumpCardsOnly(player, trump)

        if not valuesTrump:
            return None, None

        #finds low and high
        high = max(valuesTrump, key=lambda c: self.deck.rankCards[c])
        low = min(valuesTrump, key=lambda c: self.deck.rankCards[c])

        return high, low

    def fiveNineJack(self, player, trump):

        #creating variables 
        five = False
        nine = False
        jack = False

        #runs function to only get trump cards
        valuesTrump = self.trumpCardsOnly(player, trump)

        if not valuesTrump:
            return False, False, False

        #finds if player have 5, 9, or Jack
        for value in valuesTrump:
            if value == "5":
                five = True
            elif value == "9":
                nine = True
            elif value == "Jack":
                jack = True
        
        return five, nine, jack

    def makeBid(self, bid, bidWinner, roundPoints):

        if roundPoints >= bid:
            return roundPoints
        else:
            roundPoints = roundPoints - bid
            return roundPoints

def Main(deck):
    global round_finished, last_score_state  

    round_finished = True
    last_score_state = None
    
    players = [deck.player1, deck.player2, deck.player3, deck.player4]

    trump = deck.round.trump_suit
    bidWinner = deck.round.winning_bidder
    bidAmount = deck.round.winning_bid

    calc = calcScore(deck, trump)

    # RESET ROUND CALCULATION
    for p in players:
        p.round_points = 0 

    # GAME POINTS 
    game_scores = {
        p: calc.game(p) for p in players
    }

    gameWinnerPlayer = max(game_scores, key=game_scores.get)
    gameWinnerPlayer.points += 1
    gameWinnerPlayer.round_points += 1


    # HIGH / LOW TRUMP
    highs_lows = {
        p: calc.HighLow(p, trump) for p in players
    }

    highs = []
    lows = []

    for player, (h, l) in highs_lows.items():
        if h:
            highs.append((player, h))
        if l:
            lows.append((player, l))

    highWinnerPlayer = None
    lowWinnerPlayer = None

    if highs:
        highWinnerPlayer, _ = max(highs, key=lambda x: deck.rankCards[x[1]])
        highWinnerPlayer.points += 1
        highWinnerPlayer.round_points += 1

    if lows:
        lowWinnerPlayer, _ = min(lows, key=lambda x: deck.rankCards[x[1]])
        lowWinnerPlayer.points += 1
        lowWinnerPlayer.round_points += 1

    # 5 / 9 / JACK SCORING
    for player in players:
        five, nine, jack = calc.fiveNineJack(player, trump)

        if five:
            player.points += 5
            player.round_points += 5

        if nine:
            player.points += 9
            player.round_points += 9

        if jack:
            player.points += 1
            player.round_points += 1


    # BID PENALTY
    if bidWinner:
        for p in players:
            if p.name == bidWinner:
                if p.points < bidAmount:
                    p.points -= bidAmount
                    p.round_points -= bidAmount

    # RETURN SUMMARY
    return (
        bidWinner,
        bidAmount,
        gameWinnerPlayer,
        highWinnerPlayer,
        lowWinnerPlayer,
        players[0].round_points,
        players[1].round_points,
        players[2].round_points,
        players[3].round_points,
        players[0].points,
        players[1].points,
        players[2].points,
        players[3].points,
    )

def get_player_wins(player_name, game_state):
    wins = []

    if game_state.get('game_winner_player') == player_name:
        wins.append("Game")

    if game_state.get('high_winner_player') == player_name:
        wins.append("High")

    if game_state.get('low_winner_player') == player_name:
        wins.append("Low")

    if game_state.get('five_winner') == player_name:
        wins.append("5")

    if game_state.get('nine_winner') == player_name:
        wins.append("9")

    if game_state.get('jack_winner') == player_name:
        wins.append("Jack")

    return wins

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


def build_bot_hand_counts():
    return {
        "player2": len(deck.player2.hand),
        "player3": len(deck.player3.hand),
        "player4": len(deck.player4.hand),
    }


def can_player_play():
    return (
        deck is not None
        and deck.round.bids_finalized
        and deck.round.trump_suit is not None
    )


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
    can_play = can_player_play()

    return {
        "winning_score": getattr(game, "winning_score", None),
        "hand_images": hand_images,
        "card_back_image": card_back_image,
        "bot_hand_counts": bot_hand_counts,
        "table_cards": table_cards,
        "user_bid": user_bid,
        "show_bid_modal": user_bid is None,
        "can_play": can_play,
        "bids": getattr(deck.round, "bids", {}),
        "dealer": getattr(deck.round, "dealer", None),
        "winning_bidder": getattr(deck.round, "winning_bidder", None),
        "winning_bid": getattr(deck.round, "winning_bid", None),
        "trump_suit": deck.round.trump_suit,
        "initial_state": {
            "hand_images": hand_images,
            "card_back_image": card_back_image,
            "bot_hand_counts": bot_hand_counts,
            "table_cards": table_cards,
            "can_play": can_play,
            "trick_complete": deck.round.trick_complete,
        },
    }

def determine_trick_winner(round_obj):
    rank = {
        "1":1,"2":2,"3":3,"4":4,"5":5,"6":6,
        "7":7,"8":8,"9":9,"10":10,
        "Jack":11,"Queen":12,"King":13,"Ace":14
    }

    trump = round_obj.trump_suit
    lead = round_obj.lead_suit

    # check trump first
    trump_cards = [c for c in round_obj.current_trick if c["card"][0] == trump]
    if trump_cards:
        return max(trump_cards, key=lambda c: rank[c["card"][1]])["player"]

    # fallback to lead suit
    lead_cards = [c for c in round_obj.current_trick if c["card"][0] == lead]
    return max(lead_cards, key=lambda c: rank[c["card"][1]])["player"]

def resolve_trick(deck):
    winner_name = determine_trick_winner(deck.round)

    winner = deck.player_map[winner_name]

    for entry in deck.round.current_trick:
        winner.cards_won.append(entry["card"])

    deck.round.trick_complete = True

    return winner_name

def is_round_over():
    return all(len(p.hand) == 0 for p in deck.players)

def clear_completed_trick():
    deck.round.current_trick = []
    deck.round.lead_suit = None
    deck.round.trick_complete = False

@app.route("/")
def index():
    return render_template("new_game.html")

@app.route("/winning_value")
def winning_value():
    return render_template("winning_value.html")

@app.route("/new_game")
def new_game():
    return render_template("new_game.html")

#Task: API call to define starting a new game
#Precondition: All associated objects have been created
#Postcondition: The user can restart the game
@app.route("/start_game", methods=["GET", "POST"])
def start_game():
    global deck, game_controller, game

    winning_score = None

    if request.method == "POST":
        score = request.form.get("score", "").strip()
        try:
            winning_score = int(score)
        except ValueError:
            return redirect("/winning_value")

    # FULL RESET
    deck = Deck()

    game_controller = GameController()
    game_controller.start_game()

    players = [deck.player1, deck.player2, deck.player3, deck.player4]
    game = Game(players, winning_score) if winning_score else None

    if last_score_state is not None:
        return redirect("/score_board")

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

    if getattr(deck.round, "bids_finalized", False):
        return redirect("/game")

    try:
        selected_bid = int(request.form.get("bid", 0))
    except ValueError:
        return redirect("/game")

    winner_index = game_controller.bid_manager.high_bidder_index
    deck.round.current_player_index = winner_index

    deck.player1.bid = selected_bid

    dealer_index = game_controller.dealer_manager.get_dealer_index()

    bids, winning_player, winning_bid = game_controller.bid_manager.collect_bids(
        dealer_index,
        player_bid=selected_bid,
    )

    deck.round.bids = bids
    deck.round.winning_bidder = winning_player
    deck.round.winning_bid = winning_bid
    deck.round.bids_finalized = True 

    if winning_player == "Player 1":
        deck.round.trump_suit = None
        return redirect("/game")

    deck.round.trump_suit = game_controller.bid_manager.choose_trump_suit()
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
    deck.round.trump_suit = game_controller.bid_manager.choose_trump_suit(
        player_trump_suit=selected_suit
    )
    return redirect("/game")


@app.route("/clear_trick", methods=["POST"])
def clear_trick():
    global deck

    if deck is None:
        return jsonify({"ok": False, "error": "Game not started."}), 400

    if deck.round.trick_complete:
        deck.round.reset_trick()

    return jsonify({
        "ok": True,
        "table_cards": build_table_cards(),
        "trick_complete": deck.round.trick_complete
    })


#Task: API call to define the card selection function
#Precondition: The cards have been dealt & it's the player's turn
#Postcondition: The selected card will be removed from the player's hand and moved to the discard pile
@app.route("/play_card", methods=["POST"])
def play_card():
    global deck, last_score_state

    if deck is None:
        return jsonify({"ok": False, "error": "Game not started."}), 400

    r = deck.round

    if not can_player_play():
        return jsonify({"ok": False, "error": "Not ready"}), 409

    #PLAYER MOVE
    index = int(request.form["index"])
    card = deck.player1.play_card(index)

    r.add_play("Player 1", card)

    if r.current_player_index == 0:
        r.current_player_index = 1

    #BOT MOVES
    bot_plays = []

    while r.current_player_index != 0 and not r.is_trick_full():
        bot = deck.players[r.current_player_index]
        bot_card = bot.choose_card(r)

        if bot_card:
            r.add_play(bot.name, bot_card)

            bot_plays.append({
                "player": bot.name,
                "card": bot_card,
                "card_image": card_to_path(bot_card),
                "remaining_hand_count": len(bot.hand)
            })

        r.current_player_index = (r.current_player_index + 1) % 4

    #TRICK RESOLUTION
    winner = None

    if r.is_trick_full():
        winner = determine_trick_winner(r)
        winner_player = deck.player_map[winner]

        for entry in r.current_trick:
            winner_player.cards_won.append(entry["card"])

        r.current_player_index = deck.players.index(winner_player)

        r.reset_trick()

    #ROUND END
    if all(len(p.hand) == 0 for p in deck.players):
        last_score_state = Main(deck)

        return jsonify({
            "ok": True,
            "redirect": "/score_board"
        })

    #NORMAL RESPONSE
    return jsonify({
        "ok": True,
        "player_card": {
            "player": "Player 1",
            "card": card,
            "card_image": card_to_path(card)
        },
        "hand_images": [card_to_path(c) for c in deck.player1.hand],
        "bot_plays": bot_plays,
        "bot_hand_counts": build_bot_hand_counts(),
        "table_cards": build_table_cards(),
        "trick_complete": r.trick_complete
    })

@app.route("/next_round", methods=["POST"])
def next_round():
    global deck, game_controller, round_finished

    # reset round state
    deck.round = Round(deck.round.round_number + 1, deck.players)
    deck.deal()

    round_finished = False

    # rotate dealer like original game
    game_controller.end_round()

    return redirect("/game")

@app.route('/score_board')
def score_board():
    global last_score_state

    # Safety check
    if last_score_state is None:
        return redirect("/game")

    (
        bidWinner, bidAmount,
        gameWinnerPlayer, highWinnerPlayer, lowWinnerPlayer,
        fiveWinner, nineWinner, jackWinner,
        p1_round, p2_round, p3_round, p4_round,
        p1_total, p2_total, p3_total, p4_total,
    ) = last_score_state

    # Now build your template data
    game_state = {
        "bid_winner": bidWinner,
        "bid_amount": bidAmount,
        "game_winner_player": gameWinnerPlayer.name if gameWinnerPlayer else None,
        "high_winner_player": highWinnerPlayer.name if highWinnerPlayer else None,
        "low_winner_player": lowWinnerPlayer.name if lowWinnerPlayer else None,
        "five_winner": fiveWinner.name if fiveWinner else None,
        "nine_winner": nineWinner.name if nineWinner else None,
        "jack_winner": jackWinner.name if jackWinner else None,

        # round points
        "player1_round": p1_round,
        "player2_round": p2_round,
        "player3_round": p3_round,
        "player4_round": p4_round,

        # total points
        "player1_total": p1_total,
        "player2_total": p2_total,
        "player3_total": p3_total,
        "player4_total": p4_total,
    }

    return render_template("scoreBoard.html", game_state=game_state)

if __name__ == "__main__":
    app.run(debug=True)
