#!/usr/bin/env bash
# Met à jour le dashboard LFBH de bout en bout : collecte les nouveaux vols,
# géolocalise les aéroports manquants, reconstruit dashboard_data.json,
# récupère les photos des nouveaux jets d'affaires.
#
# Usage : ./update.sh [--post-instagram]
#   --post-instagram : publie aussi automatiquement sur Instagram les vols les
#                       plus notables (désactivé par défaut en local pour ne
#                       jamais poster par accident sur le vrai compte).
# Ensuite : vérifier le résultat (ex: python3 -m http.server puis ouvrir
# index.html), puis commit + push manuellement (sauf pour --post-instagram,
# qui commit/push lui-même les cartes publiées).
set -euo pipefail
cd "$(dirname "$0")"

POST_INSTAGRAM=0
for arg in "$@"; do
  case "$arg" in
    --post-instagram) POST_INSTAGRAM=1 ;;
  esac
done

echo "== 1/5 Collecte des nouveaux vols =="
python3 collect_history.py

echo
echo "== 2/5 Géolocalisation des nouveaux aéroports =="
python3 fetch_airport_coords.py

echo
echo "== 3/5 Reconstruction de dashboard_data.json =="
python3 build_dashboard_data.py

echo
echo "== 4/5 Photos des jets d'affaires =="
python3 fetch_aircraft_photos.py

echo
if [ "$POST_INSTAGRAM" -eq 1 ]; then
  echo "== 5/5 Publication Instagram =="
  python3 post_instagram.py
else
  echo "== 5/5 Publication Instagram (ignorée, relancer avec --post-instagram) =="
fi

echo
echo "Terminé. Pour publier :"
echo "  git add -A && git commit -m 'Mise à jour des données' && git push"
