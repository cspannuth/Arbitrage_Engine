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

MONEYLINE_ARBITRAGE_TABLE = "moneyline_arbitrage_opportunities"
MONEYLINE_CONFLICT_KEYS = "game_id,over_book,under_book"
PROP_ARBITRAGE_TABLE = "prop_arbitrage_opportunities"
PROP_CONFLICT_KEYS = (
    "game_id,market_type,player_name,line_value,over_book,under_book"
)

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
    Resolve a user-provided sport alias to the canonical Odds API sport key. Return the original value when no alias mapping exists.
    """
    return SPORT_KEY_ALIASES.get(sport_key, sport_key)


def get_prop_markets(sport_key):
    """
    Input: sport_key (str)
    Output: list[str]
    Get configured prop market keys for a sport after alias resolution. Return an empty list when no markets are configured.
    """
    return PROP_MARKETS_BY_SPORT.get(resolve_sport_key(sport_key), [])
