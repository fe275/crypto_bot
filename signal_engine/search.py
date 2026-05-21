import requests
from difflib import get_close_matches
from .fa_map import FA_TO_EN
from .normalize_query import normalize_query

CACHE = {}


def search_coins(query):
    query = normalize_query(query)
    query = query.lower().strip()

    # Auto-clean (usdt, perp, 3l, 3s, up, down)
    for suffix in ["usdt", "perp", "3l", "3s", "up", "down"]:
        if query.endswith(suffix):
            query = query.replace(suffix, "")

    if len(query) < 2:
        return "SHORT_QUERY"

    # Cache
    key = ("search", query)
    if key in CACHE:
        return CACHE[key]

    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "per_page": 250, "page": 1}
    data = requests.get(url, params=params).json()

    # Exact / partial match
    results = [
        c for c in data
        if query in c["symbol"].lower() or query in c["name"].lower()
    ]

    # Fuzzy match if empty
    if not results:
        names = [c["name"].lower() for c in data]
        close = get_close_matches(query, names, n=1, cutoff=0.7)
        if close:
            results = [c for c in data if c["name"].lower() == close[0]]

    CACHE[key] = results
    return results
