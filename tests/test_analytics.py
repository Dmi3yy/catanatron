from unittest.mock import patch, MagicMock

from catanatron.analytics import build_analytics
from catanatron.game import Game
from catanatron.models.player import Color, SimplePlayer, WebHookPlayer


def test_build_analytics_basic():
    players = [SimplePlayer(Color.RED), SimplePlayer(Color.BLUE)]
    game = Game(players)
    actions = game.state.playable_actions
    analytics = build_analytics(game, Color.RED, actions)
    assert "players" in analytics
    assert "board" in analytics
    assert "available_actions" in analytics
    assert len(analytics["available_actions"]) == len(actions)
    assert analytics["players"][Color.RED.value]["victory_points"] >= 0


def test_webhook_player_sends_analytics():
    bot = WebHookPlayer(Color.RED, "http://example.com")
    other = SimplePlayer(Color.BLUE)
    game = Game([bot, other])

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"action_index": 0}
    mock_resp.raise_for_status.return_value = None

    with patch(
        "catanatron.models.player.requests.post", return_value=mock_resp
    ) as mock_post:
        bot.decide(game, game.state.playable_actions)
        assert mock_post.called
        sent = mock_post.call_args.kwargs["json"]
        assert "analytics" in sent
        assert "available_actions" in sent["analytics"]
