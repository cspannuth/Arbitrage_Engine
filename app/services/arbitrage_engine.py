def detect_two_way_arbitrage(side_a, side_b):
    """
    Input: side_a (dict | None), side_b (dict | None)
    Output: dict | None
    Check if two opposite sides create an arbitrage opportunity based on implied probabilities. Return price and profit data only when the total implied probability is below one.
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
    Find the best odds for one team across all sportsbooks in a game. Return `None` if no valid team price is found.
    """
    best_book = None
    best_odds = None
    best_implied_prob = None

    for book, teams in game_data.get("books", {}).items():
        team_data = teams.get(team_name)
        if not team_data:
            continue

        odds = team_data["odds"]
        implied_prob = team_data["implied_prob"]

        if best_odds is None or odds > best_odds:
            best_book = book
            best_odds = odds
            best_implied_prob = implied_prob

    if best_book is None:
        return None

    return {
        "book": best_book,
        "odds": best_odds,
        "implied_prob": best_implied_prob,
    }


def detect_moneyline_arbitrage(games_by_id):
    """
    Input: games_by_id (dict[str, dict])
    Output: list[dict]
    Find moneyline arbitrage opportunities from normalized game odds data. Build standard opportunity rows when the best home and away prices create an arbitrage.
    """
    opportunities = []

    for game_id, game in games_by_id.items():
        home = _best_price_for_team(game, game["home_team"])
        away = _best_price_for_team(game, game["away_team"])
        arb = detect_two_way_arbitrage(home, away)
        if not arb:
            continue

        opportunity = {
            "game_id": game_id,
            "sport": game.get("sport"),
            "market_type": "h2h",
            "player_name": None,
            "line_value": None,
            "home_team": game["home_team"],
            "away_team": game["away_team"],
            "profit_percent": arb["profit_percent"],
            "over_book": arb["over_book"],
            "under_book": arb["under_book"],
            "over_odds": arb["over_odds"],
            "under_odds": arb["under_odds"],
        }
        opportunities.append(opportunity)

    return opportunities


def _best_prop_side(books_data, side_name):
    """
    Input: books_data (dict[str, dict]), side_name (str)
    Output: dict | None
    Find the best odds for one prop side, usually Over or Under, across sportsbooks. Return `None` if that side is missing everywhere.
    """
    best_book = None
    best_odds = None
    best_implied_prob = None

    for book, sides in books_data.items():
        side_data = sides.get(side_name)
        if not side_data:
            continue

        odds = side_data["odds"]
        implied_prob = side_data["implied_prob"]

        if best_odds is None or odds > best_odds:
            best_book = book
            best_odds = odds
            best_implied_prob = implied_prob

    if best_book is None:
        return None

    return {
        "book": best_book,
        "odds": best_odds,
        "implied_prob": best_implied_prob,
    }


def detect_prop_arbitrage(normalized_props):
    """
    Input: normalized_props (dict[str, dict])
    Output: list[dict]
    Find prop arbitrage opportunities from normalized prop markets for each game. Return standard rows when Over and Under prices create an arbitrage.
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

                opportunity = {
                    "game_id": game_id,
                    "market_type": market_type,
                    "player_name": player_line_data["player"],
                    "line_value": player_line_data["line"],
                    "home_team": None,
                    "away_team": None,
                    "profit_percent": arb["profit_percent"],
                    "over_book": arb["over_book"],
                    "under_book": arb["under_book"],
                    "over_odds": arb["over_odds"],
                    "under_odds": arb["under_odds"],
                }
                opportunities.append(opportunity)

    return opportunities
