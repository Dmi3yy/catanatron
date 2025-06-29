from unittest.mock import patch, MagicMock
import pytest
import requests

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
    assert "board_tensor" in analytics
    assert "available_actions" in analytics
    assert len(analytics["available_actions"]) == len(actions)
    assert analytics["players"][Color.RED.value]["victory_points"] >= 0
    # board summary should include robber and per-player info
    assert "robber" in analytics["board"]
    assert Color.RED.value in analytics["board"]["players"]
    assert "expected_production" in analytics["board"]["players"][Color.RED.value]
    assert "resources_count" in analytics["players"][Color.RED.value]
    assert "threat_level" in analytics["players"][Color.RED.value]
    first_action = analytics["available_actions"][0]
    assert "risk_level" in first_action
    assert "strategic_value" in first_action
    assert "score" in first_action
    assert "strategic_analysis" in analytics
    sa = analytics["strategic_analysis"]
    assert {"threat", "position", "discard_risk"}.issubset(sa)
    assert "bot_predictions" in analytics
    assert len(analytics["bot_predictions"]) <= 2


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
        assert "board_tensor" in sent["analytics"]
        assert "available_actions" in sent["analytics"]


def test_webhook_player_uses_five_minute_timeout():
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
        assert mock_post.call_args.kwargs.get("timeout") == 300


def test_webhook_player_raises_on_error():
    bot = WebHookPlayer(Color.RED, "http://example.com")
    other = SimplePlayer(Color.BLUE)
    game = Game([bot, other])

    with patch(
        "catanatron.models.player.requests.post",
        side_effect=requests.exceptions.Timeout,
    ) as mock_post:
        action = bot.decide(game, game.state.playable_actions)
        assert mock_post.called
        assert action == game.state.playable_actions[0]


def test_settlement_and_city_recommendations():
    players = [SimplePlayer(Color.RED), SimplePlayer(Color.BLUE)]
    game = Game(players)
    analytics = build_analytics(game, Color.RED, game.state.playable_actions)
    assert "board_tensor" in analytics
    assert "settlement_recommendations" in analytics
    rec = analytics["settlement_recommendations"]
    assert "best_positions" in rec
    assert "analysis" in rec
    assert "city_recommendations" in analytics
    city = analytics["city_recommendations"]
    assert "best_upgrades" in city
    assert "action_history" in analytics
    assert isinstance(analytics["action_history"], list)
    assert "advanced_hints" in analytics
    assert isinstance(analytics["advanced_hints"], list)
