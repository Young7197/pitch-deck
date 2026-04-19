#Libraries needed
import random
from flask import Flask, render_template

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

        #ranking card values
        self.rankCards = {
            "1": 1,
            "2": 2,
            "3": 3, 
            "4": 4,
            "5": 5,
            "6": 6,
            "7": 7,
            "8": 8,
            "9": 9,
            "10": 10,
            "Jack": 11,
            "Queen": 12,
            "King": 13,
            "Ace": 14
        }
        
        #Defining Players (Player1, Player2, Player3, Dealer)
        self.player1 = Player("Player 1") #User
        self.player2 = Player("Player 2")    #Bot
        self.player3 = Player("Player 3")    #Bot
        self.player4 = Player("Player 4")    #Bot

        #Defining the list to keep track of played cards
        self.played_cards = []

        #Defining the game state
        #self.round = Round()
        
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
        self.points = 0       #number of points

        #temp; only to get scoring logic working
        self.suitsInHand = []  #the suits in a players hand
        self.valuesInHand = [] #the values in players hand

    #Task: Adds card to a player's hand
    #Precondition: Round must start
    #Postcondition: Each player will have a random card in their hand    
    def add_card(self, suit, card):
        self.hand.append((suit, card))
        self.suitsInHand.append(suit)
        self.valuesInHand.append(card)

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


#Class calculates score
class calcScore:

    def __init__(self, deck, trump):
        self.deck = deck
        self.trump = trump

    def game(self, player):

        #sets game points for round at 0
        gamePoints = 0

        #goes through each card value to calculate the points
        for card in player.valuesInHand:
            
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

        for card in player.hand:
            suit, rank = card    #defines card layout
            if suit == trump:
                trumpCards.append(rank)  #adds all players trump cards to 

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
            roundPoints = roundPoints - roundPoints - bid
            return roundPoints

