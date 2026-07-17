"""Régénère airport_coords.json avec les coordonnées de tous les aéroports
apparaissant dans history.json, via la base publique OurAirports (l'API FR24
ne donne pas accès aux coordonnées sur le plan souscrit — endpoint /full
retourne 403).

Idempotent : ne re-télécharge le CSV OurAirports que si besoin, et ne
recalcule que les codes manquants par rapport au cache existant.
"""
import csv
import json
import os
import sys

import requests

IN_PATH = os.path.join(os.path.dirname(__file__), "history.json")
OUT_PATH = os.path.join(os.path.dirname(__file__), "airport_coords.json")
CSV_URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"
CSV_CACHE = os.path.join(os.path.dirname(__file__), ".airports_ourairports.csv")


def collect_codes():
    with open(IN_PATH) as f:
        d = json.load(f)
    codes = set()
    for f_ in d["flights"]:
        for key in ("orig_icao", "dest_icao_actual", "dest_icao"):
            c = f_.get(key)
            if c:
                codes.add(c)
    codes.add("LFBH")
    return codes


def ensure_csv():
    if not os.path.exists(CSV_CACHE):
        print("Téléchargement de la base OurAirports...", file=sys.stderr)
        r = requests.get(CSV_URL, timeout=30)
        r.raise_for_status()
        with open(CSV_CACHE, "wb") as f:
            f.write(r.content)
    return CSV_CACHE


def main():
    codes = collect_codes()
    cache = {}
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH) as f:
            cache = json.load(f)

    missing = codes - set(cache.keys())
    if not missing:
        print(f"airport_coords.json déjà à jour ({len(cache)} aéroports).", file=sys.stderr)
        return

    print(f"{len(missing)} nouveaux codes à géolocaliser: {sorted(missing)}", file=sys.stderr)
    csv_path = ensure_csv()

    found = {}
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            icao = row.get("icao_code") or row.get("gps_code") or row.get("ident")
            if icao in missing:
                found[icao] = {
                    "lat": float(row["latitude_deg"]),
                    "lon": float(row["longitude_deg"]),
                    "name": row["name"],
                }

    cache.update(found)
    still_missing = missing - set(found.keys())
    if still_missing:
        print(f"Non trouvés dans OurAirports: {sorted(still_missing)}", file=sys.stderr)

    with open(OUT_PATH, "w") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

    print(f"Sauvegardé: {len(cache)} aéroports au total (+{len(found)} nouveaux) -> {OUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
