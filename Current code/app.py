#Imported libraries
from pathlib import Path
from flask import Flask, request, render_template, redirect, jsonify, send_from_directory
import random

# Initialize Flask
app = Flask(
    __name__,
    template_folder="templates", # Looks for the 'templates' folder
    static_folder="static",      # Looks for the 'static' folder
    static_url_path="/static"
)

#Initializing global variables
game = None
deck = None
game_controller = None

#Deck Object (Creates deck of cards)
class Deck:
    #Constructor
    def __init__(self):
        #Defining suits and their corresponding ranks
        self.suits = ["Spades", "Clubs", "Hearts", "Diamonds"]
        self.spades = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
        self.clubs = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
        self.hearts = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
        self.diamonds = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]

        # Create a full deck list for easier management of remaining cards
        self.remaining_deck = []
        for suit in self.suits:
            ranks = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
            for rank in ranks:
                self.remaining_deck.append((suit, rank))

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

    #Task: Replenish player hand after discard
    #Precondition: Discard phase must end with user discarding at least one card
    #Postcondition: The user will have new cards depending on how many they discarded
    def replenish_player(self, player_obj, num_cards_needed):
        new_cards_added = []
        print(f"Deck remaining before replenish: {len(self.remaining_deck)}")
        
        for _ in range(num_cards_needed):
            if self.remaining_deck:
                card = self.remaining_deck.pop()
                player_obj.add_card(card[0], card[1])
                new_cards_added.append(card)
            else:
                # Depending on Pitch rules, if the deck is empty, you can't get more.
                print("Deck is empty. Cannot replenish fully.")
                break
        return new_cards_added


#Player Object (Creates players)
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

    #Task: Calculates the player's points
    #Precondition: A round must end
    #Postcondition: The amount of points a play has will be updated
    def calculate_points(self):
        return 0


#Bot object (Extends off the Player class to create bots)
class Bot(Player):
    #Constructor
    def __init__(self, name):
        super().__init__(name)

    #Task: Allows bots to play a card each trick
    #Precondition: Cards have been dealt & it's the bots' turn
    #Postcondition: A card will be selected, played, and removed from bot's hand
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


#Game object (Creates a game)
class Game:
    #Constructor
    def __init__(self, players, winning_score):
        self.players = players
        self.winning_score = winning_score
        self.scores = {player.name: 0 for player in players}
        self.round_number = 1
        self.current_round = None

    #Task: Creates a new Round object
    #Precondition: The game has started and winning value chosen
    #Postcondition: The game will start a new round
    def start_round(self):
        self.current_round = Round(self.round_number, self.players)

    #Task: Player scores are updated at the end of each round
    #Precondition: The current round has ended
    #Postcondition: The result of the round are calculated
    def end_round(self):
        if self.current_round is None:
            return

        results = self.current_round.get_results()

        for player, points in results.items():
            self.scores[player] += points

        self.round_number += 1

    #Task: Check if there is a winner each round
    #Precondition: The current round has ended
    #Postcondition: The winner is decided if there is a winner
    def check_winner(self):
        for player, score in self.scores.items():
            if score >= self.winning_score:
                return player
        return None


#Round object (Extends off the Game class to create a round in a game)
class Round:
    #Constructor
    def __init__(self, round_number, players):
        self.roundNumber = round_number  #Number of the round
        self.players = players           #Players in the round
        self.trumpSuit = None            #Trump suit for for the round
        self.current_trick = []          #Cards played in a trick
        self.lead_suit = None            #Leading card in a trick
        self.trick_complete = False      #If a trick is completed
        self.bids = {}                   #Player's bid for the round
        self.dealer = None               #Dealer for the round
        self.winning_bidder = None       #Winning bidder for the round
        self.winning_bid = None          #Winning bid for the round

    #Task: Passes round information to the Game object
    #Precondition: The current round has ended
    #Postcondition: The Game object knows each player's points
    def get_results(self):
        results = {}

        for player in self.players:
            results[player.name] = player.calculate_points()

        return results

