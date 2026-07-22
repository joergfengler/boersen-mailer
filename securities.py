"""WKN-Hilfsfunktionen: Auflösung einer WKN zu einem Yahoo-Finance-Symbol samt Namen.

Nutzt die freie OpenFIGI-API (idType ID_WERTPAPIER = WKN), um alle Handelsplätze
einer Wertpapierkennnummer zu ermitteln - unabhängig vom Sitzland des Emittenten.
Das ist nötig, weil viele an deutschen Börsen gehandelte Wertpapiere (US-Aktien,
irische/luxemburgische ETFs, ...) keine deutsche ISIN haben und sich daher nicht
aus der WKN herleiten lässt.
"""
import requests
import yfinance as yf

OPENFIGI_URL = "https://api.openfigi.com/v3/mapping"

# Bloomberg-Exchange-Codes deutscher Handelsplätze -> Yahoo-Finance-Suffix,
# in Prioritätsreihenfolge (liquidester/gängigster Handelsplatz zuerst).
GERMAN_EXCHANGES = [
    ("GY", "DE"),  # Xetra
    ("GF", "F"),   # Frankfurt (Parkett)
    ("GD", "DU"),  # Düsseldorf
    ("GS", "SG"),  # Stuttgart
    ("GM", "MU"),  # München
    ("GB", "BE"),  # Berlin
    ("GH", "HM"),  # Hamburg
    ("GZ", "HA"),  # Hannover
]


class ResolveError(Exception):
    pass


def _openfigi_candidates(wkn: str) -> list:
    try:
        resp = requests.post(
            OPENFIGI_URL,
            json=[{"idType": "ID_WERTPAPIER", "idValue": wkn}],
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        result = resp.json()[0]
    except Exception as e:
        raise ResolveError(f"Abfrage bei OpenFIGI fehlgeschlagen: {e}") from e

    if "error" in result:
        return []
    return result.get("data", [])


def _fetch_name(symbol: str, fallback: str) -> str:
    try:
        info = yf.Ticker(symbol).info
        name = info.get("longName") or info.get("shortName")
        if name:
            return name
    except Exception:
        pass
    return fallback


def resolve_wkn(wkn: str) -> dict:
    """Ermittelt zu einer WKN das an einem deutschen Handelsplatz gehandelte
    Yahoo-Finance-Symbol samt Namen - unabhängig davon, ob das Wertpapier
    selbst eine deutsche ISIN hat.
    """
    wkn = wkn.strip().upper()
    if not wkn:
        raise ResolveError("WKN darf nicht leer sein.")

    candidates = {c.get("exchCode"): c for c in _openfigi_candidates(wkn)}

    for exch_code, yahoo_suffix in GERMAN_EXCHANGES:
        candidate = candidates.get(exch_code)
        ticker = candidate.get("ticker") if candidate else None
        if not ticker:
            continue

        symbol = ticker.replace("/", "-") + "." + yahoo_suffix
        try:
            price = yf.Ticker(symbol).fast_info.get("lastPrice")
        except Exception:
            price = None
        if price is not None:
            name = _fetch_name(symbol, candidate.get("name") or symbol)
            return {"wkn": wkn, "symbol": symbol, "name": name}

    raise ResolveError(
        f"Keine handelbaren Kursdaten zur WKN {wkn} an einem deutschen Handelsplatz gefunden. "
        "Bitte WKN prüfen."
    )
