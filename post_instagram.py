"""Publie automatiquement sur Instagram (@volsderiches) la carte de partage
des vols de jets privés les plus notables (CO2 le plus élevé), plafonné à
3 posts par 24h glissantes.

Séquence par vol sélectionné : rendre la carte (render_flight_card.py),
générer la légende (generate_caption.py), committer+pousser l'image,
attendre qu'elle soit accessible publiquement (raw.githubusercontent.com),
appeler l'API Instagram Graph, puis enregistrer l'état dans
instagram_posts.json.

Ne fait jamais échouer le job CI : toute erreur est loguée, le script sort
en code 0 quoi qu'il arrive (sauf secret manquant en argument --post-instagram
explicite, cas de config invalide).
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

from generate_caption import generate_caption
from render_flight_card import render_card

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_PATH = os.path.join(BASE_DIR, "dashboard_data.json")
POSTS_STATE_PATH = os.path.join(BASE_DIR, "instagram_posts.json")
POSTS_DIR = os.path.join(BASE_DIR, "posts")

DAILY_CAP = 3
GITHUB_REPO = "Romaindavid/LFBH"
GITHUB_BRANCH = "main"

GRAPH_API_VERSION = "v21.0"
GRAPH_API_ROOT = "https://graph.instagram.com"


def _load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def _save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _run(cmd, **kwargs):
    return subprocess.run(cmd, check=True, cwd=BASE_DIR, **kwargs)


def _git_commit_and_push(paths, message):
    _run(["git", "add", *paths])
    diff = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=BASE_DIR
    )
    if diff.returncode == 0:
        return False  # rien à committer
    _run(["git", "commit", "-m", message])
    _run(["git", "push"])
    return True


SHORT_FLIGHT_MAX_MIN = 60


def _select_candidates(business_jets, posted_ids, remaining_slots):
    """Alterne l'angle éditorial : le vol le plus polluant en priorité, puis
    (si possible) un vol très court (< 1h — abusif même si peu de CO2), puis
    à nouveau le plus polluant des restants pour les slots suivants."""
    candidates = [
        f
        for f in business_jets
        if f.get("fr24_id")
        and f["fr24_id"] not in posted_ids
        and f.get("orig_coords")
        and f.get("dest_coords")
        and f.get("landed")
        and f.get("co2_kg")
    ]
    by_co2 = sorted(candidates, key=lambda f: f["co2_kg"], reverse=True)

    selected = []
    remaining_pool = list(by_co2)

    def _take_most_polluting():
        if remaining_pool:
            selected.append(remaining_pool.pop(0))

    def _take_shortest_flight():
        short_flights = sorted(
            (f for f in remaining_pool if (f.get("duration_min") or 9999) < SHORT_FLIGHT_MAX_MIN),
            key=lambda f: f["duration_min"],
        )
        if short_flights:
            chosen = short_flights[0]
            remaining_pool.remove(chosen)
            selected.append(chosen)
        else:
            _take_most_polluting()

    slot_order = [_take_most_polluting, _take_shortest_flight, _take_most_polluting]
    for i in range(remaining_slots):
        slot_order[i % len(slot_order)]()

    return selected


def _posts_last_24h(posted_entries):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    count = 0
    for entry in posted_entries:
        try:
            posted_at = datetime.fromisoformat(entry["posted_at"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            continue
        if posted_at >= cutoff:
            count += 1
    return count


def _wait_for_public_url(url, attempts=12, delay=5):
    for i in range(attempts):
        try:
            r = requests.head(url, timeout=10, allow_redirects=True)
            if r.status_code == 200:
                return True
        except requests.RequestException:
            pass
        if i < attempts - 1:
            time.sleep(delay)
    return False


def _raise_with_body(resp):
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        try:
            detail = resp.json()
        except ValueError:
            detail = resp.text
        raise requests.HTTPError(f"{e} — réponse: {detail}", response=resp) from None


def _wait_for_container_ready(container_id, access_token, attempts=10, delay=3):
    for i in range(attempts):
        r = requests.get(
            f"{GRAPH_API_ROOT}/{GRAPH_API_VERSION}/{container_id}",
            params={"fields": "status_code", "access_token": access_token},
            timeout=15,
        )
        _raise_with_body(r)
        status = r.json().get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError(f"container {container_id} en erreur: {r.json()}")
        if i < attempts - 1:
            time.sleep(delay)
    raise RuntimeError(f"container {container_id} pas prêt après {attempts * delay}s (status={status})")


def _publish_to_instagram(image_url, caption, access_token, ig_user_id):
    media_resp = requests.post(
        f"{GRAPH_API_ROOT}/{GRAPH_API_VERSION}/{ig_user_id}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token,
        },
        timeout=30,
    )
    _raise_with_body(media_resp)
    creation_id = media_resp.json()["id"]

    _wait_for_container_ready(creation_id, access_token)

    publish_resp = requests.post(
        f"{GRAPH_API_ROOT}/{GRAPH_API_VERSION}/{ig_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": access_token},
        timeout=30,
    )
    _raise_with_body(publish_resp)
    return publish_resp.json()["id"]


def run(dry_run: bool = False) -> None:
    access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
    ig_user_id = os.environ.get("INSTAGRAM_USER_ID")
    if not dry_run and (not access_token or not ig_user_id):
        print("post_instagram: INSTAGRAM_ACCESS_TOKEN / INSTAGRAM_USER_ID absents, rien à faire.")
        return

    dashboard = _load_json(DASHBOARD_PATH, {"business_jets": []})
    state = _load_json(POSTS_STATE_PATH, {"posted": []})
    posted_ids = {e["fr24_id"] for e in state["posted"]}

    remaining = DAILY_CAP - _posts_last_24h(state["posted"])
    if remaining <= 0:
        print(f"post_instagram: plafond quotidien ({DAILY_CAP}/24h) atteint, rien à poster.")
        return

    candidates = _select_candidates(dashboard["business_jets"], posted_ids, remaining)
    if not candidates:
        print("post_instagram: aucun vol éligible à poster.")
        return

    os.makedirs(POSTS_DIR, exist_ok=True)

    for flight in candidates:
        fr24_id = flight["fr24_id"]
        image_path = os.path.join(POSTS_DIR, f"{fr24_id}.jpg")
        rel_image_path = f"posts/{fr24_id}.jpg"

        print(f"post_instagram: traitement du vol {fr24_id} ({flight.get('reg')})")

        try:
            render_card(flight, image_path)
        except Exception as e:
            print(f"  échec du rendu de la carte: {e}, on passe au vol suivant")
            continue

        try:
            caption = generate_caption(flight)
        except Exception as e:
            print(f"  échec de la génération de légende: {e}, on passe au vol suivant")
            continue

        if dry_run:
            print(f"  [dry-run] carte rendue: {image_path}")
            print(f"  [dry-run] légende:\n{caption}")
            continue

        try:
            pushed = _git_commit_and_push(
                [rel_image_path],
                f"Ajoute la carte du vol {flight.get('reg') or fr24_id} pour Instagram",
            )
        except subprocess.CalledProcessError as e:
            print(f"  échec du commit/push de l'image: {e}, on passe au vol suivant")
            continue

        if not pushed:
            print("  rien à committer (image déjà présente), on continue quand même")

        raw_url = (
            f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{rel_image_path}"
        )
        if not _wait_for_public_url(raw_url):
            print(f"  l'image n'est pas devenue accessible publiquement ({raw_url}), on passe au vol suivant")
            continue

        try:
            media_id = _publish_to_instagram(raw_url, caption, access_token, ig_user_id)
        except (requests.RequestException, RuntimeError) as e:
            print(f"  échec de la publication Instagram: {e}, on passe au vol suivant")
            continue

        state["posted"].append(
            {
                "fr24_id": fr24_id,
                "posted_at": datetime.now(timezone.utc).isoformat(),
                "ig_media_id": media_id,
                "image_path": rel_image_path,
                "co2_kg": flight.get("co2_kg"),
            }
        )
        _save_json(POSTS_STATE_PATH, state)
        try:
            _git_commit_and_push(
                ["instagram_posts.json"],
                f"Marque le vol {flight.get('reg') or fr24_id} comme publié sur Instagram",
            )
        except subprocess.CalledProcessError as e:
            print(f"  échec du commit de l'état (le post Instagram a bien eu lieu): {e}")

        print(f"  publié sur Instagram: media_id={media_id}")


def main():
    parser = argparse.ArgumentParser(description="Publie les vols de jets privés sur Instagram")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Rend les cartes et génère les légendes sans committer ni appeler l'API Instagram",
    )
    args = parser.parse_args()

    try:
        run(dry_run=args.dry_run)
    except Exception as e:
        # Ne fait jamais échouer le pipeline CI à cause d'un souci de publication.
        print(f"post_instagram: erreur inattendue, ignorée pour ne pas casser le pipeline: {e}")
        sys.exit(0)


if __name__ == "__main__":
    main()
