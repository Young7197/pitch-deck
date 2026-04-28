#Libraries needed
import random
from flask import Flask, render_template, redirect

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
        for suit, card in player.hand:
            
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

        for suit, rank in player.hand:
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
            return -bid

def safe_name(player):
    return player.name if hasattr(player, "name") else player

def Main(deck):

    player1 = deck.player1
    player2 = deck.player2
    player3 = deck.player3
    player4 = deck.player4

    wins = {
        player1: [],
        player2: [],
        player3: [],
        player4: []
    }

    players = [player1, player2, player3, player4]

    trump = random.choice(deck.suits)
    bidWinner = random.choice(players)
    bidAmount = random.randint(2, 10)

    calc = calcScore(deck, trump)

    # reset round points
    roundPoints = {
        player1: 0,
        player2: 0,
        player3: 0,
        player4: 0
    }

    # -----------------------
    # GAME POINTS
    # -----------------------
    gameScores = {p: calc.game(p) for p in players}
    gameWinnerPlayer = max(gameScores, key=gameScores.get)
    roundPoints[gameWinnerPlayer] += 1
    wins[gameWinnerPlayer].append("Game")

    # -----------------------
    # HIGH / LOW
    # -----------------------
    highs = {}
    lows = {}

    for p in players:
        high, low = calc.HighLow(p, trump)
        highs[p] = high
        lows[p] = low

    valid_highs = {p: c for p, c in highs.items() if c}
    valid_lows = {p: c for p, c in lows.items() if c}

    if valid_highs:
        highWinnerPlayer = max(valid_highs, key=lambda p: deck.rankCards[valid_highs[p]])
        roundPoints[highWinnerPlayer] += 1
        wins[highWinnerPlayer].append("High")
    else:
        highWinnerPlayer = None

    if valid_lows:
        lowWinnerPlayer = min(valid_lows, key=lambda p: deck.rankCards[valid_lows[p]])
        roundPoints[lowWinnerPlayer] += 1
        wins[lowWinnerPlayer].append("Low")
    else:
        lowWinnerPlayer = None

    # -----------------------
    # FIVE / NINE / JACK
    # -----------------------
    fiveWinner = nineWinner = jackWinner = None

    for p in players:
        five, nine, jack = calc.fiveNineJack(p, trump)

        if five and fiveWinner is None:
            fiveWinner = p
            roundPoints[p] += 5
            wins[p].append("5")

        if nine and nineWinner is None:
            nineWinner = p
            roundPoints[p] += 9
            wins[p].append("9")

        if jack and jackWinner is None:
            jackWinner = p
            roundPoints[p] += 1
            wins[p].append("Jack")

    # -----------------------
    # BID LOGIC
    # -----------------------
    if bidWinner:
        roundPoints[bidWinner] = calc.makeBid(
            bidAmount,
            bidWinner,
            roundPoints[bidWinner]
        )

    # -----------------------
    # TOTAL SCORE UPDATE
    # -----------------------
    for p in players:
        p.points += roundPoints[p]

    # -----------------------
    # RETURN CLEAN DATA
    # -----------------------
    return (
        bidWinner.name,
        bidAmount,

        safe_name(gameWinnerPlayer),
        safe_name(highWinnerPlayer),
        safe_name(lowWinnerPlayer),

        safe_name(fiveWinner),
        safe_name(nineWinner),
        safe_name(jackWinner),

        roundPoints[player1],
        roundPoints[player2],
        roundPoints[player3],
        roundPoints[player4],

        player1.points,
        player2.points,
        player3.points,
        player4.points,

        wins[player1],
        wins[player2],
        wins[player3],
        wins[player4]
    )

def get_player_wins(player_name, game_state):
    wins = []

    if game_state['game_winner_player'] == player_name:
            wins.append("Game")
    if game_state['high_winner_player'] == player_name:
            wins.append("High")
    if game_state['low_winner_player'] == player_name:
            wins.append("Low")
    if game_state['five_winner'] == player_name:
            wins.append("5")
    if game_state['nine_winner'] == player_name:
            wins.append("9")
    if game_state['jack_winner'] == player_name:
            wins.append("Jack")

    return wins

deck = Deck()
deck.deal()

@app.route('/score_board')
def gameboard():
    global deck

    results = Main(deck)

    (
        bidWinner, bidAmount,
        gameWinnerPlayer, highWinnerPlayer, lowWinnerPlayer,
        fiveWinner, nineWinner, jackWinner,
        player1Points, player2Points, player3Points, player4Points,
        player1Total, player2Total, player3Total, player4Total,
        player1Wins, player2Wins, player3Wins, player4Wins
    ) = results

    game_state = {
        'bid_winner': bidWinner,
        'bid_amount': bidAmount,

        'game_winner_player': gameWinnerPlayer,
        'high_winner_player': highWinnerPlayer,
        'low_winner_player': lowWinnerPlayer,
        'five_winner': fiveWinner,
        'nine_winner': nineWinner,
        'jack_winner': jackWinner,

        'player1_points': player1Points,
        'player2_points': player2Points,
        'player3_points': player3Points,
        'player4_points': player4Points,

        'player1_total': player1Total,
        'player2_total': player2Total,
        'player3_total': player3Total,
        'player4_total': player4Total,


        'player1_wins': player1Wins,
        'player2_wins': player2Wins,
        'player3_wins': player3Wins,
        'player4_wins': player4Wins,
    }

    return render_template('scoreBoard.html', game_state=game_state)

        
@app.route("/new_score")
def newScore():
        global deck

        # Reset deck and round
        deck = Deck()
        deck.deal()

        return redirect("/score_board")

if __name__ == "__main__":
    app.run(debug=True)