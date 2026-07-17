"""Récupère l'historique des vols à LFBH sur N jours via l'API Flightradar24
et le sauvegarde en JSON.

Le plan Explorer souscrit a deux limites distinctes (confirmées côté compte) :
  - Response limit = 10 : chaque appel /api/flight-summary/full retourne au
    plus 10 résultats, quelle que soit la valeur de `limit` demandée.
  - Request rate limit = 20 : au plus 20 requêtes par minute.
Pour ne rien perdre, on découpe en petites tranches et on subdivise
récursivement toute tranche qui revient à exactement 10 résultats (signe
probable de troncature), tout en espaçant les appels pour rester sous la
limite de débit.
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

from fr24_client import api_get

AIRPORT = "LFBH"
OUT_PATH = os.path.join(os.path.dirname(__file__), "history.json")
RESPONSE_CAP = 10  # "Response limit" du plan souscrit
MIN_CHUNK = timedelta(minutes=15)
REQUEST_INTERVAL = 3.5  # secondes entre appels, pour rester sous 20 req/min


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def fetch_chunk(begin, end, retries=5):
    for attempt in range(retries):
        try:
            data = api_get("/api/flight-summary/full", {
                "airports": AIRPORT,
                "flight_datetime_from": iso(begin),
                "flight_datetime_to": iso(end),
                "limit": 500,
            })
            time.sleep(REQUEST_INTERVAL)
            return data.get("data", [])
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 429 and attempt < retries - 1:
                wait = 2 ** attempt * 2
                print(f"    rate limited, attente {wait}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                raise


def fetch_range(begin, end, chunk=timedelta(hours=3)):
    results = []
    t = begin
    while t < end:
        t_end = min(t + chunk, end)
        flights = fetch_chunk(t, t_end)
        print(f"  {iso(t)} -> {iso(t_end)}: {len(flights)} vols", file=sys.stderr)
        if len(flights) >= RESPONSE_CAP and (t_end - t) > MIN_CHUNK:
            # Probable troncature : on retente cette même fenêtre en deux moitiés.
            mid = t + (t_end - t) / 2
            print(f"    -> plafond atteint, subdivision en deux", file=sys.stderr)
            results.extend(fetch_range(t, mid, chunk=(mid - t)))
            results.extend(fetch_range(mid, t_end, chunk=(t_end - mid)))
        else:
            results.extend(flights)
        t = t_end
    return results


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 29
    end = datetime.now(timezone.utc)
    begin = end - timedelta(days=days) + timedelta(minutes=5)

    print(f"Récupération des vols LFBH ({days}j)...", file=sys.stderr)
    flights = fetch_range(begin, end)

    # Déduplique par fr24_id (une tranche subdivisée peut se chevaucher aux bornes).
    by_id = {f["fr24_id"]: f for f in flights}
    flights = list(by_id.values())

    with open(OUT_PATH, "w") as f:
        json.dump({
            "airport": AIRPORT,
            "begin": iso(begin),
            "end": iso(end),
            "flights": flights,
        }, f, indent=2)

    print(f"Sauvegardé: {len(flights)} vols distincts -> {OUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
