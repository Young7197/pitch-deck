#Libraries needed
from flask import Flask, request, render_template, redirect
import random

# Initialize Flask
app = Flask(__name__)

#Initializing global variables
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

        #Defining the list to keep track of played cards
        self.played_cards = []

        #Defining the game state
        self.round = Round()
        
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
        self.bid =  None       #Player's bid (default None)
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
    def play_card(self, index, deck):
        card = self.hand.pop(index)
        deck.played_cards.append(card)
        return card

#Bot object (extends off Player class)
class Bot(Player):
    #Constructor
    def __init__(self, name):
        super().__init__(name)

    def choose_card(self, round):
        points = {
            "1" : 1, "2" : 2, "3" : 3, "4" : 4,
            "5" : 5, "6" : 6, "7" : 7, "8" : 8,
            "9" : 9, "10" : 10, "Jack" : 11,
            "Queen" : 12, "King" : 13, "Ace" : 14
        }

        #If there's nothing in the bot's hand
        if not self.hand:
            return None

        #If there's no lead suit yet, play first card
        lead_suit = round.lead_suit
        if lead_suit is None:
            return self.hand.pop(0)

        #Find all cards matching lead suit
        valid_cards = [card for card in self.hand if card[0] == lead_suit]

        #If bots have a matching suit, they play it
        if valid_cards:
            # 2. Find the most valuable card in the table
            if deck.played_cards:
                best_on_table = max(deck.played_cards, key=lambda c: points[c[1]])
                power_on_table = points[best_on_table[1]]
            else:
                power_on_table = 0

            # 3. Filter the cards that can win
            winning_cards = [c for c in valid_cards if points[c[1]] > power_on_table]

            if winning_cards:
                # Trowing the least valuable card
                chosen_card = min(winning_cards, key=lambda c: points[c[1]])
            else:
                # cannot win, throwing the worse card
                chosen_card = min(valid_cards, key=lambda c: points[c[1]])
        else:
            chosen_card = self.hand[0]

        #Remove chosen card from hand
        self.hand.remove(chosen_card)
        return chosen_card

#Round object
class Round:
    #Constructor
    def __init__(self):
        self.roundNumber = 0      #Number of the round
        self.trumpSuit = None     #Trump suit for round
        self.current_trick = []   #Cards played in a sub-round
        self.lead_suit = None     #Leading card in a sub-round
        self.bids = {}
        self.dealer = None
        self.winning_bidder = None
        self.winning_bid = None

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

        # Player 1 wins → use provided suit
        if self.high_bidder_index == 0:
            if player_trump_suit is None:
                # Don't assign anything yet; UI will prompt player
                return None
            self.trump_suit = player_trump_suit
            print(f"Player 1 chooses trump: {self.trump_suit}")
        else:
            # Bot wins → random suit
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
            "trump_suit": trump_suit
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

def build_game_context():
    user_hand = deck.player1.show_hand()
    user_bid = deck.player1.bid

    # Convert each card to its image path
    hand_images = [f"/static/cards/{card_to_image(card)}" for card in user_hand]
    back_images = [f"/static/cards/card_back.png" for card in user_hand]
    played_images = [f"/static/cards/{card_to_image(card)}" for card in deck.played_cards]

    return {
        "hand_images": hand_images,
        "back_images": back_images,
        "played_images": played_images,
        "user_bid": user_bid,
        "show_bid_modal": user_bid is None,
        "bids": getattr(deck.round, "bids", {}),
        "dealer": getattr(deck.round, "dealer", None),
        "winning_bidder": getattr(deck.round, "winning_bidder", None),
        "winning_bid": getattr(deck.round, "winning_bid", None),
        "trump_suit": deck.round.trumpSuit,
    }

#Task: API call to define starting a new game
#Precondition: All associated objects have been created
#Postcondition: The user can restart the game
@app.route("/start_game")
def start_game():
    global deck, game_controller  #Creating global variables
    
    deck = Deck()                 #Defining variables
    game_controller = GameController()
    
    deck.deal()                   #Calling necessary functions
    game_controller.start_game()
    return redirect("/game")

#Task: API call to define the gameboard screen and functions
#Precondition: All associated objects have been initialized
#Postcondition: The gameboard screen is displayed
@app.route("/game")
def home():
    global deck

    if deck is None:
        deck = Deck()
        deck.deal()

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
        player_bid=deck.player1.bid
    )

    # Store bidding results
    deck.round.bids = bids
    deck.round.winning_bidder = winning_player
    deck.round.winning_bid = winning_bid

    # If player won bid, just go back to game and let UI prompt for trump
    if winning_player == "Player 1":
        # Trump not assigned yet → let user pick
        deck.round.trumpSuit = None
        return redirect("/game")

    # Bot wins → pick random trump immediately
    trump_suit = game_controller.bid_manager.choose_trump_suit()
    deck.round.trumpSuit = trump_suit
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

#Task: API call to define the card selection function
#Precondition: The cards have been dealt & it's the player's turn
#Postcondition: The selected card will be removed from the player's hand and moved to the discard pile
@app.route("/play_card", methods=["GET", "POST"])
def play_card():
    global deck
    if deck is None:
        return "Game not started."

    index = int(request.form["index"])

    #User plays a card
    card = deck.player1.play_card(index, deck=deck)
    print(f"User played {card}")

    #Update the round state
    if deck.round.lead_suit is None:
        deck.round.lead_suit = card[0]

    deck.round.current_trick.append(card)

    #Bots play after the user
    for bot_player in [deck.player2, deck.player3, deck.player4]:
        bot_card = bot_player.choose_card(deck.round)
        if bot_card:
            deck.round.current_trick.append(bot_card)
            deck.played_cards.append(bot_card)
            print(f"{bot_player.name} played {bot_card}")
    
    #After all 4 players play, restart trick
    if len(deck.round.current_trick) == 4:
        deck.round.current_trick = []
        deck.round.lead_suit = None

    return redirect("/game")
                
if __name__ == "__main__":
    app.run(debug=True)