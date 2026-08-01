"""Génère la légende Instagram d'un vol via l'API Claude, dans le style de
@volsderiches (angle éditorial varié — durée, CO2, opérateur, comparaison
train, etc. — signature fixe en fin de légende).

Repose sur ANTHROPIC_API_KEY (.env en local, secret GitHub Actions en CI,
même pattern que FR24_API_TOKEN dans fr24_client.py). En cas d'échec de
l'appel API, retombe sur une légende factuelle générée localement pour ne
jamais bloquer une publication.
"""
import os

from dotenv import load_dotenv

load_dotenv()

SIGNATURE = "C'est ok pour vous ? On continue ? #LFBH #larochelle"

SYSTEM_PROMPT = """Tu écris les légendes Instagram du compte @volsderiches, qui suit \
les vols de jets privés à l'aéroport de La Rochelle - Île de Ré (LFBH) et interpelle \
sur leur impact climatique.

Style à respecter, d'après ces exemples réels déjà publiés :

"🛩️ 1h08 de vol pour rejoindre La Rochelle depuis Valence...
#larochelle Ça va à tout le monde ?"

"🛩️ 21 minutes de vol pour rejoindre l'aérodrome de l'Île d'Yeu.
#larochelle Ça va à tout le monde ?"

"🛩️ Ce matin à 9h29, ce Cessna Citation Mustang ne pouvant transporter que 4 \
passagers est arrivé de Milan...

Il est opéré par GlobeAir, la première compagnie de location de jets en Europe...

2t+ de CO2, c'est l'équivalent de ce qu'une personne devrait émettre en une année \
pour rester dans un monde à 1,5°...

C'est ok pour tout le monde ? #LFBH #larochelle"

"🛩️ À 8h50 a atterri ce Bombardier Challenger 350 opéré par l'agence de location de \
jets privé VistaJet...

Ce Bombardier consomme plus de 1000L à l'heure...

C'est ok pour tout le monde ? #LFBH #larochelle"

"🛩️ Décollage pour Sienne, 2h de vol et 2,25t de CO2...

C'est ok pour tout le monde ? #LFBH #larochelle"

"🛩️ 11h06, décollage pour Nice, ils y seront pour le déj !

1,15t de CO2...

C'est ok pour tout le monde ? On les laisse continuer ? #LFBH #larochelle"

"🛩️ 11 minutes de vol pour aller chercher le passager de ce jet à La Rochelle...

Pouvait il rejoindre Rochefort en train pour éviter ça ?

C'est ok pour vous ? On continue ? #LFBH #larochelle"

Règles :
- Commence toujours par l'emoji 🛩️.
- Choisis UN seul angle par légende parmi : durée du vol, quantité de CO2 (avec \
éventuellement une comparaison parlante comme le budget carbone annuel individuel \
pour rester sous 1,5°C), l'opérateur/la compagnie de location, une comparaison avec \
un trajet en train, le nombre de passagers transportable par l'appareil, l'heure \
d'arrivée/de départ. Ne mélange pas plus de deux angles dans un même texte.
- Ton factuel, jamais insultant envers des personnes, les chiffres et les questions \
rhétoriques suffisent à faire passer le message.
- Termine TOUJOURS par une phrase interrogative dans l'esprit de "C'est ok pour vous ?" \
suivie des hashtags #LFBH #larochelle (tu peux varier légèrement la phrase \
d'interpellation, mais garde les deux hashtags).
- Reste court : 2 à 4 phrases maximum, pas de pavé.
- N'invente jamais de chiffre ou de fait non fourni dans les données du vol.
- Ne mentionne jamais @volsderiches (c'est le compte qui publie, se taguer soi-même \
n'a pas de sens).

Réponds uniquement avec le texte de la légende, sans guillemets ni commentaire."""


def _fallback_caption(flight: dict) -> str:
    reg = flight.get("reg") or "immatriculation inconnue"
    ftype = flight.get("type") or "appareil"
    orig = flight.get("orig_name") or flight.get("orig") or "origine inconnue"
    dest = flight.get("dest_name") or flight.get("dest") or "destination inconnue"
    duration = flight.get("duration_min")
    co2_kg = flight.get("co2_kg")

    parts = [f"🛩️ Un {ftype} ({reg}) a rejoint {dest} depuis {orig}."]
    if duration:
        parts.append(f"{duration} min de vol.")
    if co2_kg:
        co2_str = f"{co2_kg / 1000:.2f}".replace(".", ",")
        parts.append(f"{co2_str} t de CO2 estimées.")
    parts.append(SIGNATURE)
    return " ".join(parts)


def _flight_summary(flight: dict) -> str:
    lines = [
        f"Immatriculation: {flight.get('reg') or 'inconnue'}",
        f"Type d'appareil: {flight.get('type') or 'inconnu'}",
        f"Opérateur: {flight.get('operator') or 'inconnu'}",
        f"Origine: {flight.get('orig_name') or flight.get('orig') or 'inconnue'}",
        f"Destination: {flight.get('dest_name') or flight.get('dest') or 'inconnue'}",
        f"Décollage: {flight.get('takeoff') or 'inconnu'}",
        f"Atterrissage: {flight.get('landed') or 'inconnu'}",
    ]
    if flight.get("duration_min") is not None:
        lines.append(f"Durée de vol: {flight['duration_min']} minutes")
    if flight.get("distance_km") is not None:
        lines.append(f"Distance: {flight['distance_km']} km")
    if flight.get("co2_kg") is not None:
        co2_t = flight["co2_kg"] / 1000
        lines.append(f"CO2 estimé: {co2_t:.2f} tonnes ({flight['co2_kg']} kg)")
    return "\n".join(lines)


def generate_caption(flight: dict) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback_caption(flight)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Données du vol :\n\n"
                        + _flight_summary(flight)
                        + "\n\nÉcris la légende Instagram pour ce vol."
                    ),
                }
            ],
        )
        text = "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
        if not text:
            return _fallback_caption(flight)
        return text
    except Exception as e:
        print(f"generate_caption: échec appel API Claude ({e}), fallback local")
        return _fallback_caption(flight)


if __name__ == "__main__":
    import json
    import sys

    fr24_id = sys.argv[1] if len(sys.argv) > 1 else None
    with open("dashboard_data.json") as f:
        data = json.load(f)
    flight = (
        next((bj for bj in data["business_jets"] if bj.get("fr24_id") == fr24_id), None)
        if fr24_id
        else data["business_jets"][-1]
    )
    if not flight:
        print(f"Vol {fr24_id} introuvable")
        sys.exit(1)
    print(generate_caption(flight))
