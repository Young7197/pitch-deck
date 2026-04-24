import importlib.util
import random
from flask import request, jsonify, redirect


# -----------------------------
# Load app file
# -----------------------------
APP_FILE = "app.py"

spec = importlib.util.spec_from_file_location("pitch_app", APP_FILE)
pitch_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pitch_app)


# -----------------------------
# Card validation logic
# -----------------------------
class CardValidator:
    """
    Works with card format:
        ("Spades", "Ace")
        ("Hearts", "10")
    """

    def normalize_suit(self, suit):
        """Make suit names match card format."""
        if suit is None:
            return None
        return suit.strip().capitalize()

    def get_valid_cards(self, hand, round_state):
        """
        Return the cards the player or bot is allowed to play.

        Rules:
        - If leading the trick, any card is valid.
        - If not leading, follow lead suit if possible.
        - If no lead suit cards, play trump if possible.
        - If neither lead suit nor trump is available, any card is valid.
        """
        if not hand:
            return []

        lead_suit = self.normalize_suit(round_state.lead_suit)
        trump_suit = self.normalize_suit(round_state.trumpSuit)

        # Leading the trick: any card is legal
        if lead_suit is None:
            return hand[:]

        # Must follow lead suit if possible
        lead_cards = [card for card in hand if card[0] == lead_suit]
        if lead_cards:
            return lead_cards

        # If no lead suit, play trump if possible
        trump_cards = [card for card in hand if card[0] == trump_suit]
        if trump_cards:
            return trump_cards

        # If no lead suit or trump, any card is legal
        return hand[:]

    def validate_card(self, selected_card, hand, round_state):
        """Return True/False and a message."""
        if selected_card not in hand:
            return False, "Selected card is not in your hand."

        valid_cards = self.get_valid_cards(hand, round_state)

        if selected_card not in valid_cards:
            return False, "Invalid card. You must follow suit or play trump if able."

        return True, "Valid card."


validator = CardValidator()


# -----------------------------
# Patch bot card selection
# -----------------------------
def validated_bot_choose_card(self, round_state):
    """
    Replaces Bot.choose_card so bots also obey card validation rules.
    """
    if not self.hand:
        return None

    valid_cards = validator.get_valid_cards(self.hand, round_state)

    if not valid_cards:
        return None

    points = {
        "1": 1, "2": 2, "3": 3, "4": 4,
        "5": 5, "6": 6, "7": 7, "8": 8,
        "9": 9, "10": 10, "Jack": 11,
        "Queen": 12, "King": 13, "Ace": 14,
    }

    # Simple bot strategy: play the lowest valid card
    chosen_card = min(valid_cards, key=lambda card: points.get(card[1], 0))

    self.hand.remove(chosen_card)
    return chosen_card


pitch_app.Bot.choose_card = validated_bot_choose_card


# -----------------------------
# Patch /play_card route
# -----------------------------
def validated_play_card():
    """
    Replaces the existing /play_card route behavior with validation added.
    Invalid cards are rejected before they are removed from the player's hand.
    """
    deck = pitch_app.deck

    if deck is None:
        if pitch_app.is_json_request():
            return jsonify({"ok": False, "error": "Game not started."}), 400
        return "Game not started."

    if not pitch_app.can_player_play():
        if pitch_app.is_json_request():
            return jsonify({"ok": False, "error": "Finish the bid and trump selection first."}), 409
        return redirect("/game")

    if deck.round.trick_complete:
        pitch_app.clear_completed_trick()

    try:
        index = int(request.form["index"])
    except (KeyError, TypeError, ValueError):
        if pitch_app.is_json_request():
            return jsonify({"ok": False, "error": "Invalid card selection."}), 400
        return redirect("/game")

    if index < 0 or index >= len(deck.player1.hand):
        if pitch_app.is_json_request():
            return jsonify({"ok": False, "error": "Selected card is out of range."}), 400
        return redirect("/game")

    selected_card = deck.player1.hand[index]

    # Card validation happens BEFORE pop()
    is_valid, message = validator.validate_card(
        selected_card,
        deck.player1.hand,
        deck.round
    )

    if not is_valid:
        if pitch_app.is_json_request():
            return jsonify({"ok": False, "error": message}), 400
        return redirect("/game")

    # User plays a valid card
    card = deck.player1.play_card(index)
    deck.played_cards.append(card)

    # Set lead suit if this is the first card in the trick
    if not deck.round.current_trick:
        deck.round.lead_suit = card[0]

    user_entry = {"player": deck.player1.name, "card": card}
    deck.round.current_trick.append(user_entry)

    # Bots play valid cards only
    bot_plays = []
    for bot_player in [deck.player2, deck.player3, deck.player4]:
        bot_card = bot_player.choose_card(deck.round)

        if bot_card:
            deck.played_cards.append(bot_card)

            bot_entry = {"player": bot_player.name, "card": bot_card}
            deck.round.current_trick.append(bot_entry)

            bot_plays.append({
                **pitch_app.trick_entry_to_payload(bot_entry),
                "remaining_hand_count": len(bot_player.hand),
            })

    deck.round.trick_complete = len(deck.round.current_trick) == 4

    if deck.round.trick_complete:
        deck.round.lead_suit = None

    payload = {
        "ok": True,
        "player_card": pitch_app.trick_entry_to_payload(user_entry),
        "player_card_image": pitch_app.card_to_path(card),
        "bot_plays": bot_plays,
        "hand_images": [pitch_app.card_to_path(hand_card) for hand_card in deck.player1.show_hand()],
        "bot_hand_counts": pitch_app.build_bot_hand_counts(),
        "table_cards": pitch_app.build_table_cards(),
        "trick_complete": deck.round.trick_complete,
        "round_over": pitch_app.is_round_over(),
    }

    if pitch_app.is_json_request():
        return jsonify(payload)

    return redirect("/game")


# Replace the old Flask route function without editing app.py
pitch_app.app.view_functions["play_card"] = validated_play_card


# -----------------------------
# Run the patched app
# -----------------------------
if __name__ == "__main__":
    pitch_app.app.run(debug=True)