"""Rendu de la carte de partage d'un vol (#flight-card) en JPEG via Playwright.

Réutilise le HTML/CSS/Leaflet de index.html tel quel (window.openFlightModal
est exposée à cet effet) plutôt que de recréer le rendu en Python — la carte
générée reste donc toujours identique à ce que produit le bouton "Voir" du
site.
"""
import http.server
import os
import threading
from contextlib import contextmanager

from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIEWPORT_WIDTH = 1080
VIEWPORT_HEIGHT = 1350


@contextmanager
def _local_server(directory, port=0):
    """Sert `directory` en HTTP local — index.html fait des fetch() relatifs
    (dashboard_data.json, aircraft_photos.json) qui échouent sous file://
    à cause des restrictions CORS des navigateurs."""
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(
        *a, directory=directory, **kw
    )
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield httpd.server_address[1]
    finally:
        httpd.shutdown()
        thread.join(timeout=5)


def render_card(flight: dict, out_path: str) -> str:
    """Rend la carte de partage pour `flight` (une entrée business_jets, avec
    fr24_id/orig_coords/dest_coords/etc.) et l'écrit en JPEG à `out_path`.
    Retourne `out_path`."""
    with _local_server(BASE_DIR) as port:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page(
                    viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT}
                )
                page.goto(f"http://127.0.0.1:{port}/index.html", wait_until="load")

                # Attend que les données (photos + dashboard) soient chargées
                # avant de déclencher l'ouverture de la carte.
                page.wait_for_function(
                    "window.__aircraftPhotos !== undefined && "
                    "typeof window.openFlightModal === 'function'",
                    timeout=15000,
                )

                page.evaluate("(f) => window.openFlightModal(f)", flight)

                # Laisse le temps aux 2x requestAnimationFrame + les deux
                # setTimeout (50ms, 150ms) de openFlightModal de s'exécuter,
                # et aux tuiles Leaflet de charger sur le réseau.
                page.wait_for_timeout(900)
                try:
                    page.wait_for_function(
                        "document.querySelectorAll("
                        "'#flight-modal-map img.leaflet-tile-loaded').length > 0",
                        timeout=4000,
                    )
                except Exception:
                    pass  # best-effort, on capture quand même après le timeout

                os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
                page.locator("#flight-card").screenshot(
                    path=out_path, type="jpeg", quality=90
                )
            finally:
                browser.close()
    return out_path


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) != 3:
        print("Usage: python3 render_flight_card.py <fr24_id> <out.jpg>")
        sys.exit(1)

    fr24_id, out_path = sys.argv[1], sys.argv[2]
    with open(os.path.join(BASE_DIR, "dashboard_data.json")) as f:
        data = json.load(f)
    flight = next(
        (bj for bj in data["business_jets"] if bj.get("fr24_id") == fr24_id), None
    )
    if not flight:
        print(f"Vol {fr24_id} introuvable dans business_jets")
        sys.exit(1)

    render_card(flight, out_path)
    print(f"Carte rendue: {out_path}")
