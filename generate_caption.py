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

Angles disponibles (choisis-en un ou deux max par légende, jamais plus) :
- Durée du vol (surtout si très courte, moins d'une heure — souligne alors que c'est \
à peine plus long qu'un trajet en voiture ou en train, et que ce serait facilement \
évitable).
- Quantité de CO2 émise, avec éventuellement une comparaison au budget carbone \
individuel annuel pour rester sous 1,5°C (~2t/an/personne selon les études GIEC/Shift \
Project — utilise cet ordre de grandeur, mais NE RÉPÈTE JAMAIS la même formulation \
d'une légende à l'autre. Varie activement la tournure, par exemple parmi :
  * "soit X fois le budget carbone annuel d'une personne pour rester sous 1,5°"
  * "l'équivalent de ce qu'une personne devrait émettre en une année pour rester dans \
un monde à 1,5°"
  * "presque X années de budget carbone individuel"
  * "de quoi vider le compteur CO2 annuel d'une personne en un seul vol"
  * une formulation différente inventée par toi, tant qu'elle reste factuelle et \
dans le même esprit
  Ne réutilise pas deux fois de suite la même structure de phrase.)
- L'opérateur/la compagnie de location de jets.
- Le nombre de passagers maximum transportable par l'appareil (donnée \
"Capacité passagers" fournie) — surtout percutant en contraste avec le CO2 émis ou \
avec un vol commercial équivalent qui transporterait des dizaines/centaines de \
personnes pour un impact comparable par passager.
- Une comparaison avec un trajet en train (uniquement si le trajet est plausible en \
train sur le territoire français/européen — ne l'invente pas si l'origine/destination \
ne s'y prête pas).
- L'heure d'arrivée/de départ, avec une touche d'ironie factuelle si pertinent (ex: \
"ils y seront pour le déj !").

Règles :
- Commence toujours par l'emoji 🛩️.
- Ton factuel, jamais insultant envers des personnes, les chiffres et les questions \
rhétoriques suffisent à faire passer le message.
- Termine TOUJOURS par une phrase interrogative dans l'esprit de "C'est ok pour vous ?" \
suivie des hashtags #LFBH #larochelle (tu peux varier légèrement la phrase \
d'interpellation, mais garde les deux hashtags).
- Reste court : 2 à 4 phrases maximum, pas de pavé.
- N'invente jamais de chiffre ou de fait non fourni dans les données du vol. Si la \
capacité passagers ou l'opérateur ne sont pas fournis, n'en parle simplement pas.
- Ne mentionne jamais @volsderiches (c'est le compte qui publie, se taguer soi-même \
n'a pas de sens).
- Varie sincèrement d'une légende à l'autre : évite de retomber systématiquement sur \
le même angle (CO2 + comparaison 1,5°C) si d'autres données intéressantes sont \
disponibles pour ce vol (opérateur connu, capacité passagers connue, vol très court).

Réponds uniquement avec le texte de la légende, sans guillemets ni commentaire."""


def _fallback_caption(flight: dict) -> str:
    reg = flight.get("reg") or "immatriculation inconnue"
    ftype = flight.get("type") or "appareil"
    orig = flight.get("orig_name") or flight.get("orig") or "origine inconnue"
    dest = flight.get("dest_name") or flight.get("dest") or "destination inconnue"
    duration = flight.get("duration_min")
    co2_kg = flight.get("co2_kg")

    capacity = flight.get("passenger_capacity")

    parts = [f"🛩️ Un {ftype} ({reg}) a rejoint {dest} depuis {orig}."]
    if duration:
        parts.append(f"{duration} min de vol.")
    if capacity:
        parts.append(f"Capacité max : {capacity} passagers.")
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
        f"Capacité passagers: {flight['passenger_capacity']}" if flight.get("passenger_capacity") else "Capacité passagers: inconnue",
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
