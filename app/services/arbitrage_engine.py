def detect_two_way_arbitrage(side_a, side_b):
    """
    Input: side_a (dict | None), side_b (dict | None)
    Output: dict | None
    Determine whether two opposing sides create an arbitrage opportunity based on implied probabilities. Return pricing and profit metadata only when the combined implied probability is below one.
    """
    if not side_a or not side_b:
        return None

    total_prob = side_a["implied_prob"] + side_b["implied_prob"]
    if total_prob >= 1:
        return None

    return {
        "profit_percent": round((1 - total_prob) * 100, 3),
        "over_book": side_a["book"],
        "under_book": side_b["book"],
        "over_odds": side_a["odds"],
        "under_odds": side_b["odds"],
    }


def _best_price_for_team(game_data, team_name):
    """
    Input: game_data (dict), team_name (str)
    Output: dict | None
    Find the best available odds for a specific team across all books in a game. Return `None` when no qualifying team price is available.
    """
    best = None
    for book, teams in game_data.get("books", {}).items():
        team_data = teams.get(team_name)
        if not team_data:
            continue

        odds = team_data["odds"]
        if best is None or odds > best["odds"]:
            best = {
                "book": book,
                "odds": odds,
                "implied_prob": team_data["implied_prob"],
            }
    return best


def detect_moneyline_arbitrage(games_by_id):
    """
    Input: games_by_id (dict[str, dict])
    Output: list[dict]
    Detect moneyline arbitrage opportunities from normalized game odds data. Build standardized opportunity rows for each game where the home and away best prices form an arbitrage.
    """
    opportunities = []

    for game_id, game in games_by_id.items():
        home = _best_price_for_team(game, game["home_team"])
        away = _best_price_for_team(game, game["away_team"])
        arb = detect_two_way_arbitrage(home, away)
        if not arb:
            continue

        opportunities.append(
            {
                "game_id": game_id,
                "market_type": "h2h",
                "player_name": None,
                "line_value": None,
                "home_team": game["home_team"],
                "away_team": game["away_team"],
                **arb,
            }
        )

    return opportunities


def _best_prop_side(books_data, side_name):
    """
    Input: books_data (dict[str, dict]), side_name (str)
    Output: dict | None
    Find the best odds for one prop side, typically Over or Under, across sportsbooks. Return `None` when that side is not present in any book entry.
    """
    best = None
    for book, sides in books_data.items():
        side_data = sides.get(side_name)
        if not side_data:
            continue

        odds = side_data["odds"]
        if best is None or odds > best["odds"]:
            best = {
                "book": book,
                "odds": odds,
                "implied_prob": side_data["implied_prob"],
            }
    return best


def detect_prop_arbitrage(normalized_props):
    """
    Input: normalized_props (dict[str, dict])
    Output: list[dict]
    Detect prop arbitrage opportunities from normalized per-game prop markets. Return standardized rows for player-line combinations where Over and Under prices create arbitrage.
    """
    opportunities = []

    for game_id, markets in normalized_props.items():
        for market_type, player_lines in markets.items():
            for _, player_line_data in player_lines.items():
                over = _best_prop_side(player_line_data["books"], "Over")
                under = _best_prop_side(player_line_data["books"], "Under")
                arb = detect_two_way_arbitrage(over, under)
                if not arb:
                    continue

                opportunities.append(
                    {
                        "game_id": game_id,
                        "market_type": market_type,
                        "player_name": player_line_data["player"],
                        "line_value": player_line_data["line"],
                        "home_team": None,
                        "away_team": None,
                        **arb,
                    }
                )

    return opportunities
