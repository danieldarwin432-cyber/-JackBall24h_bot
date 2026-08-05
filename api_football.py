"""
Thin wrapper around the API-Football v3 API (api-sports.io).

Get a free key at https://www.api-football.com/ (100 requests/day on the free tier).
Set it as the API_FOOTBALL_KEY environment variable.
"""

import os
import requests

BASE_URL = "https://v3.football.api-sports.io"


def _headers() -> dict:
    api_key = os.environ["API_FOOTBALL_KEY"]
    return {"x-apisports-key": api_key}


def get_fixtures_by_date(date: str, league: int | None = None, season: int | None = None) -> list[dict]:
    """
    date: 'YYYY-MM-DD'
    league: optional API-Football league id (e.g. 39 = Premier League)
    season: optional year, e.g. 2025. Required by the API if league is set.
    """
    params = {"date": date}
    if league:
        params["league"] = league
        params["season"] = season or int(date[:4])

    resp = requests.get(f"{BASE_URL}/fixtures", headers=_headers(), params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("response", [])


def get_prediction(fixture_id: int) -> dict | None:
    resp = requests.get(
        f"{BASE_URL}/predictions",
        headers=_headers(),
        params={"fixture": fixture_id},
        timeout=15,
    )
    resp.raise_for_status()
    results = resp.json().get("response", [])
    return results[0] if results else None


# A few common league ids, handy for /today <league_key>
LEAGUES = {
    "epl": 39,       # Premier League
    "laliga": 140,   # La Liga
    "seriea": 135,   # Serie A
    "bundesliga": 78,
    "ligue1": 61,
    "ucl": 2,        # Champions League
      }
