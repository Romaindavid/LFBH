# LFBH — Observatoire du trafic aérien

Dashboard public du trafic aérien à l'aéroport de La Rochelle – Île de Ré (LFBH), basé sur les données de l'API officielle [Flightradar24](https://fr24api.flightradar24.com).

**Site en ligne :** https://romaindavid.github.io/LFBH/

## Mettre à jour les données

```bash
./update.sh
```

Ce script fait tout, dans l'ordre :

1. **`collect_history.py`** — récupère les nouveaux vols depuis la dernière collecte et les cumule dans `history.json` (ne l'écrase jamais). Le plan API souscrit ne permet d'interroger que les 29 derniers jours glissants, mais comme les collectes se cumulent, relancer ce script régulièrement (au moins 1x/mois, idéalement plus souvent) permet de conserver un historique qui dépasse cette fenêtre.
2. **`fetch_airport_coords.py`** — géolocalise les nouveaux aéroports apparus dans `history.json` (base publique [OurAirports](https://davidmegginson.github.io/ourairports-data/), l'API FR24 ne donne pas accès aux coordonnées sur le plan souscrit).
3. **`build_dashboard_data.py`** — reconstruit `dashboard_data.json`, le seul fichier que `index.html` consomme réellement.

Ensuite, vérifiez le résultat en local puis publiez :

```bash
python3 -m http.server 8000   # puis ouvrir http://localhost:8000/index.html
git add -A && git commit -m "Mise à jour des données" && git push
```

GitHub Pages republie automatiquement `index.html` après le push (quelques minutes).

## Prérequis

- Un token API Flightradar24 valide dans `.env` (voir `.env.example`) — plan payant requis, l'API gratuite/sandbox ne donne que des données factices.
- `pip install requests python-dotenv`

## Fichiers

| Fichier | Rôle | Versionné ? |
|---|---|---|
| `fr24_client.py` | Authentification API | oui |
| `collect_history.py` | Collecte cumulative des vols | oui |
| `fetch_airport_coords.py` | Géolocalisation des aéroports | oui |
| `build_dashboard_data.py` | Agrégation + estimation CO2 | oui |
| `update.sh` | Enchaîne les 3 scripts ci-dessus | oui |
| `index.html` | Le dashboard (statique, servi par GitHub Pages) | oui |
| `history.json` | Vols bruts cumulés (peut grossir, 1-2 Mo) | **non** (`.gitignore`) |
| `airport_coords.json` | Cache lat/lon des aéroports | oui (évite de re-télécharger le CSV OurAirports à chaque run) |
| `dashboard_data.json` | Données agrégées consommées par `index.html` | oui (nécessaire pour GitHub Pages, qui ne peut pas exécuter Python) |
| `.env` | Token API (secret) | **non** (`.gitignore`) |

## Limites connues

- **CO2 estimé** : ordre de grandeur basé sur une table de consommation kérosène/essence par type d'appareil × durée de vol réelle. Ne tient pas compte du taux de remplissage, de la météo, ni des trajectoires réelles. Voir la méthodologie affichée sur le dashboard.
- **Plafond API** : le plan souscrit limite chaque appel à 10 résultats et 20 requêtes/minute — `collect_history.py` gère ça en découpant récursivement les fenêtres temporelles, mais une collecte initiale complète (29 jours) prend 30-45 minutes.
- **Aéroports non trouvés** : si un code ICAO n'existe pas dans OurAirports (rare — bases militaires, terrains très obscurs), il s'affichera sous son code brut plutôt qu'un nom de ville.
