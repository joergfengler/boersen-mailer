"""WKN/ISIN-Hilfsfunktionen: WKN -> ISIN-Berechnung und Auflösung zu einem Yahoo-Finance-Ticker."""
import yfinance as yf


def isin_check_digit(isin11: str) -> int:
    digits = ""
    for ch in isin11:
        if ch.isdigit():
            digits += ch
        else:
            digits += str(10 + (ord(ch.upper()) - ord("A")))

    total = 0
    for i, d in enumerate(reversed([int(c) for c in digits])):
        if i % 2 == 0:
            doubled = d * 2
            total += doubled - 9 if doubled > 9 else doubled
        else:
            total += d
    return (10 - (total % 10)) % 10


def wkn_to_isin(wkn: str, country: str = "DE") -> str:
    nsin = wkn.strip().upper().zfill(9)
    base = country + nsin
    return base + str(isin_check_digit(base))


class ResolveError(Exception):
    pass


def resolve_wkn(wkn: str) -> dict:
    """Ermittelt zu einer WKN das passende Yahoo-Finance-Symbol samt Namen.

    Wandelt die WKN zunächst in eine deutsche ISIN um (DE + WKN + Prüfziffer)
    und sucht darüber bei Yahoo Finance. Funktioniert nur für in Deutschland
    notierte Wertpapiere.
    """
    wkn = wkn.strip().upper()
    if not wkn:
        raise ResolveError("WKN darf nicht leer sein.")

    isin = wkn_to_isin(wkn)
    try:
        search = yf.Search(isin, max_results=5)
        quotes = search.quotes
    except Exception as e:
        raise ResolveError(f"Suche fehlgeschlagen: {e}") from e

    if not quotes:
        raise ResolveError(
            f"Keine Yahoo-Finance-Daten zur WKN {wkn} (ISIN {isin}) gefunden. "
            "Bitte WKN prüfen (funktioniert nur für in Deutschland notierte Wertpapiere)."
        )

    best = quotes[0]
    symbol = best.get("symbol")
    name = best.get("longname") or best.get("shortname") or symbol
    name = " ".join(name.split())  # Yahoo liefert shortname teils mit Füll-Leerzeichen/Artefakten
    return {"wkn": wkn, "isin": isin, "symbol": symbol, "name": name}
