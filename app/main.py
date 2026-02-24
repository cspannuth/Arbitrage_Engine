from fastapi import FastAPI, Request, Header
import argparse

from app.config import get_prop_markets
from app.db import supabase_client
from app.db.supabase_client import supabase
from app.services import arbitrage_engine, odds_fetcher

app = FastAPI()


@app.get("/arbitrage/moneyline")
def get_moneyline_arbitrage(min_profit: float = 0.0):
    """
    Input: min_profit (float)
    Output: list[dict]
    Fetch persisted moneyline arbitrage rows from Supabase above a minimum profit threshold. Return rows sorted by descending profit percentage.
    """
    response = (
        supabase
        .table("moneyline_arbitrage_opportunities")
        .select("*")
        .gte("profit_percent", min_profit)
        .order("profit_percent", desc=True)
        .execute()
    )
    return response.data


@app.get("/arbitrage/props")
def get_prop_arbitrage(min_profit: float = 0.0):
    """
    Input: min_profit (float)
    Output: list[dict]
    Fetch persisted prop arbitrage rows from Supabase above a minimum profit threshold. Return rows sorted by descending profit percentage.
    """
    response = (
        supabase
        .table("prop_arbitrage_opportunities")
        .select("*")
        .gte("profit_percent", min_profit)
        .order("profit_percent", desc=True)
        .execute()
    )
    return response.data

def extract_auth_token(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise AssertionError
    token = authorization.split(" ", 1)[1]
    return token

@app.get("/arbitrage/fetch")
async def fetch_from_api(request: Request, authorization: str | None = Header(default=None)):
    """
    Input: sport (str), market (str), key (str)
    Output API Status (str)
    A query based access point to call the arbitrage; Secured by a key value parameter.
    """
    jwt = extract_auth_token(authorization)

    try:
        user_response = supabase.auth.get_user(jwt)
        user = user_response.user
        if not user:
            raise AssertionError
    except Exception:
        raise AssertionError

    body = await request.json()
    sport = body.get("sport")
    market = body.get("market")

    if not sport or not market:
        raise AssertionError
    
    if(market == "prop"):
        fetch_and_process_props(sport)
    elif(market == "moneyline"):
        fetch_and_process_moneyline(sport)
    else:
        fetch_and_process(sport)
    



@app.get("/")
def root():
    """
    Input: None
    Output: dict[str, str]
    Provide a lightweight health-check response for the API root endpoint. This helps confirm that the FastAPI service is running.
    """
    return {"status": "Arbitrage API is Healthy"}


def fetch_moneyline_opportunities(sport_key):
    """
    Input: sport_key (str)
    Output: tuple[list[dict], dict[str, dict]]
    Fetch and normalize upcoming games, then detect moneyline arbitrage opportunities. Return both opportunities and normalized game data for reuse in prop processing.
    """
    raw_games = odds_fetcher.fetch_upcoming_games(sport_key)
    normalized_games = odds_fetcher.normalize_moneyline_odds(raw_games)
    moneyline_opps = arbitrage_engine.detect_moneyline_arbitrage(normalized_games)
    return moneyline_opps, normalized_games


def fetch_prop_opportunities(sport_key, normalized_games=None):
    """
    Input: sport_key (str), normalized_games (dict[str, dict] | None)
    Output: tuple[list[dict], int]
    Fetch and process event-level prop odds for each normalized game in the selected sport. Return detected prop opportunities and a count of request failures.
    """
    if normalized_games is None:
        raw_games = odds_fetcher.fetch_upcoming_games(sport_key)
        normalized_games = odds_fetcher.normalize_moneyline_odds(raw_games)

    opportunities = []
    prop_markets = get_prop_markets(sport_key)
    prop_request_errors = 0

    if prop_markets:
        for game_id in normalized_games:
            raw_props, request_errors = odds_fetcher.fetch_event_props(
                sport_key=sport_key,
                event_id=game_id,
                markets=prop_markets,
            )
            prop_request_errors += request_errors
            if not raw_props:
                continue

            normalized_props = odds_fetcher.normalize_prop_odds(game_id, raw_props)
            prop_opps = arbitrage_engine.detect_prop_arbitrage(normalized_props)
            home_team = normalized_games[game_id]["home_team"]
            away_team = normalized_games[game_id]["away_team"]
            for opp in prop_opps:
                opp["home_team"] = home_team
                opp["away_team"] = away_team
            opportunities.extend(prop_opps)

    return opportunities, prop_request_errors


def fetch_and_process_moneyline(sport_key):
    """
    Input: sport_key (str)
    Output: list[dict]
    Run the moneyline pipeline end-to-end for one sport and upsert qualifying rows. Print a short run summary with counts for visibility.
    """
    moneyline_opps, _ = fetch_moneyline_opportunities(sport_key)
    saved_rows = supabase_client.upsert_moneyline_opportunities(moneyline_opps)
    print(
        f"Moneyline run complete. Opportunities: {len(moneyline_opps)}. Upserted: {len(saved_rows)}."
    )
    return saved_rows


def fetch_and_process_props(sport_key):
    """
    Input: sport_key (str)
    Output: list[dict]
    Run the props pipeline end-to-end for one sport and upsert qualifying rows. Print a short run summary including request error counts.
    """
    _, normalized_games = fetch_moneyline_opportunities(sport_key)
    prop_opps, prop_request_errors = fetch_prop_opportunities(
        sport_key, normalized_games=normalized_games
    )
    saved_rows = supabase_client.upsert_prop_opportunities(prop_opps)
    print(
        f"Props run complete. Opportunities: {len(prop_opps)}. "
        f"Prop request errors: {prop_request_errors}. Upserted: {len(saved_rows)}."
    )
    return saved_rows


def fetch_and_process(sport_key):
    """
    Input: sport_key (str)
    Output: None
    Run both moneyline and prop pipelines for one sport using shared normalized game data. Print a combined summary of detected opportunities, request errors, and upsert counts.
    """
    moneyline_opps, normalized_games = fetch_moneyline_opportunities(sport_key)
    prop_opps, prop_request_errors = fetch_prop_opportunities(sport_key, normalized_games=normalized_games)
    moneyline_rows = supabase_client.upsert_moneyline_opportunities(moneyline_opps)
    prop_rows = supabase_client.upsert_prop_opportunities(prop_opps)
    print(
        f"Processed {len(normalized_games)} games. "
        f"Moneyline arbs: {len(moneyline_opps)}. "
        f"Prop arbs: {len(prop_opps)}. "
        f"Prop request errors: {prop_request_errors}. "
        f"Upserted moneyline: {len(moneyline_rows)}. "
        f"Upserted props: {len(prop_rows)}."
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run arbitrage processing")
    parser.add_argument(
        "-sport",
        default="basketball_nba",
        help="Sport key (example: basketball_nba)",
    )
    parser.add_argument(
        "-mode",
        choices=["all", "moneyline", "props"],
        default="all",
        help="Which pipeline to run",
    )
    args = parser.parse_args()

    if args.mode == "moneyline":
        fetch_and_process_moneyline(args.sport)
    elif args.mode == "props":
        fetch_and_process_props(args.sport)
    else:
        fetch_and_process(args.sport)