#DealManager object (Handles dealer selection)
class DealerManager:
    #Constructor
    def __init__(self, players):
        self.players = players
        self.dealer_index = None

    #Task: Choose the first dealer randomly
    #Precondition: A game has started and player have been created
    #Postcondition: A dealer is selected randomly among the players
    def new_dealer(self):
        self.dealer_index = random.randint(0, len(self.players) - 1)
        return self.dealer_index

    #Task: Moves dealer position to the player on the left
    #Precondition: A new round has started after a previous round
    #Postcondition: A new dealer is selected
    def left_dealer(self):
        if self.dealer_index is None:
            raise ValueError("Dealer has not been chosen yet.")
        self.dealer_index = (self.dealer_index + 1) % len(self.players)
        return self.dealer_index

    #Task: Gets the current dealer's index
    #Precondition: A dealer has been selected
    #Postcondition: The current dealer's index is known
    def get_dealer_index(self):
        return self.dealer_index

#BidManager class (Handles bidding and trump suit selection)
class BidManager:
    VALID_SUITS = ["clubs", "diamonds", "hearts", "spades"]
    #Constructor
    def __init__(self, players):
        self.players = players
        self.reset_round_bidding()

    #Task: Reset all bidding data for a new round
    #Precondition: A new round has been started
    #Postcondition: The new round contains no information from the previous round
    def reset_round_bidding(self):
        self.bids = {player: 0 for player in self.players}
        self.high_bid = 0
        self.high_bidder_index = None
        self.high_bidder_name = None
        self.trump_suit = None

    #Task: Validate any bid
    #Precondition: The user's bid has been selected
    #Postcondition: The user's bid is confirmed as valid for that round
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

    #Task: Give the bots a random valid bid
    #Precondition: A new round has started
    #Postcondition: The bots' bids are confirmed as valid for that round
    def get_bot_bid(self, current_high_bid):
        valid_choices = [0] + list(range(current_high_bid + 1, 19))
        return random.choice(valid_choices)

    #Task: Run the full bidding phase
    #Precondition: All players have selected a bid
    #Postcondition: All players' bid are known by the round
    def collect_bids(self, dealer_index, player_bid):
        self.reset_round_bidding()

        start_index = (dealer_index + 1) % len(self.players)

        print(f"Dealer: {self.players[dealer_index]}")

        for turn in range(len(self.players)):
            player_index = (start_index + turn) % len(self.players)
            player_name = self.players[player_index]

            if player_index == 0:
                #Use the player's submitted bid
                bid = player_bid
            else:
                #Bots generate a bid
                bid = self.get_bot_bid(self.high_bid)

            bid = self.validate_bid(bid, self.high_bid)
            print(f"{player_name} bids: {bid}")

            self.bids[player_name] = bid

            if bid > self.high_bid:
                self.high_bid = bid
                self.high_bidder_index = player_index
                self.high_bidder_name = player_name

        #If everyone passes with 0, dealer is forced to 2
        if all(bid == 0 for bid in self.bids.values()):
            dealer_name = self.players[dealer_index]
            self.bids[dealer_name] = 2
            self.high_bid = 2
            self.high_bidder_index = dealer_index
            self.high_bidder_name = dealer_name
            print(f"All players passed. Dealer rule applied: {dealer_name}'s bid becomes 2.")

        return self.bids, self.high_bidder_name, self.high_bid

    #Task: Pass on the trump suit of the winner of the bid
    #Precondition: All players' bid has been selected
    #Postcondition: The trump suit is chosen for the round
    def choose_trump_suit(self, player_trump_suit=None):
        if self.high_bidder_index is None:
            raise ValueError("No winning bidder found. Run collect_bids() first.")

        #If Player 1 wins, use provided suit
        if self.high_bidder_index == 0:
            if player_trump_suit is None:
                #Don't assign anything; UI will prompt player
                return None
            self.trump_suit = player_trump_suit
            print(f"Player 1 chooses trump: {self.trump_suit}")
        else:
            #If a bot wins, random suit is selected
            self.trump_suit = random.choice(self.VALID_SUITS)
            print(f"{self.high_bidder_name} chooses trump: {self.trump_suit}")

        return self.trump_suit

