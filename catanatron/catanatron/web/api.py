import json
import logging
import traceback
from typing import List

from flask import Response, Blueprint, jsonify, abort, request

from catanatron.web.models import upsert_game_state, get_game_state
from catanatron.json import GameEncoder, action_from_json
from catanatron.models.player import Color, Player, RandomPlayer, WebHookPlayer
from catanatron.game import Game
from catanatron.players.value import ValueFunctionPlayer
from catanatron.players.minimax import AlphaBetaPlayer
from catanatron.cli.cli_players import CLI_PLAYERS
import re
from catanatron.web.mcts_analysis import GameAnalyzer

bp = Blueprint("api", __name__, url_prefix="/api")


def player_factory(player_key):
    if player_key[0] == "CATANATRON":
        return AlphaBetaPlayer(player_key[1], 2, True)
    elif player_key[0] == "RANDOM":
        return RandomPlayer(player_key[1])
    elif player_key[0] == "HUMAN":
        return ValueFunctionPlayer(player_key[1], is_bot=False)
    else:
        raise ValueError("Invalid player key")


def player_factory_v2(player_dict):
    name = player_dict.get("name") or "Player"
    color = Color[player_dict["color"].upper()]
    webhook = player_dict.get("webhook")

    # WebHook player takes precedence
    if webhook:
        return WebHookPlayer(color, webhook, name=name)

    upper = name.upper()
    parts = upper.split(":")
    code = parts[0]
    params = parts[1:]

    match = re.match(r"([A-Z]+)(\d+)$", code)
    if match:
        code = match.group(1)
        params = [match.group(2)] + params

    for cli_player in CLI_PLAYERS:
        if cli_player.code == code:
            return cli_player.import_fn(color, *params, name=name)

    if upper in ("CATANATRON", "ALPHABETA"):
        return AlphaBetaPlayer(color, 2, True, name=name)
    elif upper == "RANDOM":
        return RandomPlayer(color, name=name)
    elif upper == "HUMAN":
        return ValueFunctionPlayer(color, is_bot=False, name=name)
    else:
        raise ValueError(
            f"Unknown player type or missing webhook for custom bot: {name}"
        )


@bp.route("/games", methods=("POST",))
def post_game_endpoint():
    if not request.is_json or request.json is None or "players" not in request.json:
        abort(400, description="Missing or invalid JSON body: 'players' key required")
    players_data = request.json["players"]
    # Support old format: ["RANDOM", "HUMAN", ...]
    if players_data and isinstance(players_data[0], str):
        players = list(map(player_factory, zip(players_data, Color)))
    else:
        players = [player_factory_v2(p) for p in players_data]
    game = Game(players=players)
    upsert_game_state(game)
    return jsonify({"game_id": game.id})


@bp.route("/games/<string:game_id>/states/<string:state_index>", methods=("GET",))
def get_game_endpoint(game_id, state_index):
    parsed_state_index = _parse_state_index(state_index)
    game = get_game_state(game_id, parsed_state_index)
    if game is None:
        abort(404, description="Resource not found")

    return Response(
        response=json.dumps(game, cls=GameEncoder),
        status=200,
        mimetype="application/json",
    )


@bp.route("/games/<string:game_id>/actions", methods=["POST"])
def post_action_endpoint(game_id):
    game = get_game_state(game_id)
    if game is None:
        abort(404, description="Resource not found")

    if game.winning_color() is not None:
        return Response(
            response=json.dumps(game, cls=GameEncoder),
            status=200,
            mimetype="application/json",
        )

    # TODO: remove `or body_is_empty` when fully implement actions in FE
    body_is_empty = (not request.data) or request.json is None or request.json == {}
    if game.state.current_player().is_bot or body_is_empty:
        game.play_tick()
        upsert_game_state(game)
    else:
        action = action_from_json(request.json)
        game.execute(action)
        upsert_game_state(game)

    return Response(
        response=json.dumps(game, cls=GameEncoder),
        status=200,
        mimetype="application/json",
    )


@bp.route("/stress-test", methods=["GET"])
def stress_test_endpoint():
    players = [
        AlphaBetaPlayer(Color.RED, 2, True),
        AlphaBetaPlayer(Color.BLUE, 2, True),
        AlphaBetaPlayer(Color.ORANGE, 2, True),
        AlphaBetaPlayer(Color.WHITE, 2, True),
    ]
    game = Game(players=players)
    game.play_tick()
    return Response(
        response=json.dumps(game, cls=GameEncoder),
        status=200,
        mimetype="application/json",
    )


@bp.route(
    "/games/<string:game_id>/states/<string:state_index>/mcts-analysis", methods=["GET"]
)
def mcts_analysis_endpoint(game_id, state_index):
    """Get MCTS analysis for specific game state."""
    logging.info(f"MCTS analysis request for game {game_id} at state {state_index}")

    # Convert 'latest' to None for consistency with get_game_state
    parsed_state_index = _parse_state_index(state_index)
    try:
        game = get_game_state(game_id, parsed_state_index)
        if game is None:
            logging.error(
                f"Game/state not found: {game_id}/{state_index}"
            )  # Use original state_index for logging
            abort(404, description="Game state not found")

        analyzer = GameAnalyzer(num_simulations=100)
        probabilities = analyzer.analyze_win_probabilities(game)

        logging.info(f"Analysis successful. Probabilities: {probabilities}")
        return Response(
            response=json.dumps(
                {
                    "success": True,
                    "probabilities": probabilities,
                    "state_index": (
                        parsed_state_index
                        if parsed_state_index is not None
                        else len(game.state.actions)
                    ),
                }
            ),
            status=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"Error in MCTS analysis endpoint: {str(e)}")
        logging.error(traceback.format_exc())
        return Response(
            response=json.dumps(
                {"success": False, "error": str(e), "trace": traceback.format_exc()}
            ),
            status=500,
            mimetype="application/json",
        )


def _parse_state_index(state_index_str: str):
    """Helper function to parse and validate state_index."""
    if state_index_str == "latest":
        return None
    try:
        return int(state_index_str)
    except ValueError:
        abort(
            400,
            description="Invalid state_index format. state_index must be an integer or 'latest'.",
        )


# ===== Debugging Routes
# @app.route(
#     "/games/<string:game_id>/players/<int:player_index>/features", methods=["GET"]
# )
# def get_game_feature_vector(game_id, player_index):
#     game = get_game_state(game_id)
#     if game is None:
#         abort(404, description="Resource not found")

#     return create_sample(game, game.state.colors[player_index])


# @app.route("/games/<string:game_id>/value-function", methods=["GET"])
# def get_game_value_function(game_id):
#     game = get_game_state(game_id)
#     if game is None:
#         abort(404, description="Resource not found")

#     # model = tf.keras.models.load_model("data/models/mcts-rep-a")
#     model2 = tf.keras.models.load_model("data/models/mcts-rep-b")
#     feature_ordering = get_feature_ordering()
#     indices = [feature_ordering.index(f) for f in NUMERIC_FEATURES]
#     data = {}
#     for color in game.state.colors:
#         sample = create_sample_vector(game, color)
#         # scores = model.call(tf.convert_to_tensor([sample]))

#         inputs1 = [create_board_tensor(game, color)]
#         inputs2 = [[float(sample[i]) for i in indices]]
#         scores2 = model2.call(
#             [tf.convert_to_tensor(inputs1), tf.convert_to_tensor(inputs2)]
#         )
#         data[color.value] = float(scores2.numpy()[0][0])

#     return data
