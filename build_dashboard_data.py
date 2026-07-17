"""Agrège history.json en un unique JSON de données prêtes pour le dashboard
(code.html), avec estimation CO2 grossière par type d'appareil.

Toutes les stats sont calculées directement depuis les données FR24 réelles —
aucune valeur n'est inventée. L'estimation CO2 est une approximation basée sur
une table de consommation kérosène/heure par type ICAO (ordres de grandeur
publics ICAO/constructeurs), volontairement présentée comme approximative.
"""
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone

IN_PATH = os.path.join(os.path.dirname(__file__), "history.json")
OUT_PATH = os.path.join(os.path.dirname(__file__), "dashboard_data.json")
COORDS_PATH = os.path.join(os.path.dirname(__file__), "airport_coords.json")

# Consommation kérosène approximative en litres/heure de vol, par type ICAO.
# Ordres de grandeur publics (manuels constructeurs / ICAO Carbon Emissions
# Calculator) — à affiner si une source plus précise est disponible.
FUEL_BURN_LPH = {
    # Commercial (litres/heure en croisière, approximatif toutes phases confondues)
    "A319": 2400, "A320": 2500, "A20N": 2200, "A21N": 2600,
    "B738": 2600, "B38M": 2300,
    # Jets d'affaires
    "E55P": 550, "E50P": 500, "C510": 450, "C25A": 500, "C25B": 550, "C25M": 550,
    "C56X": 750, "C68A": 850, "C550": 600, "C560": 650,
    "FA7X": 1400, "F2TH": 1200, "CL60": 1300, "CL35": 1000, "CRJ2": 1500,
    "PC24": 550,
    # Turbopropulseurs / avions légers rapides
    "PC12": 260, "TBM8": 220, "TBM9": 230, "P180": 350,
    # Aviation légère (essence, bien plus faible)
    "DR40": 35, "C172": 35, "C182": 45, "P28A": 35, "P28R": 40, "P32R": 55,
    "SR22": 45, "SR20": 40, "S22T": 45, "DA40": 30, "DA42": 45, "DA62": 55,
    "M20T": 45, "M20P": 35, "M700": 220,  # M700 = Mooney Acclaim, turbo-essence
    "TB20": 40, "C77R": 35, "R300": 35, "GY80": 30, "C303": 60, "PA34": 60,
    "PA46": 65, "C72R": 35,
    "PNR3": 20, "WT9": 15, "PIVI": 15, "NG5": 15, "FDCT": 18, "PIAT": 12,
    "MCR1": 18, "APM3": 15, "EL10": 15,
    # Hélicoptères
    "EC45": 220, "AS50": 140, "AS65": 240,
    "B350": 320,  # King Air (turboprop bimoteur)
}
CO2_PER_LITER_KEROSENE = 2.52  # kg CO2 / litre kérosène Jet A-1 (ICAO/DEFRA)
CO2_PER_LITER_AVGAS = 2.28     # kg CO2 / litre essence aviation (approx, proche essence auto)
PISTON_TYPES = {
    "DR40", "C172", "C182", "P28A", "P28R", "P32R", "SR22", "SR20", "S22T",
    "DA40", "DA42", "DA62", "M20T", "M20P", "TB20", "C77R", "R300", "GY80",
    "C303", "PA34", "PA46", "C72R", "PNR3", "WT9", "PIVI", "NG5", "FDCT",
    "PIAT", "MCR1", "APM3", "EL10",
}

CATEGORY_LABELS = {
    "Passenger": "commercial",
    "Cargo": "commercial",
    "Business_jets": "jets_prives",
    "General_aviation": "aviation_legere",
    "Military_and_government": "militaire",
    "Helicopters": "helicoptere",
}

