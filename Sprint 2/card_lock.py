# Libraries needed
from flask import Flask, request, render_template, redirect, url_for
import random

# Initialize Flask
app = Flask(__name__)


class CardValidator:
    """
    Validates whether a selected card is legal to play.

    Card format used:
        ("Hearts", "Ace")
        ("Spades", "10")
    """

    VALID_SUITS = {"Spades", "Clubs", "Hearts", "Diamonds"}

    def get_lead_suit(self, played_cards):
        """
        Return the suit of the first card played in the current trick.
        If no cards have been played yet, return None.
        """
        if not played_cards:
            return None
        return played_cards[0][0]

    def get_valid_play_cards(self, hand, trump_suit, played_cards, is_players_turn=True):
        """
        Return a list of cards the player is allowed to play.

        Rules:
        - If no card has been played yet in the trick, any card may be played.
        - Otherwise, player must follow lead suit if possible.
        - If player has no lead suit, they may play trump if possible.
        - If player has neither lead suit nor trump, any card may be played.
        """
        if not is_players_turn:
            return []

        if trump_suit not in self.VALID_SUITS:
            # If trump suit has not been chosen yet, allow any card for now
            trump_suit = None

        lead_suit = self.get_lead_suit(played_cards)

        # If player is leading, any card is valid
        if lead_suit is None:
            return hand[:]

        # Cards matching lead suit
        lead_cards = [card for card in hand if card[0] == lead_suit]

        # Cards matching trump suit
        trump_cards = [card for card in hand if trump_suit is not None and card[0] == trump_suit]

        # Must follow lead suit if possible
        if lead_cards:
            return lead_cards

        # If no lead suit cards, may play trump if possible
        if trump_cards:
            return trump_cards

        # Otherwise any card is allowed
        return hand[:]

    def validate_play(self, selected_card, hand, trump_suit, played_cards, is_players_turn=True):
        """
        Check whether the selected card is a legal play.
        Returns (True, message) or (False, message)
        """
        if not is_players_turn:
            return False, "It is not your turn."

        if selected_card not in hand:
            return False, "Selected card is not in the player's hand."

        valid_cards = self.get_valid_play_cards(
            hand=hand,
            trump_suit=trump_suit,
            played_cards=played_cards,
            is_players_turn=is_players_turn
        )

        if selected_card not in valid_cards:
            return False, "Invalid card. You must follow suit or play trump if able."

        return True, "Valid play."


# Deck Object
class Deck:
    # Constructor
    def __init__(self):
        # Defining suits and their corresponding ranks
        self.suits = ["Spades", "Clubs", "Hearts", "Diamonds"]
        self.spades = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
        self.clubs = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
        self.hearts = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
        self.diamonds = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]

        # Defining Players (Player1, Player2, Player3, Dealer)
        self.player1 = Player("Player 1")  # User
        self.player2 = Player("Player 2")  # Bot
        self.player3 = Player("Player 3")  # Bot
        self.player4 = Player("Player 4")  # Bot

        # Defining the list to keep track of played cards in the current trick
        self.played_cards = []

        # Defining the game state
        self.round = Round()

        # Validator object
        self.validator = CardValidator()

    # Task: Deals 6 random cards to each player
    def deal(self):
        for i in range(24):
            randomSuit = random.choice(self.suits)

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

            if i in list(range(0, 3)) + list(range(12, 15)):
                self.player1.add_card(randomSuit, randomCard)

            if i in list(range(3, 6)) + list(range(15, 18)):
                self.player2.add_card(randomSuit, randomCard)

            if i in list(range(6, 9)) + list(range(18, 21)):
                self.player3.add_card(randomSuit, randomCard)

            if i in list(range(9, 12)) + list(range(21, 24)):
                self.player4.add_card(randomSuit, randomCard)


# Player Object
class Player:
    # Constructor
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.bid = 0
        self.is_dealer = False

    def add_card(self, suit, card):
        self.hand.append((suit, card))

    def show_hand(self):
        return self.hand

    def play_card(self, index, deck):
        """
        Attempt to play a card from the player's hand.
        This version checks validity before removing the card.
        """
        if index < 0 or index >= len(self.hand):
            return False, "Invalid card index."

        selected_card = self.hand[index]

        is_valid, message = deck.validator.validate_play(
            selected_card=selected_card,
            hand=self.hand,
            trump_suit=deck.round.trumpSuit,
            played_cards=deck.played_cards,
            is_players_turn=True
        )

        if not is_valid:
            return False, message

        card = self.hand.pop(index)
        deck.played_cards.append(card)
        return True, f"Played {card[1]} of {card[0]}."


# Round object
class Round:
    # Constructor
    def __init__(self):
        self.roundNumber = 0
        self.trumpSuit = "Hearts"   # Set a real suit for testing


# Initializing variables
deck = Deck()
deck.deal()


def card_to_image(card):
    suit, rank = card
    return f"{suit}_{rank}.png"


@app.route("/start_game")
def start_game():
    global deck
    deck = Deck()
    deck.deal()
    return redirect("/game")


@app.route("/game")
def home():
    global deck

    if deck is None:
        deck = Deck()
        deck.deal()

    user_hand = deck.player1.show_hand()
    user_bid = deck.player1

    hand_images = [f"/static/cards/{card_to_image(card)}" for card in user_hand]
    played_images = [f"/static/cards/{card_to_image(card)}" for card in deck.played_cards]

    # Get valid cards for the player
    valid_cards = deck.validator.get_valid_play_cards(
        hand=user_hand,
        trump_suit=deck.round.trumpSuit,
        played_cards=deck.played_cards,
        is_players_turn=True
    )

    # Send valid indexes to template so you can lock invalid cards
    valid_indexes = [i for i, card in enumerate(user_hand) if card in valid_cards]

    message = request.args.get("message", "")

    return render_template(
        "game.html",
        hand_images=hand_images,
        played_images=played_images,
        user_bid=user_bid,
        round=deck.round,
        valid_indexes=valid_indexes,
        message=message
    )


@app.route("/play_card", methods=["POST"])
def play_card():
    global deck
    if deck is None:
        return "Game not started."

    index = int(request.form["index"])
    success, message = deck.player1.play_card(index, deck=deck)

    return redirect(url_for("home", message=message))


if __name__ == "__main__":
    app.run(debug=True)