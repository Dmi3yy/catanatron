import random
import builtins
import requests
import os
import time

from catanatron.analytics import build_analytics

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

    def __init__(self, color, is_bot=True, name=None):
        """Initialize the player

        Args:
            color(Color): the color of the player
            is_bot(bool): whether the player is controlled by the computer
            name(str): the name of the player
        """
        self.color = color
        self.is_bot = is_bot
        self.name = name if name is not None else type(self).__name__

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
        return f"{self.name}:{self.color.value}"


class SimplePlayer(Player):
    """Simple AI player that always takes the first action in the list of playable_actions"""

    def __init__(self, color, name=None):
        super().__init__(color, is_bot=True, name=name)

    def decide(self, game, playable_actions):
        return playable_actions[0]


class HumanPlayer(Player):
    """Human player that selects which action to take using standard input"""

    def __init__(self, color, is_bot=False, input_fn=builtins.input, name=None):
        super().__init__(color, is_bot, name=name)
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

    def __init__(self, color, name=None):
        super().__init__(color, is_bot=True, name=name)

    def decide(self, game, playable_actions):
        return random.choice(playable_actions)


class WebHookPlayer(Player):
    """Player that makes decisions by calling an external webhook."""

    def __init__(self, color, webhook_url, name="WebHookBot"):
        super().__init__(color, is_bot=True, name=name)
        self.webhook_url = webhook_url

    def decide(self, game, playable_actions):
        print(
            f"[WEBHOOK DECIDE] game_id={game.id} turn={game.state.num_turns} color={self.color} name={self.name} pid={os.getpid()} time={time.time()}"
        )
        # Prepare data for webhook
        # Serialize game_state minimally for webhook (expand as needed)
        game_state = {
            "current_color": (
                game.state.current_color().value
                if hasattr(game.state.current_color(), "value")
                else game.state.current_color()
            ),
            "current_prompt": str(game.state.current_prompt),
            "num_turns": game.state.num_turns,
            "actions_count": len(game.state.actions),
        }
        data = {
            "color": self.color.value,
            "name": self.name,
            "game_id": game.id,
            "game_state": game_state,
            "analytics": build_analytics(game, self.color, playable_actions),
            "actions": [
                {
                    "color": a.color.value if hasattr(a.color, "value") else a.color,
                    "action_type": (
                        a.action_type.value
                        if hasattr(a.action_type, "value")
                        else a.action_type
                    ),
                    "value": a.value,
                }
                for a in playable_actions
            ],
        }
        try:
            response = requests.post(self.webhook_url, json=data, timeout=300)
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
