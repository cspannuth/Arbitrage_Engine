import os

from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.environ.get("ODDS_API_KEY")
ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"
ODDS_API_TIMEOUT_SECONDS = 30
ODDS_API_REGION = "us"
ODDS_API_FORMAT = "american"

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

raw_cors_origins = os.environ.get("CORS_ALLOW_ORIGINS", "")
split_cors_origins = raw_cors_origins.split(",")
CORS_ALLOW_ORIGINS = []

for origin in split_cors_origins:
    cleaned_origin = origin.strip()
    if cleaned_origin:
        CORS_ALLOW_ORIGINS.append(cleaned_origin)

MONEYLINE_ARBITRAGE_TABLE = "moneyline_arbitrage_opportunities"
MONEYLINE_CONFLICT_KEYS = "game_id,over_book,under_book"
PROP_ARBITRAGE_TABLE = "prop_arbitrage_opportunities"
PROP_CONFLICT_KEYS = "game_id,market_type,player_name,line_value,over_book,under_book"
SPREAD_ARBITRAGE_TABLE = "spread_arbitrage_opportunities"
SPREAD_CONFLICT_KEYS = "game_id,line_value,home_book,away_book"

SPORT_KEY_ALIASES = {
    "nhl": "icehockey_nhl",
    "nfl": "americanfootball_nfl",
    "soccer": "soccer_usa_mls",
    "nba": "basketball_nba",
    "mlb": "baseball_mlb",
    "ufc": "mma_mixed_martial_arts",
}

PROP_MARKETS_BY_SPORT = {
    "americanfootball_nfl": [
        "player_pass_tds",
        "player_rush_yds",
        "player_rec_yds",
    ],
    "basketball_nba": [
        "player_points",
        "player_rebounds",
        "player_assists",
    ],
}


def resolve_sport_key(sport_key):
    """
    Input: sport_key (str)
    Output: str
    Change a short sport alias into the full Odds API sport key. Return the original value if there is no matching alias.
    """
    return SPORT_KEY_ALIASES.get(sport_key, sport_key)


def get_prop_markets(sport_key):
    """
    Input: sport_key (str)
    Output: list[str]
    Get the configured prop markets for a sport after alias resolution. Return an empty list if the sport has no prop markets set.
    """
    return PROP_MARKETS_BY_SPORT.get(resolve_sport_key(sport_key), [])
