from __future__ import annotations

from typing import Any, Dict, List

from catanatron.models.enums import ActionType
from catanatron.state_functions import (
    player_key,
    get_actual_victory_points,
    player_num_resource_cards,
    get_dev_cards_in_hand,
    get_longest_road_color,
    get_largest_army,
)


def _compress_players_state(game: Any) -> Dict[str, Any]:
    state = game.state
    result: Dict[str, Any] = {}
    for color in state.colors:
        key = player_key(state, color)
        result[color.value] = {
            "victory_points": get_actual_victory_points(state, color),
            "resources": player_num_resource_cards(state, color),
            "dev_cards": get_dev_cards_in_hand(state, color),
            "roads_left": state.player_state[f"{key}_ROADS_AVAILABLE"],
            "settlements_left": state.player_state[f"{key}_SETTLEMENTS_AVAILABLE"],
            "cities_left": state.player_state[f"{key}_CITIES_AVAILABLE"],
        }
    return result


def _describe_action(action) -> str:
    typ = action.action_type
    val = action.value
    if typ == ActionType.BUILD_SETTLEMENT:
        return f"Build settlement at {val}"
    elif typ == ActionType.BUILD_CITY:
        return f"Upgrade to city at {val}"
    elif typ == ActionType.BUILD_ROAD:
        return f"Build road between {val}"
    elif typ == ActionType.BUY_DEVELOPMENT_CARD:
        return "Buy development card"
    elif typ == ActionType.END_TURN:
        return "End current turn"
    elif typ == ActionType.ROLL:
        return "Roll"
    else:
        return typ.value


def build_analytics(game: Any, my_color: Any, playable_actions: List) -> Dict[str, Any]:
    """Return a lightweight analytics dictionary for the given state."""
    players_state = _compress_players_state(game)
    board = {
        "robber": game.state.board.robber_coordinate,
        "longest_road_color": get_longest_road_color(game.state),
        "largest_army_color": get_largest_army(game.state)[0],
    }
    available = [
        {
            "type": a.action_type.value,
            "value": a.value,
            "description": _describe_action(a),
        }
        for a in playable_actions
    ]
    analytics = {
        "players": players_state,
        "board": board,
        "available_actions": available,
    }
    return analytics
