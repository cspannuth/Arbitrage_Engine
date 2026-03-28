import requests
import time
from requests import HTTPError

from app.config import (
    ODDS_API_BASE_URL,
    ODDS_API_FORMAT,
    ODDS_API_KEY,
    ODDS_API_REGION,
    ODDS_API_TIMEOUT_SECONDS,
    resolve_sport_key,
)


def odds_to_probability(odds):
    """
    Input: odds (int | float)
    Output: float
    Convert American odds into implied probability as a decimal. Handle both positive and negative odds.
    """
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)


def _request(path, markets):
    """
    Input: path (str), markets (list[str])
    Output: dict | list
    Send a request to The Odds API for the given path and markets. Raise an error if the response is not successful, then return the JSON data.
    """
    response = requests.get(
        f"{ODDS_API_BASE_URL}{path}",
        params={
            "apiKey": ODDS_API_KEY,
            "regions": ODDS_API_REGION,
            "markets": ",".join(markets),
            "oddsFormat": ODDS_API_FORMAT,
        },
        timeout=ODDS_API_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def _request_with_429_retry(path, markets, max_retries=3):
    """
    Input: path (str), markets (list[str]), max_retries (int)
    Output: dict | list
    Request Odds API data and retry if the API returns HTTP 429. Use `Retry-After` when it is available, otherwise wait longer after each retry.
    """
    attempt = 0
    while True:
        try:
            return _request(path, markets)
        except HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code != 429 or attempt >= max_retries:
                raise

            retry_after_header = exc.response.headers.get("Retry-After")
            try:
                wait_seconds = float(retry_after_header) if retry_after_header else 0
            except ValueError:
                wait_seconds = 0

            if wait_seconds <= 0:
                wait_seconds = 2 ** attempt

            time.sleep(wait_seconds)
            attempt += 1


def fetch_upcoming_games(sport_key):
    """
    Input: sport_key (str)
    Output: list[dict]
    Fetch upcoming games for a sport using the moneyline market (`h2h`). Resolve aliases first so shorthand sport keys still work.
    """
    sport = resolve_sport_key(sport_key)
    return _request(f"/sports/{sport}/odds", ["h2h"])


def fetch_event_props(sport_key, event_id, markets):
    """
    Input: sport_key (str), event_id (str), markets (list[str])
    Output: tuple[dict, int]
    Fetch prop odds for one event with 429 retry handling. Return an empty payload and one request error if the fetch still fails.
    """
    if not markets:
        return {}, 0

    sport = resolve_sport_key(sport_key)
    path = f"/sports/{sport}/events/{event_id}/odds"
    try:
        return _request_with_429_retry(path, markets), 0
    except HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else "unknown"
        print(
            f"Skipping props for event {event_id} after request failure. Status: {status_code}."
        )
        return {}, 1


def fetch_upcoming_spreads(sport_key):
    """
    Input: sport_key (str)
    Output: list[dict]
    Fetch upcoming games for a sport using the spread market.
    """
    sport = resolve_sport_key(sport_key)
    return _request(f"/sports/{sport}/odds", ["spreads"])


def normalize_spread_odds(raw_games, sport_key=None):
    """
    Input: raw_games (list[dict])
    Output: dict[str, dict]
    Normalize raw spread data into a structure grouped by game ID and line value.
    Keep home and away side prices separate so only matching lines are compared.
    """
    normalized = {}
    resolved_sport = resolve_sport_key(sport_key) if sport_key else None

    for game in raw_games:
        game_id = game["id"]
        game_data = {
            "game_id": game_id,
            "sport": game.get("sport_key") or resolved_sport,
            "home_team": game["home_team"],
            "away_team": game["away_team"],
            "commence_time": game.get("commence_time"),
            "lines": {},
        }

        for bookmaker in game.get("bookmakers", []):
            book_name = bookmaker.get("title", bookmaker.get("key"))
            if not book_name:
                continue

            selected_market = None
            for market in bookmaker.get("markets", []):
                market_key = market.get("key")
                if market_key == "spreads":
                    selected_market = market
                    break

            if selected_market is None:
                continue

            for outcome in selected_market.get("outcomes", []):
                team = outcome.get("name")
                point = outcome.get("point")
                odds = outcome.get("price")
                if team is None or point is None or odds is None:
                    continue

                if team == game["home_team"]:
                    side_name = "home"
                elif team == game["away_team"]:
                    side_name = "away"
                else:
                    continue

                line_value = abs(point)
                if line_value not in game_data["lines"]:
                    game_data["lines"][line_value] = {"home": {}, "away": {}}

                game_data["lines"][line_value][side_name][book_name] = {
                    "odds": odds,
                    "implied_prob": odds_to_probability(odds),
                    "point": point,
                }

        normalized[game_id] = game_data

    return normalized


def normalize_moneyline_odds(raw_games, sport_key=None):
    """
    Input: raw_games (list[dict])
    Output: dict[str, dict]
    Normalize raw moneyline data into a structure grouped by game ID and sportsbook.
    """
    normalized = {}
    resolved_sport = resolve_sport_key(sport_key) if sport_key else None

    for game in raw_games:
        game_id = game["id"]
        game_data = {
            "game_id": game_id,
            "sport": game.get("sport_key") or resolved_sport,
            "home_team": game["home_team"],
            "away_team": game["away_team"],
            "commence_time": game.get("commence_time"),
            "books": {},
        }

        for bookmaker in game.get("bookmakers", []):
            book_name = bookmaker.get("title", bookmaker.get("key"))
            if not book_name:
                continue

            selected_market = None
            for market in bookmaker.get("markets", []):
                market_key = market.get("key")
                if market_key == "h2h":
                    selected_market = market
                    break

            if selected_market is None:
                continue

            teams = {}
            for outcome in selected_market.get("outcomes", []):
                team = outcome.get("name")
                odds = outcome.get("price")
                if team is None or odds is None:
                    continue

                teams[team] = {
                    "odds": odds,
                    "implied_prob": odds_to_probability(odds),
                }

            if teams:
                game_data["books"][book_name] = teams

        normalized[game_id] = game_data

    return normalized


def normalize_prop_odds(game_id, raw_event_odds):
    """
    Input: game_id (str), raw_event_odds (dict)
    Output: dict[str, dict]
    Normalize raw prop data into game, market, and player-line groups. Store Over and Under odds with implied probabilities for arbitrage checks.
    """
    normalized = {game_id: {}}

    for bookmaker in raw_event_odds.get("bookmakers", []):
        book_name = bookmaker.get("title", bookmaker.get("key"))
        if not book_name:
            continue

        for market in bookmaker.get("markets", []):
            market_type = market.get("key")
            if not market_type:
                continue

            if market_type not in normalized[game_id]:
                normalized[game_id][market_type] = {}

            market_bucket = normalized[game_id][market_type]

            for outcome in market.get("outcomes", []):
                side = outcome.get("name")
                player = outcome.get("description")
                line = outcome.get("point")
                odds = outcome.get("price")

                if side not in {"Over", "Under"}:
                    continue
                if player is None or line is None or odds is None:
                    continue

                player_line_key = f"{player}|{line}"
                if player_line_key not in market_bucket:
                    market_bucket[player_line_key] = {
                        "player": player,
                        "line": line,
                        "books": {},
                    }

                player_line_entry = market_bucket[player_line_key]

                if book_name not in player_line_entry["books"]:
                    player_line_entry["books"][book_name] = {}

                book_entry = player_line_entry["books"][book_name]
                book_entry[side] = {
                    "odds": odds,
                    "implied_prob": odds_to_probability(odds),
                }

    return normalized