#GameController object (Controls round flow by coordinating DealerManager and BidManager)
class GameController:
    #Constructor
    def __init__(self):
        self.players = ["Player 1", "Player 2", "Player 3", "Player 4"]
        self.dealer_manager = DealerManager(self.players)
        self.bid_manager = BidManager(self.players)
        self.round_number = 0

    #Task: Start the game and choose the first dealer
    #Precondition: A new game has been created
    #Postcondition: The game starts and a dealer is selected
    def start_game(self):
        self.round_number = 1
        first_dealer_index = self.dealer_manager.new_dealer()
        print(f"First dealer: {self.players[first_dealer_index]}")

    #Task: Start one round of bidding and trump selection
    #Precondition: A new round has been started
    #Postcondition: The round will know the dealer, player bids, and trump suit
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

    #Task: End the current round and rotate dealer left
    #Precondition: The round has ended
    #Postcondition: The round ends and a new dealer is chosen for the next round
    def end_round(self):
        next_dealer_index = self.dealer_manager.left_dealer()
        self.round_number += 1
        print(f"\nNext dealer will be: {self.players[next_dealer_index]}")

#Task: Connects the card to their appropiate image
#Precondition: Cards are created
#Postcondition: Cards will have an associated image attached
def card_to_image(card):
    suit, rank = card
    return f"{suit}_{rank}.png"

#Task: Creates the pathway for cards to their associated image
#Precondition: Cards have an attached image
#Postcondition: Cards and their associated image can be made visible
def card_to_path(card):
    return f"/static/cards/{card_to_image(card)}"

#Task: Converts a Game object into something the frontend can use
#Precondition: The players and cards have been created
#Postcondition: The frontend can use the game's information
def trick_entry_to_payload(entry):
    return {
        "player": entry["player"],
        "card_image": card_to_path(entry["card"]),
    }

#Task: Creates a list of all visible cards for the frontend
#Precondition: The cards have all been dealt
#Postcondition: The frontend can use the card's images
def build_table_cards():
    return [trick_entry_to_payload(entry) for entry in deck.round.current_trick]

#Task: Counts the number of cards in the bots' hands
#Precondition: The bots' have been dealt cards
#Postcondition: The system knows the number of cards in the bots' hands
def build_bot_hand_counts():
    return {
        "player2": len(deck.player2.hand),
        "player3": len(deck.player3.hand),
        "player4": len(deck.player4.hand),
    }

#Task: Checks if it's the player's turn
#Precondition: A round is in session
#Postcondition: Blocks or makes cards available depending on if it's the player's turn
def can_player_play():
    return (
        deck is not None
        and deck.player1.bid is not None
        and deck.round.trumpSuit is not None
    )

#Task: Clears the trick's information when a trick is completed
#Precondition: The trick has ended
#Postcondition: The trick's information is wiped clean
def clear_completed_trick():
    deck.round.current_trick = []
    deck.round.lead_suit = None
    deck.round.trick_complete = False

#Task: Checks if current round should end
#Precondition: Each player has no more cards
#Postcondition: The round ends
def is_round_over():
    return (
        len(deck.player1.hand) == 0 and
        len(deck.player2.hand) == 0 and
        len(deck.player3.hand) == 0 and
        len(deck.player4.hand) == 0
    )

#Task: It detects if a request coming from JavaScript or a normal page
#Precondition: A request is send through the system
#Postcondition: Gives either a JSON or HTML response
def is_json_request():
    accept_header = request.headers.get("Accept", "")
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in accept_header
    )

