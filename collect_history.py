"""Récupère l'historique des vols à LFBH via l'API Flightradar24 et le
CUMULE dans history.json (ne l'écrase jamais).

Le plan Explorer souscrit a deux limites distinctes (confirmées côté compte) :
  - Response limit = 10 : chaque appel /api/flight-summary/full retourne au
    plus 10 résultats, quelle que soit la valeur de `limit` demandée.
  - Request rate limit = 20 : au plus 20 requêtes par minute.
Pour ne rien perdre, on découpe en petites tranches et on subdivise
récursivement toute tranche qui revient à exactement 10 résultats (signe
probable de troncature), tout en espaçant les appels pour rester sous la
limite de débit.

Le plan limite aussi l'historique interrogeable à 29 jours glissants dans le
passé. Comme history.json cumule les collectes successives, relancer ce
script régulièrement (au moins 1x/mois) permet de construire un historique
qui dépasse cette fenêtre glissante — chaque run ne re-télécharge que ce qui
manque depuis la dernière collecte (ou les 29 jours complets au premier run).
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


def load_existing():
    if not os.path.exists(OUT_PATH):
        return None
    with open(OUT_PATH) as f:
        return json.load(f)


def main():
    max_days = int(sys.argv[1]) if len(sys.argv) > 1 else 29
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    earliest_allowed = now - timedelta(days=max_days) + timedelta(minutes=5)

    existing = load_existing()
    if existing and existing.get("flights"):
        # Ne récupère que ce qui manque depuis la dernière collecte (borné par
        # la limite de 29 jours du plan), pour rester rapide sur les runs
        # réguliers plutôt que de tout retélécharger à chaque fois.
        last_end = datetime.fromisoformat(existing["end"])
        begin = max(earliest_allowed, last_end - timedelta(hours=1))  # petit chevauchement de sécurité
        print(f"Historique existant: {len(existing['flights'])} vols "
              f"({existing['begin']} -> {existing['end']})", file=sys.stderr)
    else:
        existing = {"flights": []}
        begin = earliest_allowed

    end = now
    if begin >= end:
        print("Rien à récupérer, historique déjà à jour.", file=sys.stderr)
        return

    print(f"Récupération des vols LFBH ({iso(begin)} -> {iso(end)})...", file=sys.stderr)
    new_flights = fetch_range(begin, end)

    # Fusionne avec l'existant et déduplique par fr24_id.
    by_id = {f["fr24_id"]: f for f in existing["flights"]}
    for f in new_flights:
        by_id[f["fr24_id"]] = f
    flights = list(by_id.values())

    # La borne "begin" globale ne recule jamais (on ne perd pas l'historique
    # déjà collecté même s'il dépasse la fenêtre de 29 jours du plan).
    overall_begin = min(
        [datetime.fromisoformat(existing.get("begin", iso(begin)))] if existing.get("begin") else [begin]
    )
    overall_begin = min(overall_begin, begin)

    with open(OUT_PATH, "w") as f:
        json.dump({
            "airport": AIRPORT,
            "begin": iso(overall_begin),
            "end": iso(end),
            "flights": flights,
        }, f, indent=2)

    print(f"Sauvegardé: {len(flights)} vols distincts au total "
          f"(+{len(new_flights)} nouveaux) -> {OUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
