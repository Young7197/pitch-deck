#Libraries needed
from flask import Flask, request, render_template, redirect, jsonify
import random

# Initialize Flask
app = Flask(__name__)

deck = None

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
        self.player2 = Player("Player 2") #Bot
        self.player3 = Player("Player 3") #Bot
        self.player4 = Player("Player 4") #Bot

        #Defining the list to keep track of played cards
        self.played_cards = []
        
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
    
#Task: Connects the card to their appropiate image
#Precondition: Cards are created
#Postcondition: Visible cards will have an associated image attached
def card_to_image(card):
    suit, rank = card
    return f"{suit}_{rank}.png"

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

#Round object
class Round:
    #Constructor
    def __init__(self):
        roundNumber = 0      #Number of the round
        trumpSuit = '???'    #Trump suit for round

#API starting game
@app.route("/start_game")
def start_game():
    global deck              #creating global variable
    deck = Deck()            #defining variable
    deck.deal()              #calling deal function
    return redirect("/game")

@app.route("/game_state")
def game_state():
    if deck is None:
        return jsonify({"error": "Game not started"})

    user_hand = deck.player1.show_hand()

    # Convert each card to its image path
    hand_images = [f"/static/cards/{card_to_image(card)}" for card in user_hand]
    played_images = [f"/static/cards/{card_to_image(card)}" for card in deck.played_cards]

    return render_template("game.html", hand_images=hand_images, played_images=played_images)
    

@app.route("/game")
def home():

    if deck is None:
        return "Game note started."

    user_hand = deck.player1.show_hand()

    # Convert each card to its image path
    hand_images = [f"/static/cards/{card_to_image(card)}" for card in user_hand]
    played_images = [f"/static/cards/{card_to_image(card)}" for card in deck.played_cards]

    return render_template("game.html", hand_images=hand_images, played_images=played_images)

@app.route("/play_card", methods=["GET", "POST"])
def play_card():
    global deck

    if deck is None:
            return "Game not started."

    index = int(request.form["index"])
    deck.player1.play_card(index, deck=deck)
    return redirect("/game")
                
if __name__ == "__main__":

    app.run(debug=True)