AIRPORT_NAMES = {
    "EGKK": "Londres-Gatwick", "EGSS": "Londres-Stansted", "EIDW": "Dublin",
    "LFML": "Marseille", "EBCI": "Charleroi", "LFLL": "Lyon", "LSGG": "Genève",
    "GMMX": "Marrakech", "EICK": "Cork", "LPPR": "Porto", "EGCC": "Manchester",
    "EGGD": "Bristol", "LFPB": "Paris-Le Bourget", "LFPN": "Versailles-Saclay",
    "LFDN": "Rochefort", "LFFK": "Fontenay-le-Comte", "LFOR": "Chartres",
    "LFEA": "Belle-Île-en-Mer", "LFEY": "Île d'Yeu", "LFRI": "La Roche-sur-Yon",
    "LFCL": "Toulouse-Lasbordes", "LFOU": "Cholet", "EGJJ": "Jersey",
    "LFBN": "Niort", "LFRD": "Saint-Brieuc", "LFRC": "Cognac",
    "LFBD": "Bordeaux", "LFRS": "Saint-Nazaire", "EGJB": "Guernesey",
    "LFOH": "Le Havre", "LFOZ": "Orléans", "LFQQ": "Lille", "LFCY": "Royan",
    "LFBU": "Angoulême", "LFOT": "Tours", "LFRQ": "Quimper", "LFBS": "Biscarrosse",
    "LFLM": "Mâcon", "LFRO": "Lannion", "LFBL": "Limoges", "LFLX": "Châteauroux",
    "LFQG": "Nevers", "LFRF": "Granville", "LFRE": "La Baule", "LFRB": "Brest",
    "LFBZ": "Biarritz", "LFMV": "Vichy", "LIML": "Milan", "GMAD": "Madère",
    "LEPA": "Palma de Majorque", "LIBR": "Brač", "LSZH": "Zurich",
    "LGPZ": "Skiathos", "LFLY": "Lyon-Bron", "LFTH": "Touraine",
    "LOWL": "Linz", "LFRB": "Brest", "EGLF": "Farnborough", "LFGJ": "Dole",
    "EGBB": "Birmingham", "EGGW": "Luton", "LEXJ": "Jerez", "LEVX": "Vitoria",
    "EGKB": "Londres-Biggin Hill", "LIMC": "Milan-Malpensa", "LFLC": "Clermont-Ferrand",
    "LEIB": "Ibiza", "LFRV": "Rochefort (aéroclub)", "LFKF": "?",
    "EPWA": "Varsovie", "EGHQ": "Newquay", "LFMP": "Marseille-Provence",
    "LFPX": "?", "LSGK": "?",
}


def fmt(dt_str):
    return dt_str.replace("T", " ").replace("Z", "") if dt_str else None


def other_airport(f):
    orig = f.get("orig_icao")
    dest = f.get("dest_icao_actual") or f.get("dest_icao")
    if orig == "LFBH":
        return dest
    return orig


def is_local(f):
    orig = f.get("orig_icao")
    dest = f.get("dest_icao_actual") or f.get("dest_icao")
    has_real_other = (orig and orig != "LFBH") or (dest and dest != "LFBH")
    return (orig == "LFBH" and dest == "LFBH") or not has_real_other


def estimate_co2_kg(f):
    t = f.get("type")
    burn = FUEL_BURN_LPH.get(t)
    hours = (f.get("flight_time") or 0) / 3600
    if not burn or hours <= 0:
        return None
    liters = burn * hours
    factor = CO2_PER_LITER_AVGAS if t in PISTON_TYPES else CO2_PER_LITER_KEROSENE
    return liters * factor


