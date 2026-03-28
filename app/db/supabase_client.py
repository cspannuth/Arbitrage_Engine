from datetime import datetime, timezone

from supabase import create_client

from app.config import (
    MONEYLINE_ARBITRAGE_TABLE,
    MONEYLINE_CONFLICT_KEYS,
    PROP_ARBITRAGE_TABLE,
    PROP_CONFLICT_KEYS,
    SPREAD_ARBITRAGE_TABLE,
    SPREAD_CONFLICT_KEYS,
    SUPABASE_KEY,
    SUPABASE_URL,
)
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def _format_moneyline_opportunity(event):
    """
    Input: event (dict)
    Output: dict
    Change a moneyline arbitrage event into the row shape used by Supabase. Add a UTC timestamp so each upsert shows when the opportunity was found.
    """
    return {
        "game_id": event["game_id"],
        "sport": event.get("sport"),
        "home_team": event.get("home_team"),
        "away_team": event.get("away_team"),
        "over_book": event["over_book"],
        "under_book": event["under_book"],
        "over_odds": event["over_odds"],
        "under_odds": event["under_odds"],
        "profit_percent": event["profit_percent"],
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }


def _format_prop_opportunity(event):
    """
    Input: event (dict)
    Output: dict
    Change a prop arbitrage event into the row shape used by Supabase. Add a UTC timestamp so each upsert shows when the opportunity was found.
    """
    return {
        "game_id": event["game_id"],
        "market_type": event["market_type"],
        "player_name": event.get("player_name"),
        "line_value": event.get("line_value"),
        "sport": event.get("sport"),
        "home_team": event.get("home_team"),
        "away_team": event.get("away_team"),
        "over_book": event["over_book"],
        "under_book": event["under_book"],
        "over_odds": event["over_odds"],
        "under_odds": event["under_odds"],
        "profit_percent": event["profit_percent"],
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }


def _format_spread_opportunity(event):
    """
    Input: event (dict)
    Output: dict
    Change a spread arbitrage event into the row shape used by Supabase. Add a UTC timestamp so each upsert shows when the opportunity was found.
    """
    return {
        "game_id": event["game_id"],
        "sport": event.get("sport"),
        "home_team": event.get("home_team"),
        "away_team": event.get("away_team"),
        "line_value": event.get("line_value"),
        "home_book": event["home_book"],
        "away_book": event["away_book"],
        "home_odds": event["home_odds"],
        "away_odds": event["away_odds"],
        "profit_percent": event["profit_percent"],
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }


def upsert_moneyline_opportunities(opportunities, min_profit_percent=1.99):
    """
    Input: opportunities (list[dict]), min_profit_percent (float)
    Output: list[dict]
    Filter and upsert moneyline opportunities that meet the minimum profit. Return the rows sent to Supabase, or an empty list if nothing qualifies.
    """
    rows = [
        _format_moneyline_opportunity(opp)
        for opp in opportunities
        if opp["profit_percent"] >= min_profit_percent
    ]
    if not rows:
        return []

    (
        supabase.table(MONEYLINE_ARBITRAGE_TABLE)
        .upsert(rows, on_conflict=MONEYLINE_CONFLICT_KEYS)
        .execute()
    )
    return rows


def upsert_spread_opportunities(opportunities, min_profit_percent=1.99):
    """
    Input: opportunities (list[dict]), min_profit_percent (float)
    Output: list[dict]
    Filter and upsert spread opportunities that meet the minimum profit. Return the rows sent to Supabase, or an empty list if nothing qualifies.
    """
    rows = [
        _format_spread_opportunity(opp)
        for opp in opportunities
        if opp["profit_percent"] >= min_profit_percent
    ]
    if not rows:
        return []

    (
        supabase.table(SPREAD_ARBITRAGE_TABLE)
        .upsert(rows, on_conflict=SPREAD_CONFLICT_KEYS)
        .execute()
    )
    return rows


def upsert_prop_opportunities(opportunities, min_profit_percent=1.99):
    """
    Input: opportunities (list[dict]), min_profit_percent (float)
    Output: list[dict]
    Filter and upsert prop opportunities that meet the minimum profit. Return the rows sent to Supabase, or an empty list if nothing qualifies.
    """
    rows = [
        _format_prop_opportunity(opp)
        for opp in opportunities
        if opp["profit_percent"] >= min_profit_percent
    ]

    if not rows:
        return []

    (
        supabase.table(PROP_ARBITRAGE_TABLE)
        .upsert(rows, on_conflict=PROP_CONFLICT_KEYS)
        .execute()
    )
    return rows


def upsert_arbitrage_opportunities(opportunities, min_profit_percent=1.99):
    """
    Input: opportunities (list[dict]), min_profit_percent (float)
    Output: dict[str, list[dict]]
    Split mixed opportunities by market type. Upsert each group with the given threshold and return the result sets.
    """
    moneyline_opps = [opp for opp in opportunities if opp.get("market_type") == "h2h"]
    spread_opps = [opp for opp in opportunities if opp.get("market_type") == "spreads"]
    prop_opps = [
        opp for opp in opportunities
        if opp.get("market_type") not in {"h2h", "spreads"}
    ]

    moneyline_rows = upsert_moneyline_opportunities(moneyline_opps, min_profit_percent=min_profit_percent)
    spread_rows = upsert_spread_opportunities(spread_opps, min_profit_percent=min_profit_percent)
    prop_rows = upsert_prop_opportunities(prop_opps, min_profit_percent=min_profit_percent)
    return {
        "moneyline_rows": moneyline_rows,
        "spread_rows": spread_rows,
        "prop_rows": prop_rows,
    }
