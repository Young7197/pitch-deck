#Libraries needed
from flask import Flask, request, render_template, redirect
import random

# Initialize Flask
app = Flask(__name__)

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
        self.bid = 0           #Player's bid (default 0)
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
            chosen_card = valid_cards[0]
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

#Initializing variables
deck = Deck()
deck.deal()

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
    }

#Task: API call to define starting a new game
#Precondition: All associated objects have been created
#Postcondition: The user can restart the game
@app.route("/start_game")
def start_game():
    global deck              #creating global variable
    deck = Deck()            #defining variable
    deck.deal()              #calling deal function
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
    if deck is None:
        return redirect("/game")

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
    
    #After all 4 players play, restart trick
    if len(deck.round.current_trick) == 4:
        deck.round.current_trick = []
        deck.round.lead_suit = None

    return redirect("/game")
                
if __name__ == "__main__":
    app.run(debug=True)