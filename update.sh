#!/usr/bin/env bash
# Met à jour le dashboard LFBH de bout en bout : collecte les nouveaux vols,
# géolocalise les aéroports manquants, reconstruit dashboard_data.json.
#
# Usage : ./update.sh
# Ensuite : vérifier le résultat (ex: python3 -m http.server puis ouvrir
# index.html), puis commit + push manuellement.
set -euo pipefail
cd "$(dirname "$0")"

echo "== 1/3 Collecte des nouveaux vols =="
python3 collect_history.py

echo
echo "== 2/3 Géolocalisation des nouveaux aéroports =="
python3 fetch_airport_coords.py

echo
echo "== 3/3 Reconstruction de dashboard_data.json =="
python3 build_dashboard_data.py

echo
echo "Terminé. Pour publier :"
echo "  git add -A && git commit -m 'Mise à jour des données' && git push"
