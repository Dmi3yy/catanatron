from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List

from catanatron.models.enums import ActionType, SETTLEMENT, CITY
from catanatron.state_functions import (
    player_key,
    get_actual_victory_points,
    player_num_resource_cards,
    get_dev_cards_in_hand,
    get_longest_road_color,
    get_largest_army,
    get_player_buildings,
)
from catanatron.models.map import number_probability


def _compress_players_state(game: Any) -> Dict[str, Any]:
    state = game.state
    result: Dict[str, Any] = {}
    for color in state.colors:
        key = player_key(state, color)
        victory_points = get_actual_victory_points(state, color)
        resources = player_num_resource_cards(state, color)
        result[color.value] = {
            "victory_points": victory_points,
            "resources": resources,
            "dev_cards": get_dev_cards_in_hand(state, color),
            "roads_left": state.player_state[f"{key}_ROADS_AVAILABLE"],
            "settlements_left": state.player_state[f"{key}_SETTLEMENTS_AVAILABLE"],
            "cities_left": state.player_state[f"{key}_CITIES_AVAILABLE"],
            "resources_count": resources,
            "threat_level": (
                "HIGH"
                if victory_points >= 8
                else "MEDIUM" if victory_points >= 6 else "LOW"
            ),
            "has_largest_army": state.player_state.get(f"{key}_HAS_ARMY", False),
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


def _evaluate_action(action) -> Dict[str, Any]:
    """Return a description, strategic value and risk for an action."""
    typ = action.action_type
    val = action.value
    desc = _describe_action(action)
    strategic_value = "neutral"
    risk = "low"

    if typ == ActionType.ROLL:
        desc = "Roll dice to get resources"
        risk = "medium"
    elif typ == ActionType.BUILD_SETTLEMENT:
        strategic_value = "high"
    elif typ == ActionType.BUILD_CITY:
        strategic_value = "very_high"
    elif typ == ActionType.BUILD_ROAD:
        strategic_value = "medium"
    elif typ == ActionType.BUY_DEVELOPMENT_CARD:
        strategic_value = "medium"
    elif typ == ActionType.END_TURN:
        strategic_value = "low"

    return {
        "type": typ.value,
        "value": val,
        "description": desc,
        "strategic_value": strategic_value,
        "risk_level": risk,
    }


def _player_board_stats(game: Any, color) -> Dict[str, Any]:
    """Return production, variety and accessible ports for a player."""
    state = game.state
    board = state.board
    settlements = get_player_buildings(state, color, SETTLEMENT)
    cities = get_player_buildings(state, color, CITY)
    prod_counter: Counter = Counter()
    variety = set()
    for node_id in settlements:
        prod_counter += board.map.node_production[node_id]
        variety.update(board.map.node_production[node_id].keys())
    for node_id in cities:
        prod_counter += Counter(
            {k: 2 * v for k, v in board.map.node_production[node_id].items()}
        )
        variety.update(board.map.node_production[node_id].keys())

    accessible_ports = []
    for res, nodes in board.map.port_nodes.items():
        if any(n in nodes for n in settlements + cities):
            accessible_ports.append(res if res else "3:1")

    return {
        "expected_production": sum(prod_counter.values()),
        "resource_variety": len(variety),
        "ports": sorted(accessible_ports),
    }


def _board_summary(game: Any) -> Dict[str, Any]:
    summary = {
        "robber": game.state.board.robber_coordinate,
    }
    per_player = {}
    for color in game.state.colors:
        per_player[color.value] = _player_board_stats(game, color)
    summary["players"] = per_player
    return summary


def _score_node(board, node_id, city=False) -> Dict[str, Any]:
    tiles = board.map.adjacent_tiles[node_id]
    production_score = 0.0
    resources = set()
    for tile in tiles:
        if tile.resource is not None:
            production_score += number_probability(tile.number) * (2 if city else 1)
            resources.add(tile.resource)
    variety_bonus = len(resources) * 4 / 36
    has_port = any(node_id in nodes for nodes in board.map.port_nodes.values())
    port_bonus = 1 if has_port else 0
    score = production_score + variety_bonus + port_bonus
    return {
        "position": node_id,
        "score": score,
        "production_details": {
            "expected_production": production_score,
            "resource_variety": len(resources),
            "variety_bonus": variety_bonus,
            "has_port": has_port,
            "resources": [r.lower() for r in resources],
        },
        "adjacent_numbers": [
            f"{t.number}:{t.resource}" for t in tiles if t.resource is not None
        ],
    }


def _settlement_recommendations(game: Any, color) -> Dict[str, Any]:
    board = game.state.board
    recs = [_score_node(board, node_id) for node_id in board.buildable_node_ids(color)]
    recs.sort(key=lambda r: r["score"], reverse=True)
    analysis = {
        "total_positions": len(recs),
        "best_score": recs[0]["score"] if recs else 0,
        "strategy": "Focus on high-probability numbers (6,8) and resource variety",
    }
    action_rec = {
        "type": ActionType.BUILD_SETTLEMENT.value,
        "value": recs[0]["position"] if recs else None,
        "reasoning": (
            f"Best expected production ({recs[0]['score']:.2f}) with {recs[0]['production_details']['resource_variety']} resource types"
            if recs
            else ""
        ),
    }
    return {
        "best_positions": recs[:5],
        "analysis": analysis,
        "action_recommendation": action_rec,
    }


def _city_recommendations(game: Any, color) -> Dict[str, Any]:
    board = game.state.board
    settlements = get_player_buildings(game.state, color, SETTLEMENT)
    recs = [_score_node(board, node_id, city=True) for node_id in settlements]
    recs.sort(key=lambda r: r["score"], reverse=True)
    return {
        "best_upgrades": recs[:5],
        "analysis": {
            "total_options": len(recs),
            "best_score": recs[0]["score"] if recs else 0,
        },
    }


def build_analytics(game: Any, my_color: Any, playable_actions: List) -> Dict[str, Any]:
    """Return a lightweight analytics dictionary for the given state."""
    players_state = _compress_players_state(game)
    board = _board_summary(game)
    board["longest_road_color"] = get_longest_road_color(game.state)
    board["largest_army_color"] = get_largest_army(game.state)[0]
    available = [_evaluate_action(a) for a in playable_actions]
    analytics = {
        "players": players_state,
        "board": board,
        "available_actions": available,
        "settlement_recommendations": _settlement_recommendations(game, my_color),
        "city_recommendations": _city_recommendations(game, my_color),
    }
    return analytics
