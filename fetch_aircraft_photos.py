"""Récupère une photo par immatriculation d'appareil via l'API publique
Planespotters, pour les jets d'affaires du dashboard. Résultats mis en cache
dans aircraft_photos.json (jamais écrasé, seulement les nouvelles immat.
sont interrogées).

Respecte les conditions d'usage de l'API : User-Agent descriptif, crédit
photographe et lien vers la page source conservés pour affichage.
"""
import json
import os
import sys
import time

import requests

DATA_PATH = os.path.join(os.path.dirname(__file__), "dashboard_data.json")
OUT_PATH = os.path.join(os.path.dirname(__file__), "aircraft_photos.json")
API_ROOT = "https://api.planespotters.net/pub/photos/reg"
HEADERS = {
    "User-Agent": "LFBH-Dashboard/1.0 (+https://github.com/Romaindavid/LFBH)"
}


def collect_registrations():
    with open(DATA_PATH) as f:
        d = json.load(f)
    regs = {f["reg"] for f in d["business_jets"] if f.get("reg")}
    return sorted(regs)


def main():
    regs = collect_registrations()
    cache = {}
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH) as f:
            cache = json.load(f)

    missing = [r for r in regs if r not in cache]
    if not missing:
        print(f"aircraft_photos.json déjà à jour ({len(cache)} immatriculations).", file=sys.stderr)
        return

    print(f"{len(missing)} nouvelles immatriculations à chercher: {missing}", file=sys.stderr)
    network_errors = 0
    for reg in missing:
        try:
            r = requests.get(f"{API_ROOT}/{reg}", headers=HEADERS, timeout=10)
            r.raise_for_status()
            photos = r.json().get("photos", [])
            if photos:
                p = photos[0]
                cache[reg] = {
                    "thumbnail_large": p["thumbnail_large"]["src"],
                    "link": p["link"],
                    "photographer": p.get("photographer"),
                }
                print(f"  {reg}: trouvé (photo de {p.get('photographer')})", file=sys.stderr)
            else:
                # Vraie réponse "pas de photo" : on met en cache pour ne pas
                # réinterroger l'API à chaque run pour un résultat qui ne
                # changera probablement pas.
                cache[reg] = None
                print(f"  {reg}: aucune photo", file=sys.stderr)
        except requests.RequestException as e:
            # Erreur réseau/API (DNS, timeout, 5xx...) : on NE met PAS en
            # cache, pour que cette immatriculation soit retentée au
            # prochain run plutôt que définitivement marquée "sans photo".
            print(f"  {reg}: erreur, retentera au prochain run ({e})", file=sys.stderr)
            network_errors += 1
            continue
        time.sleep(1.5)  # reste courtois envers l'API publique

        # sauvegarde incrémentale
        with open(OUT_PATH, "w") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)

    found = sum(1 for v in cache.values() if v)
    print(f"Terminé: {found} / {len(cache)} immatriculations avec photo.", file=sys.stderr)
    if network_errors:
        print(f"{network_errors} immatriculations non résolues à cause d'erreurs réseau "
              f"— relancez ce script pour réessayer.", file=sys.stderr)


if __name__ == "__main__":
    main()
