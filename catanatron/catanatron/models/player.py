import random
import builtins
import requests

from enum import Enum


class Color(Enum):
    """Enum to represent the colors in the game"""

    RED = "RED"
    BLUE = "BLUE"
    ORANGE = "ORANGE"
    WHITE = "WHITE"


class Player:
    """Interface to represent a player's decision logic.

    Formulated as a class (instead of a function) so that players
    can have an initialization that can later be serialized to
    the database via pickle.
    """

    def __init__(self, color, is_bot=True):
        """Initialize the player

        Args:
            color(Color): the color of the player
            is_bot(bool): whether the player is controlled by the computer
        """
        self.color = color
        self.is_bot = is_bot

    def decide(self, game, playable_actions):
        """Should return one of the playable_actions or
        an OFFER_TRADE action if its your turn and you have already rolled.

        Args:
            game (Game): complete game state. read-only.
            playable_actions (Iterable[Action]): options right now
        """
        raise NotImplementedError

    def reset_state(self):
        """Hook for resetting state between games"""
        pass

    def __repr__(self):
        return f"{type(self).__name__}:{self.color.value}"


class SimplePlayer(Player):
    """Simple AI player that always takes the first action in the list of playable_actions"""

    def decide(self, game, playable_actions):
        return playable_actions[0]


class HumanPlayer(Player):
    """Human player that selects which action to take using standard input"""

    def __init__(self, color, is_bot=False, input_fn=builtins.input):
        super().__init__(color, is_bot)
        self.input_fn = input_fn  # this is for testing purposes

    def decide(self, game, playable_actions):
        for i, action in enumerate(playable_actions):
            print(f"{i}: {action.action_type} {action.value}")
        i = None
        while i is None or (i < 0 or i >= len(playable_actions)):
            print("Please enter a valid index:")
            try:
                x = self.input_fn(">>> ")  # Use the input_fn
                i = int(x)
            except ValueError:
                pass

        return playable_actions[i]


class RandomPlayer(Player):
    """Random AI player that selects an action randomly from the list of playable_actions"""

    def decide(self, game, playable_actions):
        return random.choice(playable_actions)


class WebHookPlayer(Player):
    """Player that makes decisions by calling an external webhook."""

    def __init__(self, color, webhook_url, name="WebHookBot"):
        super().__init__(color, is_bot=True)
        self.webhook_url = webhook_url
        self.name = name

    def decide(self, game, playable_actions):
        # Prepare data for webhook
        data = {
            "color": self.color.value,
            "name": self.name,
            "game_state": str(game),  # You may want to serialize this better
            "actions": [str(a) for a in playable_actions],
        }
        try:
            response = requests.post(self.webhook_url, json=data, timeout=120)
            response.raise_for_status()
            result = response.json()
            idx = int(result.get("action_index", 0))
            if 0 <= idx < len(playable_actions):
                return playable_actions[idx]
            else:
                return playable_actions[0]
        except Exception as e:
            print(f"WebHookPlayer({self.name}): Error: {e}")
            return playable_actions[0]

    def __repr__(self):
        return f"WebHookPlayer({self.name}):{self.color.value}"
