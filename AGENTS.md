# Guidelines for Repository Contributors

This repository hosts **Catanatron**, a high–performance Settlers of Catan simulator with optional web and UI components.

## Development Environment
- Use Python 3.11 or newer.
- Install dependencies with the optional extras to run tests and the web server:
  ```bash
  pip install .[web,gym,dev]
  ```
- Format Python code with **black** before committing:
  ```bash
  black catanatron catanatron_experimental
  ```
- Run the full test suite with coverage:
  ```bash
  coverage run --source=catanatron -m pytest tests/ && coverage report
  ```
- The frontend lives in `ui/` and requires Node.js `$(cat ui/.nvmrc)` (currently 24). Install dependencies and run tests with:
  ```bash
  npm ci
  npm run test
  ```

## Documentation
- Sphinx documentation is under `docs/`. Build it with:
  ```bash
  make -C docs html
  ```

## Pull Requests
- Keep commits focused and descriptive.
- Ensure all tests pass and code is formatted prior to opening a PR.

# AGENTS.md

## Project Overview

**Catanatron** is a platform for simulation, analysis, and automation of the "Settlers of Catan" game, supporting various agent types (bots, AI, webhooks, human). The project allows you to create, test, and integrate different game strategies, as well as generate advanced analytics for decision-making.

---

## Key Folders and Files for Agents and Analytics

- `catanatron/catanatron/models/player.py` — base player classes (Player, HumanPlayer, RandomPlayer, WebHookPlayer, etc.)
- `catanatron/catanatron/players/` — implementations of various bots (MCTS, AlphaBeta, Minimax, Playouts, Value, WeightedRandom, etc.)
- `catanatron/catanatron/features.py` — functions for extracting features from the game state (production, variety, VP, resources, etc.)
- `catanatron/catanatron/state_functions.py` — getters/helpers for working with the game state (resources, VP, longest road, etc.)
- `catanatron/catanatron/game.py` — main game logic, state management
- `catanatron/catanatron/analytics.py` — (to be created) module for advanced analytics and recommendations
- `catanatron/catanatron/web/` — API, webhook integration, serialization

---

## PRD (Product Requirements Document)

1. **Goal:**
   - Add the ability to generate advanced analytics and recommendations for agents (bots, AI, UI, webhooks) to the game core.
   - Analytics should include both "raw" and processed data (position evaluations, strategic hints, action recommendations, AI/bot weights).

2. **Users:**
   - Bot/agent developers
   - UI/webhook developers
   - AI/ML researchers for Catan

3. **Main Scenarios:**
   - Receiving a compressed game state with analytics via WebHookPlayer/API
   - Using AI/bot recommendations for decision-making
   - Visualizing analytics in the UI

4. **Requirements:**
   - Centralized analytics module (`analytics.py`)
   - Easy extensibility for new metrics/evaluations
   - Integration with existing core functions (features, state_functions, bots)
   - Documented analytics structure for frontend/bots

---

## Roadmap

1. **Create analytics module**
   - [x] Add `catanatron/catanatron/analytics.py` with `build_analytics(game, my_color, playable_actions)`

2. **Integrate analytics into WebHookPlayer**
   - [x] Add `analytics` field to the JSON sent to the webhook

3. **Implement basic analytics**
   - [x] Compressed player state (resources, VP, dev cards, buildings)
   - [x] Compressed opponents state
   - [x] Board summary (production, variety, robber, ports)
  - [x] Action evaluation (description, risk, strategic value)
  - [x] Settlement/city recommendations (production, variety, port bonus)
  - [ ] Strategic hints (threat, position, discard risk)

4. **Add AI/bot recommendations**
   - [ ] Call AlphaBeta/MCTS at depth 1-2 for action evaluation
   - [ ] Add weights/scores to available_actions
   - [ ] Add top-2 moves to `bot_predictions`

5. **Document analytics structure**
   - [ ] Describe the `analytics` field structure for frontend/bots

6. **Extensions**
   - [ ] Add heatmap/tensor features for the board (optional)
   - [ ] Add action history, advanced strategic hints
   - [ ] Allow specifying bot codes like `AB:2` or `G:10` in the `POST /api/games` JSON payload

---

## Analytics Structure Example

```json
{
  "my_state": { ... },
  "opponents": [ ... ],
  "board_summary": { ... },
  "available_actions": [ ... ],
  "settlement_recommendations": { ... },
  "strategic_analysis": { ... },
  "bot_predictions": [ ... ]
}
```

---

## Example: Compressed Game State (JS logic for reference)