#Task: Concentrates the game's necessary information
#Precondition: The game's necessary information has all been declared
#Postcondition: The system will have all of the game's necessary information
def build_game_context():
    user_hand = deck.player1.show_hand()
    user_bid = deck.player1.bid

    #Convert each card to its image path
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
        "trump_suit": deck.round.trumpSuit,
        "initial_state": {
            "hand_images": hand_images,
            "card_back_image": card_back_image,
            "bot_hand_counts": bot_hand_counts,
            "table_cards": table_cards,
            "can_play": can_play,
            "trick_complete": deck.round.trick_complete,
            "needs_discard": (deck.round.trumpSuit is not None and not getattr(deck.player1, 'discard_completed', False)),
            "trump_suit": deck.round.trumpSuit
        },
    }

#Task: API call to receive the game's assets from a specific directory
#Precondition: The game's assets are inside the specified directory which as been initialized
#Postcondition: The system knows the game's assets
@app.route("/assets/<path:filename>")
def sprint_asset(filename):
    return send_from_directory(CURRENT_DIR, filename)

#Task: API call to render the page to start a new game
#Precondition: The server must be running
#Postcondition: The user can create a new game
@app.route("/new_game")
def new_game():
    return render_template("new_game.html")

#Task: API call to render the page to select a winning value
#Precondition: A new game must be started
#Postcondition: That game's winning value is chosen
@app.route("/winning_value")
def winning_value():
    return render_template("winning_value.html")

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

#Task: API call so the user can select their bid
#Precondition: The winning value has been selected & a new game started
#Postcondition: The user's bid has been chosen
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

    #Save the bid so the popup does not appear again during this game state.
    deck.player1.bid = selected_bid

    #Run bidding phase
    dealer_index = game_controller.dealer_manager.get_dealer_index()
    try:
        game_controller.bid_manager.validate_bid(selected_bid, 0)
    except ValueError:
        return redirect("/game")

    bids, winning_player, winning_bid = game_controller.bid_manager.collect_bids(
        dealer_index,
        player_bid=deck.player1.bid,
    )

    #Store bidding results
    deck.round.bids = bids
    deck.round.winning_bidder = winning_player
    deck.round.winning_bid = winning_bid

    #If the player won bid, just go back to game and let UI prompt for trump
    if winning_player == "Player 1":
        # Trump not assigned yet -> let user pick
        deck.round.trumpSuit = None
        return redirect("/game")

    #If a bot wins, pick random trump immediately
    trump_suit = game_controller.bid_manager.choose_trump_suit()
    deck.round.trumpSuit = trump_suit
    return redirect("/game")

#Task: API call so the user can select the round's trump suit
#Precondition: All players' bids have been chosen
#Postcondition: The round's trump suit has been chosen
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

