"""Classe le trafic LFBH en 4 catégories à partir de history.json (FR24)."""
import json
import os
from collections import defaultdict
from datetime import datetime, timezone

IN_PATH = os.path.join(os.path.dirname(__file__), "history.json")

# Catégories officielles FR24 (champ `category` de flight-summary/full).
# Format observé dans les données réelles: Snake_Case avec underscores.
CATEGORY_LABELS = {
    "Passenger": "Commercial",
    "Cargo": "Commercial (cargo)",
    "Military_and_government": "Militaire / gouvernemental",
    "Business_jets": "Privé d'affaires",
    "General_aviation": "Tourisme privé / école",
    "Helicopters": "Hélicoptère",
    "Lighter_than_air": "Aérostat",
    "Gliders": "Planeur",
    "Drones": "Drone",
    "Ground_vehicles": "Véhicule au sol",
    "Other": "Autre",
    "Non_categorized": "Non catégorisé",
}


def fmt(dt_str):
    if not dt_str:
        return "?"
    return dt_str.replace("T", " ")


def main():
    with open(IN_PATH) as f:
        data = json.load(f)

    flights = data["flights"]
    # Déduplique par fr24_id (un vol peut apparaître dans plusieurs tranches de collecte).
    by_id = {f["fr24_id"]: f for f in flights}
    flights = list(by_id.values())

    print(f"=== LFBH — Trafic {fmt(data['begin'])} -> {fmt(data['end'])} (UTC) ===")
    print(f"Total vols distincts: {len(flights)}\n")

    by_category = defaultdict(list)
    for f in flights:
        cat = CATEGORY_LABELS.get(f.get("category"), f.get("category") or "Inconnu")
        by_category[cat].append(f)

    print("--- Répartition par catégorie officielle FR24 ---")
    for cat, fs in sorted(by_category.items(), key=lambda kv: -len(kv[1])):
        print(f"  {cat}: {len(fs)}")
    print()

    bizjets = by_category.get("Privé d'affaires", [])
    if bizjets:
        print(f"--- {len(bizjets)} vols privés d'affaires — détail ---")
        print(f"{'Immat.':9} {'Modèle':6} {'Opérateur':8} {'Origine':8} {'Destination':11} {'Décollage':17} {'Atterrissage':17}")
        for f in sorted(bizjets, key=lambda x: x.get("datetime_takeoff") or ""):
            print(f"{f.get('reg') or '?':9} {f.get('type') or '?':6} {f.get('operating_as') or '?':8} "
                  f"{f.get('orig_icao') or '?':8} {f.get('dest_icao_actual') or f.get('dest_icao') or '?':11} "
                  f"{fmt(f.get('datetime_takeoff')):17} {fmt(f.get('datetime_landed')):17}")


if __name__ == "__main__":
    main()