def main():
    with open(IN_PATH) as f:
        raw = json.load(f)
    by_id = {f["fr24_id"]: f for f in raw["flights"]}
    flights = list(by_id.values())

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period_start": raw["begin"],
        "period_end": raw["end"],
        "total_movements": len(flights),
    }

    # --- Répartition par catégorie ---
    by_cat = defaultdict(list)
    for f in flights:
        cat = CATEGORY_LABELS.get(f.get("category"), "autre")
        by_cat[cat].append(f)
    out["categories"] = {
        cat: {
            "count": len(fs),
            "pct": round(100 * len(fs) / len(flights), 1),
            "avg_duration_min": round(
                sum((f.get("flight_time") or 0) for f in fs if f.get("flight_time"))
                / max(1, sum(1 for f in fs if f.get("flight_time"))) / 60
            ),
        }
        for cat, fs in by_cat.items()
    }

    # --- Évolution quotidienne (par jour, par catégorie) ---
    daily = defaultdict(lambda: defaultdict(int))
    for f in flights:
        ts = f.get("datetime_takeoff") or f.get("first_seen")
        if not ts:
            continue
        day = ts[:10]
        cat = CATEGORY_LABELS.get(f.get("category"), "autre")
        daily[day][cat] += 1
    out["daily"] = [
        {"date": day, **counts} for day, counts in sorted(daily.items())
    ]

    # --- Distribution hebdomadaire (jour de semaine) ---
    weekday_counts = Counter()
    for f in flights:
        ts = f.get("datetime_takeoff") or f.get("first_seen")
        if not ts:
            continue
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        weekday_counts[dt.weekday()] += 1
    out["weekday_distribution"] = [weekday_counts.get(i, 0) for i in range(7)]

    # --- Intensité horaire ---
    hourly_counts = Counter()
    for f in flights:
        ts = f.get("datetime_takeoff") or f.get("first_seen")
        if not ts:
            continue
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        hourly_counts[dt.hour] += 1
    out["hourly_distribution"] = [hourly_counts.get(i, 0) for i in range(24)]

    # --- Jets d'affaires : détail mouvement par mouvement ---
    biz = by_cat.get("jets_prives", [])
    biz_sorted = sorted(biz, key=lambda f: f.get("datetime_takeoff") or "")
    out["business_jets"] = [
        {
            "reg": f.get("reg"),
            "type": f.get("type"),
            "operator": f.get("operating_as"),
            "orig": f.get("orig_icao"),
            "orig_name": AIRPORT_NAMES.get(f.get("orig_icao"), f.get("orig_icao")),
            "dest": f.get("dest_icao_actual") or f.get("dest_icao"),
            "dest_name": AIRPORT_NAMES.get(
                f.get("dest_icao_actual") or f.get("dest_icao"),
                f.get("dest_icao_actual") or f.get("dest_icao"),
            ),
            "takeoff": fmt(f.get("datetime_takeoff")),
            "landed": fmt(f.get("datetime_landed")),
        }
        for f in biz_sorted
    ]
    biz_operators = Counter(f.get("operating_as") or "Inconnu" for f in biz)
    out["business_jets_operators"] = biz_operators.most_common()

    # --- Commercial : par route ---
    commercial = by_cat.get("commercial", [])
    routes = Counter()
    for f in commercial:
        other = other_airport(f)
        if other:
            routes[other] += 1
    out["commercial_routes"] = [
        {"code": code, "name": AIRPORT_NAMES.get(code, code), "count": n}
        for code, n in routes.most_common(15)
    ]

    # --- Aviation légère : local vs tourisme ---
    ga = by_cat.get("aviation_legere", [])
    local = [f for f in ga if is_local(f)]
    tourism = [f for f in ga if not is_local(f)]
    out["general_aviation"] = {
        "local": {"count": len(local), "distinct_aircraft": len(set(f.get("reg") for f in local))},
        "tourism": {"count": len(tourism), "distinct_aircraft": len(set(f.get("reg") for f in tourism))},
    }
    tourism_routes = Counter()
    for f in tourism:
        other = other_airport(f)
        if other:
            tourism_routes[other] += 1
    out["general_aviation"]["tourism_routes"] = [
        {"code": code, "name": AIRPORT_NAMES.get(code, code), "count": n}
        for code, n in tourism_routes.most_common(15)
    ]

    # --- Carte : routes par catégorie, avec coordonnées ---
    coords = {}
    if os.path.exists(COORDS_PATH):
        with open(COORDS_PATH) as f:
            coords = json.load(f)

    def route_counter_for(fs):
        c = Counter()
        for f in fs:
            other = other_airport(f)
            if other:
                c[other] += 1
        return c

    map_categories = {
        "commercial": route_counter_for(commercial),
        "jets_prives": route_counter_for(biz),
        "aviation_legere": route_counter_for(tourism),
    }
    map_routes = []
    for cat, counter in map_categories.items():
        for code, n in counter.items():
            c = coords.get(code)
            if not c:
                continue
            map_routes.append({
                "category": cat,
                "code": code,
                "name": AIRPORT_NAMES.get(code, c["name"]),
                "lat": c["lat"],
                "lon": c["lon"],
                "count": n,
            })
    out["map_routes"] = map_routes
    lfbh_coords = coords.get("LFBH")
    out["lfbh_coords"] = lfbh_coords

    # --- CO2 estimé ---
    co2_by_cat = defaultdict(float)
    co2_flights_count = defaultdict(int)
    for f in flights:
        co2 = estimate_co2_kg(f)
        if co2 is None:
            continue
        cat = CATEGORY_LABELS.get(f.get("category"), "autre")
        co2_by_cat[cat] += co2
        co2_flights_count[cat] += 1
    total_co2_kg = sum(co2_by_cat.values())
    out["co2_estimate"] = {
        "total_tonnes": round(total_co2_kg / 1000, 1),
        "flights_with_estimate": sum(co2_flights_count.values()),
        "flights_total": len(flights),
        "by_category_tonnes": {
            cat: round(kg / 1000, 1) for cat, kg in co2_by_cat.items()
        },
        "methodology": (
            "Estimation approximative = consommation kérosène/essence moyenne par "
            "type d'appareil (ICAO) x durée de vol réelle. Ne tient pas compte du "
            "nombre de passagers, du taux de remplissage, ni des conditions météo. "
            f"Calcul possible pour {sum(co2_flights_count.values())}/{len(flights)} vols "
            "(type d'appareil et durée connus)."
        ),
    }

    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"Écrit {OUT_PATH}")
    print(f"  {len(flights)} vols, catégories: { {k: v['count'] for k, v in out['categories'].items()} }")
    print(f"  CO2 estimé: {out['co2_estimate']['total_tonnes']}t sur {out['co2_estimate']['flights_with_estimate']}/{len(flights)} vols")


if __name__ == "__main__":
    main()