def Main():

    #creating a deck and dealing
    deck = Deck()
    deck.deal()

    #creates the players becasue only exists in deck
    player1 = deck.player1
    player2 = deck.player2
    player3 = deck.player3
    player4 = deck.player4

    #temp; this will be found out by the players playing round
    bidWinner = random.choice(["player1", "player2", "player3", "player4"])
    bidAmount = random.choice(range(2, 19))

    #temp; just determining trump for calculations
    if bidWinner == "player1":
        trump = random.choice(player1.suitsInHand)
    elif bidWinner == "player2":
        trump = random.choice(player2.suitsInHand)
    elif bidWinner == "player3":
        trump = random.choice(player3.suitsInHand)
    else:
        trump = random.choice(player4.suitsInHand)

    calc = calcScore(deck, trump)

    #amount at the start of each round
    player1Points = 0
    player2Points = 0
    player3Points = 0
    player4Points = 0

    #running Game calculations
    player1Game = calc.game(player1)
    player2Game = calc.game(player2)
    player3Game = calc.game(player3)
    player4Game = calc.game(player4)

    #find who had the highest game
    gameWinner = max(player1Game, player2Game, player3Game, player4Game)

    #gives player who won game point
    if gameWinner == player1Game:
        player1Points = player1Points + 1
        gameWinnerPlayer = player1
    elif gameWinner == player2Game:
        player2Points = player2Points + 1
        gameWinnerPlayer = player2
    elif gameWinner == player3Game:
        player3Points = player3Points + 1
        gameWinnerPlayer = player3
    else:
        player4Points = player4Points + 1
        gameWinnerPlayer = player4

    #calls functions
    player1High, player1Low = calc.HighLow(player1, trump)
    player2High, player2Low = calc.HighLow(player2, trump)
    player3High, player3Low = calc.HighLow(player3, trump)
    player4High, player4Low = calc.HighLow(player4, trump)

    #finds high and low
    highs = [p for p in [player1High, player2High, player3High, player4High] if p is not None]
    lows = [p for p in [player1Low, player2Low, player3Low, player4Low] if p is not None]

    highWinner = max(highs, key=lambda c: deck.rankCards[c])
    lowWinner = min(lows, key=lambda c: deck.rankCards[c])

    #Gives player high point
    if highWinner == player1High:
        player1Points = player1Points + 1
        highWinnerPlayer = player1
    elif highWinner == player2High:
        player2Points = player2Points + 1
        highWinnerPlayer = player2
    elif highWinner == player3High:
        player3Points = player3Points + 1
        highWinnerPlayer = player3
    else: 
        player4Points = player4Points + 1
        highWinnerPlayer = player4

    #gives player low point
    if lowWinner == player1Low:
        player1Points = player1Points + 1
        lowWinnerPlayer = player1
    elif lowWinner == player2Low:
        player2Points = player2Points + 1
        lowWinnerPlayer = player2
    elif lowWinner == player3Low:
        player3Points = player3Points + 1
        lowWinnerPlayer = player3
    else:
        player4Points = player4Points + 1
        lowWinnerPlayer = player4

    #checks if each player yearned the five, nine or Jack
    player1Five, player1Nine, player1Jack = calc.fiveNineJack(player1, trump)
    player2Five, player2Nine, player2Jack = calc.fiveNineJack(player2, trump)
    player3Five, player3Nine, player3Jack = calc.fiveNineJack(player3, trump)
    player4Five, player4Nine, player4Jack = calc.fiveNineJack(player4, trump)

    #gives correct player the five points
    if player1Five == True:
        player1Points = player1Points + 5
        fiveWinner = player1
    elif player2Five == True:
        player2Points = player2Points + 5
        fiveWinner = player2
    elif player3Five == True:
        player3Points = player3Points + 5
        fiveWinner = player3
    elif player4Five == True:
        player4Points = player4Points + 5
        fiveWinner = player4
    else:
        fiveWinner = None

    #gives correct player the nine points
    if player1Nine == True:
        player1Points = player1Points + 9
        nineWinner = player1
    elif player2Nine == True:
        player2Points = player2Points + 9
        nineWinner = player2
    elif player3Nine == True:
        player3Points = player3Points + 9
        nineWinner = player3
    elif player4Nine == True:
        player4Points = player4Points + 9
        nineWinner = player4
    else:
        nineWinner = None

    #gives correct player the Jack point
    if player1Jack == True:
        player1Points = player1Points + 1
        jackWinner = player1
    elif player2Jack == True:
        player2Points = player2Points + 1
        jackWinner = player2
    elif player3Jack == True:
        player3Points = player3Points + 1
        jackWinner = player3
    elif player4Jack == True:
        player4Points = player4Points + 1
        jackWinner = player4
    else:
        jackWinner = None

    #determines if the winner of the bid, made thir bid
    if bidWinner == "player1":
        player1Points = calc.makeBid(bidAmount, bidWinner, player1Points)
    elif bidWinner == "player2":
        player2Points = calc.makeBid(bidAmount, bidWinner, player2Points)
    elif bidWinner == "player3":
        player3Points = calc.makeBid(bidAmount, bidWinner, player3Points)
    else:
        player4Points = calc.makeBid(bidAmount, bidWinner, player4Points)

    #adds points to player
    player1.points = player1.points + (player1Points or 0)
    player2.points = player2.points + (player2Points or 0)
    player3.points = player3.points + (player3Points or 0)
    player4.points = player4.points + (player4Points or 0)

    return bidWinner, bidAmount, gameWinnerPlayer, highWinnerPlayer, lowWinnerPlayer, fiveWinner, nineWinner, jackWinner, player1Points, player2Points, player3Points, player4Points

@app.route('/score_board')
def gameboard():

    bid_winner, bid_amount, game_winner_player, high_winner_player, low_winner_player, five_winner, nine_winner, jack_winner, player1_points, player2_points, player3_points, player4_points = Main()

    # Prepare game state to pass to the template
    game_state = {
        'bid_winner': bid_winner,
        'bid_amount': bid_amount,
        'game_winner_player': game_winner_player.name,
        'high_winner_player': high_winner_player.name,
        'low_winner_player': low_winner_player.name,
        'five_winner': five_winner.name if five_winner else 'None',
        'nine_winner': nine_winner.name if nine_winner else 'None',
        'jack_winner': jack_winner.name if jack_winner else 'None',
        'player1_points': player1_points,
        'player2_points': player2_points,
        'player3_points': player3_points,
        'player4_points': player4_points
    }

    return render_template('scoreBoard.html', game_state=game_state)
    
@app.route("/new_score")
def newScore():
    bid_winner, bid_amount, game_winner_player, high_winner_player, low_winner_player, five_winner, nine_winner, jack_winner, player1_points, player2_points, player3_points, player4_points  = Main()
    
    game_state = {
        'bid_winner': bid_winner,
        'bid_amount': bid_amount,
        'game_winner_player': game_winner_player.name,
        'high_winner_player': high_winner_player.name,
        'low_winner_player': low_winner_player.name,
        'five_winner': five_winner.name if five_winner else 'None',
        'nine_winner': nine_winner.name if nine_winner else 'None',
        'jack_winner': jack_winner.name if jack_winner else 'None',
        'player1_points': player1_points,
        'player2_points': player2_points,
        'player3_points': player3_points,
        'player4_points': player4_points
    }

    return render_template('scoreBoard.html', game_state=game_state)

if __name__ == "__main__":
    app.run(debug=True)