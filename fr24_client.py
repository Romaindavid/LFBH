"""Client pour l'API Flightradar24 (fr24api.flightradar24.com)."""
import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_ROOT = "https://fr24api.flightradar24.com"
TOKEN = os.environ["FR24_API_TOKEN"]

HEADERS = {
    "Accept": "application/json",
    "Accept-Version": "v1",
    "Authorization": f"Bearer {TOKEN}",
}


def api_get(path, params=None):
    r = requests.get(f"{API_ROOT}{path}", headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json()


def get_usage(period="30d"):
    return api_get("/api/usage", {"period": period})