```js
const myState = {
  color: myColor,
  victory_points: getValue("VICTORY_POINTS"),
  actual_vp: getValue("ACTUAL_VICTORY_POINTS"),
  resources: {
    wood: getValue("WOOD_IN_HAND"),
    brick: getValue("BRICK_IN_HAND"),
    sheep: getValue("SHEEP_IN_HAND"),
    wheat: getValue("WHEAT_IN_HAND"),
    ore: getValue("ORE_IN_HAND")
  },
  dev_cards: {
    knight: getValue("KNIGHT_IN_HAND"),
    victory_point: getValue("VICTORY_POINT_IN_HAND"),
    monopoly: getValue("MONOPOLY_IN_HAND"),
    road_building: getValue("ROAD_BUILDING_IN_HAND"),
    year_of_plenty: getValue("YEAR_OF_PLENTY_IN_HAND")
  },
  buildings_left: {
    roads: getValue("ROADS_AVAILABLE"),
    settlements: getValue("SETTLEMENTS_AVAILABLE"),
    cities: getValue("CITIES_AVAILABLE")
  },
  longest_road: getValue("LONGEST_ROAD_LENGTH")
};

const opponents = gameData.colors
  .map((color, index) => {
    if (color === myColor) return null;
    const oppState = (key) => gameData.player_state?.[`P${index}_${key}`] ?? 0;
    return {
      color,
      vp: oppState("VICTORY_POINTS"),
      actual_vp: oppState("ACTUAL_VICTORY_POINTS"),
      longest_road: oppState("LONGEST_ROAD_LENGTH"),
      has_largest_army: oppState("HAS_ARMY"),
      resources_count: oppState("WOOD_IN_HAND") + oppState("BRICK_IN_HAND") +
                       oppState("SHEEP_IN_HAND") + oppState("WHEAT_IN_HAND") +
                       oppState("ORE_IN_HAND"),
      threat_level: oppState("VICTORY_POINTS") >= 8 ? "HIGH" :
                    oppState("VICTORY_POINTS") >= 6 ? "MEDIUM" : "LOW"
    };
  }).filter(Boolean);

const availableActions = (gameData.current_playable_actions || []).map(a => {
  const [color, type, val] = a;
  let desc = type;
  let strategic_value = "neutral";
  let risk = "low";

  switch (type) {
    case "ROLL":
      desc = "Roll dice to get resources";
      risk = "medium";
      break;
    case "BUILD_SETTLEMENT":
      desc = `Build settlement at ${val}`;
      strategic_value = "high";
      break;
    case "BUILD_CITY":
      desc = `Upgrade to city at ${val}`;
      strategic_value = "very_high";
      break;
    case "BUILD_ROAD":
      desc = `Build road between ${val}`;
      strategic_value = "medium";
      break;
    case "BUY_DEVELOPMENT_CARD":
      desc = "Buy development card";
      strategic_value = "medium";
      break;
    case "END_TURN":
      desc = "End current turn";
      strategic_value = "low";
      break;
  }

  return {
    type,
    value: val,
    description: desc,
    strategic_value,
    risk_level: risk
  };
});
```

---

## Example: Settlement Recommendations (JS logic for reference)

```js
const availableNodes = gameData.nodes ? Object.values(gameData.nodes)
  .filter(node => !node.building)
  .map(node => ({
    id: node.id,
    adjacent_tiles: gameData.adjacent_tiles[node.id] || [],
    score: 0
  })) : [];

const scoredPositions = availableNodes.map(node => {
  let productionScore = 0;
  let resourceTypes = new Set();
  let hasPort = false;

  node.adjacent_tiles.forEach(tile => {
    if (tile.type === "RESOURCE_TILE" && tile.number) {
      const probability = {
        2: 1, 3: 2, 4: 3, 5: 4, 6: 5,
        8: 5, 9: 4, 10: 3, 11: 2, 12: 1
      }[tile.number] || 0;
      productionScore += probability * 0.0278;
      resourceTypes.add(tile.resource.toLowerCase());
    }
    if (tile.type === "PORT") {
      hasPort = true;
    }
  });
  const varietyBonus = resourceTypes.size * 4 * 0.0278;
  const portBonus = hasPort ? 1 : 0;
  const totalScore = productionScore + varietyBonus + portBonus;
  return {
    position: node.id,
    score: totalScore,
    production_details: {
      expected_production: productionScore,
      resource_variety: resourceTypes.size,
      variety_bonus: varietyBonus,
      has_port: hasPort,
      resources: Array.from(resourceTypes)
    },
    adjacent_numbers: node.adjacent_tiles
      .filter(t => t.type === "RESOURCE_TILE")
      .map(t => `${t.number}:${t.resource}`)
  };
});

scoredPositions.sort((a, b) => b.score - a.score);

const recommendations = {
  best_positions: scoredPositions.slice(0, 5),
  analysis: {
    total_positions: scoredPositions.length,
    best_score: scoredPositions[0]?.score || 0,
    strategy: "Focus on high-probability numbers (6,8) and resource variety"
  },
  action_recommendation: {
    type: "BUILD_SETTLEMENT", 
    value: scoredPositions[0]?.position || 0,
    reasoning: `Best expected production (${(scoredPositions[0]?.score || 0).toFixed(2)}) with ${scoredPositions[0]?.production_details.resource_variety || 0} resource types`
  }
};
```

---

## About `@/players` (Bot Implementations)

The folder `catanatron/catanatron/players/` contains implementations of various bots:
- **AlphaBetaPlayer** (strongest, n=2 by default, see [Making Catanatron Stronger](https://docs.catanatron.com/advanced/making-catanatron-stronger))
- **MCTSPlayer** (Monte Carlo Tree Search)
- **MinimaxPlayer**
- **Playouts, Value, WeightedRandom** (simpler strategies)

You can use these bots to generate `bot_predictions` in analytics, e.g. by running AlphaBeta or MCTS at depth 1-2 for the current state and extracting their top recommended actions and scores.

See [official documentation](https://docs.catanatron.com/advanced/making-catanatron-stronger) for more details and leaderboard.

---

**This file is updated as tasks are completed and the project evolves!** 