#Task: API call to clear the cards in the current trick
#Precondition: All players have played a card (trick has ended)
#Postcondition: The pile is clear and a new trick has started
@app.route("/clear_trick", methods=["POST"])
def clear_trick():
    global deck

    if deck is None:
        if is_json_request():
            return jsonify({"ok": False, "error": "Game not started."}), 400
        return redirect("/game")

    if deck.round.trick_complete:
        clear_completed_trick()

    payload = {
        "ok": True,
        "table_cards": build_table_cards(),
        "trick_complete": deck.round.trick_complete,
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

    if not can_player_play():
        if is_json_request():
            return jsonify({"ok": False, "error": "Finish the bid and trump selection first."}), 409
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
    deck.played_cards.append(card)
    print(f"User played {card}")

    #Update the round state
    if not deck.round.current_trick:
        deck.round.lead_suit = card[0]

    user_entry = {"player": deck.player1.name, "card": card}
    deck.round.current_trick.append(user_entry)

    #Bots play after the user
    bot_plays = []
    for bot_player in [deck.player2, deck.player3, deck.player4]:
        bot_card = bot_player.choose_card(deck.round)
        if bot_card:
            deck.played_cards.append(bot_card)
            bot_entry = {"player": bot_player.name, "card": bot_card}
            deck.round.current_trick.append(bot_entry)
            bot_plays.append({
                **trick_entry_to_payload(bot_entry),
                "remaining_hand_count": len(bot_player.hand),
            })
            print(f"{bot_player.name} played {bot_card}")

    deck.round.trick_complete = len(deck.round.current_trick) == 4
    if deck.round.trick_complete:
        deck.round.lead_suit = None

    payload = {
        "ok": True,
        "player_card": trick_entry_to_payload(user_entry),
        "player_card_image": card_to_path(card),
        "bot_plays": bot_plays,
        "hand_images": [card_to_path(hand_card) for hand_card in deck.player1.show_hand()],
        "bot_hand_counts": build_bot_hand_counts(),
        "table_cards": build_table_cards(),
        "trick_complete": deck.round.trick_complete,
        "round_over": is_round_over(),
    }

    if is_json_request():
        return jsonify(payload)
    return redirect("/game")

#Task: API call to provide the discard modal with the user's current hand and trump suit
#Precondition: The user's bid and round's trump suit has been chosen
#Postcondition: The discard model will appear for the user's hand that round
@app.route("/get_discard_status", methods=["GET"])
def get_discard_status():
    global deck
    if deck is None or deck.round.trumpSuit is None:
        return jsonify({"ok": False, "error": "Game or Trump not initialized."}), 400
    
    #Check if this player needs to enter the discard phase.
    if getattr(deck.player1, 'discard_completed', False):
        return jsonify({"ok": True, "show_discard": False})

    user_hand = deck.player1.show_hand()
    trump_suit = deck.round.trumpSuit.capitalize() # Normalize comparison case

    #Prepare hand data with an "can_discard" flag for the UI
    hand_data = []
    for index, card in enumerate(user_hand):
        card_suit, card_rank = card
        #Cannot discard trump suit cards
        is_trump = (card_suit.capitalize() == trump_suit)
        hand_data.append({
            "index": index,
            "image": card_to_path(card),
            "can_discard": not is_trump,
            "display_name": f"{card_rank} of {card_suit}"
        })

    return jsonify({
        "ok": True,
        "show_discard": True,
        "trump_suit": trump_suit,
        "hand": hand_data,
        "deck_remaining": len(deck.remaining_deck)
    })

#Task: API call to provide the system with the user's current hand and trump suit
#Precondition: The user's bid and round's trump suit has been chosen
#Postcondition: The system will receive the user's hand and the round's trump suit for the discard model
@app.route("/get_discard_data")
def get_discard_data():
    global deck, game_controller
    #Get current hand and trump suit
    user_hand = deck.player1.show_hand()
    trump_suit = game_controller.bid_manager.trump_suit

    hand_data = []
    for index, (suit, rank) in enumerate(user_hand):
        #Cannot discard trump suit
        is_trump = (suit.lower() == trump_suit.lower())
        hand_data.append({
            "index": index,
            "image": f"/static/cards/{suit.lower()}_{rank.lower()}.png",
            "can_discard": not is_trump
        })
    
    return jsonify ({
        "ok": True,
        "show_discard": True,
        "trump_suit": trump_suit,
        "hand": hand_data,
    })

#Task: API call to process the actual discards and deal new cards
#Precondition: The user has chosen which cards to discard
#Postcondition: The discarded cards will be replaced by new ones
@app.route("/process_discards", methods=["POST"])
def process_discards():
    global deck
    data = request.get_json()
    indices = sorted(data.get("indices", []), reverse=True)

    #Remove cards (backwards to maintain index integrity)
    for idx in indices:
        deck.player1.hand.pop(idx)

    #Replenish using your new method
    deck.replenish_player(deck.player1, len(indices))

    new_hand_images = [card_to_path(c) for c in deck.player1.hand]
    return jsonify({
        "ok": True, 
        "message": "Hand updated", 
        "new_hand_images": new_hand_images
    })

#Task: API call to start a new round in a game
#Precondition: A round must be completed in a game
#Postcondition: A new round will start in that game
@app.route("/next_round", methods=["POST"])
def next_round():
    global deck, game_controller

    #Reset deck and deal new cards
    deck = Deck()
    deck.deal()

    #Advance dealer
    game_controller.end_round()

    return redirect("/game")

#Run Flask
if __name__ == "__main__":
    app.run(debug=True)