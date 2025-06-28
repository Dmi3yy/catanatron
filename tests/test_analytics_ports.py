from catanatron.analytics import build_analytics
from catanatron.game import Game
from catanatron.models.player import Color, SimplePlayer
from catanatron.state_functions import build_settlement


def test_port_summary_from_building():
    players = [SimplePlayer(Color.RED), SimplePlayer(Color.BLUE)]
    game = Game(players)
    res, nodes = next(iter(game.state.board.map.port_nodes.items()))
    node = next(iter(nodes))
    game.state.board.build_settlement(Color.RED, node, initial_build_phase=True)
    build_settlement(game.state, Color.RED, node, True)
    analytics = build_analytics(game, Color.RED, game.state.playable_actions)
    ports = analytics["board"]["players"][Color.RED.value]["ports"]
    assert ports and (res if res else "3:1") in ports
