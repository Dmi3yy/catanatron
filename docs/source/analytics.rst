Analytics
=========

The :mod:`catanatron.analytics` module exposes :func:`build_analytics` which returns
a lightweight dictionary with useful information for UIs and bots. The
structure of the returned dictionary is stable and can be relied upon by
webhooks and front‑end components.

Dictionary layout
-----------------

``build_analytics(game, my_color, playable_actions)`` returns a mapping with
these top‑level keys:

``players``
    Per‑player summary including victory points, resources and threat level.
``board``
    Global board information. Includes robber position, player production stats
    and which player holds the longest road or largest army.
``available_actions``
    List of the playable actions for the current turn. Each action description
    contains a human readable ``description``, ``strategic_value``, ``risk_level``
    and a numeric ``score`` from the AlphaBeta search.
``settlement_recommendations``
    Suggested settlement locations ranked by expected production and resource
    variety.
``city_recommendations``
    Recommended settlement upgrades.
``strategic_analysis``
    High level hints such as current ranking and discard risk.
``bot_predictions``
    Top‑2 moves predicted by a shallow AlphaBeta search.

Example
-------

An abbreviated example of the analytics payload::

    {
        "players": {
            "RED": {
                "victory_points": 2,
                "resources": 3,
                "threat_level": "LOW"
            }
        },
        "board": {
            "robber": [0, 0, 0],
            "longest_road_color": null,
            "largest_army_color": null,
            "players": {
                "RED": {
                    "expected_production": 1.5,
                    "resource_variety": 2,
                    "ports": []
                }
            }
        },
        "available_actions": [
            {
                "type": "ROLL",
                "description": "Roll dice to get resources",
                "strategic_value": "neutral",
                "risk_level": "medium",
                "score": 0.0
            }
        ],
        "settlement_recommendations": {
            "best_positions": [{"position": 12, "score": 0.8}],
            "analysis": {"total_positions": 54, "best_score": 0.8},
            "action_recommendation": {"type": "BUILD_SETTLEMENT", "value": 12}
        },
        "city_recommendations": {
            "best_upgrades": []
        },
        "strategic_analysis": {"threat": "LOW", "position": 1, "discard_risk": false},
        "bot_predictions": [
            {"type": "END_TURN", "score": 0.0, "risk_level": "low", "strategic_value": "low", "description": "End current turn"}
        ]
    }

