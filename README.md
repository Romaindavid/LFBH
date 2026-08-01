# LFBH — Observatoire du trafic aérien

Dashboard public du trafic aérien à l'aéroport de La Rochelle – Île de Ré (LFBH), basé sur les données de l'API officielle [Flightradar24](https://fr24api.flightradar24.com).

**Site en ligne :** https://romaindavid.github.io/LFBH/

## Mise à jour automatique

Un workflow GitHub Actions (`.github/workflows/update.yml`) exécute la mise à jour automatiquement **2 fois par jour** (6h et 18h UTC), commit et push le résultat sans intervention manuelle. Prérequis : le secret `FR24_API_TOKEN` doit être configuré dans Settings → Secrets and variables → Actions du repo. Un lancement manuel est possible depuis l'onglet Actions ("Run workflow").

Le workflow publie aussi automatiquement sur Instagram ([@volsderiches](https://www.instagram.com/volsderiches/)) la carte de partage des vols de jets privés les plus notables (voir "Publication Instagram" ci-dessous) — nécessite les secrets `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_USER_ID` et `ANTHROPIC_API_KEY`. Sans eux, cette étape ne fait rien (le reste du pipeline continue normalement).

## Mettre à jour les données manuellement

```bash
./update.sh
```

Ce script fait tout, dans l'ordre :

1. **`collect_history.py`** — récupère les nouveaux vols depuis la dernière collecte et les cumule dans `history.json` (ne l'écrase jamais). Le plan API souscrit ne permet d'interroger que les 29 derniers jours glissants, mais comme les collectes se cumulent, relancer ce script régulièrement (au moins 1x/mois, idéalement plus souvent) permet de conserver un historique qui dépasse cette fenêtre.
2. **`fetch_airport_coords.py`** — géolocalise les nouveaux aéroports apparus dans `history.json` (base publique [OurAirports](https://davidmegginson.github.io/ourairports-data/), l'API FR24 ne donne pas accès aux coordonnées sur le plan souscrit).
3. **`build_dashboard_data.py`** — reconstruit `dashboard_data.json`, le fichier principal que `index.html` consomme.
4. **`fetch_aircraft_photos.py`** — récupère une photo par immatriculation pour les nouveaux jets d'affaires (API publique [Planespotters](https://www.planespotters.net/photo/api), avec crédit photographe conservé), stockée dans `aircraft_photos.json`.
5. **`post_instagram.py`** (seulement avec `./update.sh --post-instagram`, ou automatiquement en CI) — publie sur Instagram la carte de partage des vols de jets privés les plus polluants non encore publiés, plafonné à 3 posts par 24h glissantes. Voir "Publication Instagram" ci-dessous.

Ensuite, vérifiez le résultat en local puis publiez :

```bash
python3 -m http.server 8000   # puis ouvrir http://localhost:8000/index.html
git add -A && git commit -m "Mise à jour des données" && git push
```

GitHub Pages republie automatiquement `index.html` après le push (quelques minutes).

## Publication Instagram

`post_instagram.py` publie automatiquement sur [@volsderiches](https://www.instagram.com/volsderiches/) la carte de partage (celle du bouton "Voir") des vols de jets privés les plus notables :

1. Sélectionne, parmi les vols atterris pas encore publiés, ceux avec le CO2 estimé le plus élevé — jusqu'à 3 posts par 24h glissantes, tous runs confondus.
2. Rend la carte en JPEG via [Playwright](https://playwright.dev/python/) (Chromium headless), en réutilisant `index.html` tel quel — `window.openFlightModal` est exposée à cet effet.
3. Génère une légende via l'API Claude (dans le style éditorial du compte : un fait marquant + une question rhétorique + `#LFBH #larochelle`), avec un repli sur une légende factuelle simple si l'appel échoue.
4. Commit + push l'image dans `posts/`, attend qu'elle soit accessible publiquement (`raw.githubusercontent.com`, plus rapide à se propager que GitHub Pages), puis appelle l'API Instagram Graph (`graph.instagram.com`) pour publier.
5. Enregistre le vol dans `instagram_posts.json` (jamais republié) une fois la publication confirmée.

Une erreur à n'importe quelle étape (rendu, légende, publication) est loguée et le vol concerné est simplement ignoré ce run-ci — il redevient candidat au run suivant tant qu'il n'apparaît pas dans `instagram_posts.json`. Le script ne fait jamais échouer le pipeline de collecte de données.

Pour tester sans risque de publier réellement :
```bash
python3 post_instagram.py --dry-run   # rend les cartes + légendes, ne commit ni ne publie
```

Configuration requise (compte Instagram professionnel lié, token, etc.) : voir la [documentation Instagram Content Publishing](https://developers.facebook.com/documentation/instagram-platform/instagram-graph-api/reference/ig-user/media). Gratuit côté Meta, aucun abonnement nécessaire.

## Prérequis

- Un token API Flightradar24 valide dans `.env` (voir `.env.example`) — plan payant requis, l'API gratuite/sandbox ne donne que des données factices.
- `pip install -r requirements.txt`
- Pour la publication Instagram uniquement : `playwright install --with-deps chromium`, plus les secrets `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_USER_ID`, `ANTHROPIC_API_KEY` dans `.env`.

## Fichiers

| Fichier | Rôle | Versionné ? |
|---|---|---|
| `fr24_client.py` | Authentification API | oui |
| `collect_history.py` | Collecte cumulative des vols | oui |
| `fetch_airport_coords.py` | Géolocalisation des aéroports | oui |
| `build_dashboard_data.py` | Agrégation + estimation CO2 | oui |
| `fetch_aircraft_photos.py` | Photos des jets d'affaires (Planespotters) | oui |
| `render_flight_card.py` | Rend la carte de partage d'un vol en JPEG (Playwright) | oui |
| `generate_caption.py` | Génère la légende Instagram d'un vol (API Claude) | oui |
| `post_instagram.py` | Sélectionne et publie les vols sur Instagram | oui |
| `update.sh` | Enchaîne les 5 scripts ci-dessus | oui |
| `index.html` | Le dashboard (statique, servi par GitHub Pages) | oui |
| `history.json` | Vols bruts cumulés | oui — versionné volontairement pour ne jamais perdre l'historique (le plan API ne permet d'interroger que 29 jours glissants). Grossira dans le temps ; si ça devient un problème, migration vers un stockage externe (Supabase ou équivalent) à envisager. |
| `airport_coords.json` | Cache lat/lon des aéroports | oui (évite de re-télécharger le CSV OurAirports à chaque run) |
| `aircraft_photos.json` | Cache photo par immatriculation | oui (évite de re-solliciter l'API Planespotters) |
| `dashboard_data.json` | Données agrégées consommées par `index.html` | oui (nécessaire pour GitHub Pages, qui ne peut pas exécuter Python) |
| `instagram_posts.json` | Vols déjà publiés sur Instagram (dédup + plafond quotidien) | oui — doit persister entre les runs GitHub Actions |
| `posts/` | Cartes JPEG publiées sur Instagram, servies par GitHub Pages | oui |
| `.env` | Tokens API (secrets) | **non** (`.gitignore`) |

## Limites connues

- **CO2 estimé** : ordre de grandeur basé sur une table de consommation kérosène/essence par type d'appareil × durée de vol réelle. Ne tient pas compte du taux de remplissage, de la météo, ni des trajectoires réelles. Voir la méthodologie affichée sur le dashboard.
- **Plafond API** : le plan souscrit limite chaque appel à 10 résultats et 20 requêtes/minute — `collect_history.py` gère ça en découpant récursivement les fenêtres temporelles, mais une collecte initiale complète (29 jours) prend 30-45 minutes.
- **Aéroports non trouvés** : si un code ICAO n'existe pas dans OurAirports (rare — bases militaires, terrains très obscurs), il s'affichera sous son code brut plutôt qu'un nom de ville.
- **Photos d'appareils** : dépendent de la couverture de Planespotters, environ 90-95% des immatriculations observées ont une photo. Les photos restent la propriété de leur photographe (crédit + lien affichés sur chaque carte).
