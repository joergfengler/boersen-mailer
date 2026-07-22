# Börsenmailer

Tägliche E-Mail mit Kurs, Tagesveränderung und News-Schlagzeilen zu einer selbst gepflegten
Watchlist. Zwei Teile:

1. **Lokale Web-UI** (`app.py`) zum Pflegen der Watchlist (`watchlist.json`) — läuft nur auf
   deinem PC. Wertpapiere werden über die **WKN** eingegeben und in zwei Blöcke unterteilt:
   "Wertpapiere im Bestand" und "Watchlist". Die WKN wird über die freie OpenFIGI-API zu
   allen Handelsplätzen aufgelöst und daraus das an einem deutschen Handelsplatz (bevorzugt
   Xetra) gehandelte Yahoo-Finance-Symbol samt Name ermittelt. Das funktioniert für alle an
   deutschen Börsen gehandelten Wertpapiere — auch für ausländische Aktien/ETFs mit
   deutscher WKN, die keine deutsche ISIN haben (z. B. US-Werte).
2. **`send_report.py`** — holt Kurse/News per `yfinance` und verschickt die Mail per SMTP.
   Wird auf zwei Wegen ausgelöst:
   - täglich an Börsentagen automatisch durch einen Claude Scheduled Cloud Agent,
   - zusätzlich sofort bei jedem Klick auf "Watchlist committen & pushen" in der lokalen UI
     (nutzt dafür die lokal in `.env` hinterlegten SMTP-Zugangsdaten, siehe Schritt 3).

## 1. Lokal einrichten

```bash
cd boersen-mailer
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Watchlist-UI starten:

```bash
python app.py
```

→ http://localhost:5000 öffnen, Wertpapiere hinzufügen/ändern/löschen.
Als "WKN" die 6-stellige Wertpapierkennnummer eintragen, z. B. `716460` (SAP SE),
`840400` (Allianz SE). Kategorie "Bestand" oder "Watchlist" wählen — Name und
Ticker-Symbol werden automatisch ermittelt.

## 2. Outlook-App-Passwort erstellen

Für den SMTP-Versand über `smtp-mail.outlook.com` reicht das normale Kontopasswort meist nicht
(2FA). Erstelle ein App-Passwort:

1. https://account.microsoft.com/security öffnen, anmelden.
2. "Erweiterte Sicherheitsoptionen" → "App-Kennwort erstellen".
3. Das erzeugte Passwort notieren (wird nur einmal angezeigt).

## 3. Mailversand lokal testen

`.env.example` nach `.env` kopieren und ausfüllen:

```
SMTP_USER=joerg_fengler@hotmail.com
SMTP_PASS=<App-Passwort>
MAIL_TO=joerg_fengler@hotmail.com
```

Testlauf:

```bash
pip install python-dotenv
python -c "from dotenv import load_dotenv; load_dotenv()" 
python send_report.py
```

(Oder die drei Variablen direkt im Terminal setzen, bevor `python send_report.py` läuft.)

## 4. Auf GitHub veröffentlichen

Der Cloud Agent kann nur auf ein Git-Repository zugreifen, nicht auf deinen lokalen PC.
**Wichtig:** `.env` wird durch `.gitignore` nie mit hochgeladen — dein Passwort bleibt lokal.

```bash
git init
git add .
git commit -m "Initial commit: Börsenmailer"
```

Danach auf https://github.com/new ein (am besten privates) Repository anlegen und pushen:

```bash
git remote add origin https://github.com/<dein-user>/boersen-mailer.git
git branch -M main
git push -u origin main
```

## 5. Geheimnisse für den Cloud Agent hinterlegen

Der Cloud Agent liest `SMTP_USER` / `SMTP_PASS` / `MAIL_TO` als Umgebungsvariablen. Diese müssen
in der von der Routine verwendeten **Environment**-Konfiguration unter
https://claude.ai/code (Environments) hinterlegt werden — **nicht** im Repo.

## 6. Watchlist pflegen

Nach jeder Änderung über die lokale UI unten auf "Watchlist committen & pushen" klicken —
das führt `git add`/`commit`/`push` für `watchlist.json` automatisch aus (setzt einen
funktionierenden `git push` mit hinterlegten Zugangsdaten voraus, siehe Schritt 4) und
verschickt danach sofort einen aktuellen Bericht per Mail (setzt eine lokale `.env` mit
SMTP-Zugangsdaten voraus, siehe Schritt 3 — ohne `.env` wird trotzdem committet/gepusht,
nur der Mailversand entfällt mit entsprechendem Hinweis).

Der nächste Lauf des Cloud Agents zieht dann automatisch den aktuellen Stand.

## 7. Scheduled Cloud Agent einrichten

In Claude Code: `/schedule` aufrufen und eine Routine erstellen, die

- das Repo `https://github.com/<dein-user>/boersen-mailer` auscheckt,
- werktags (Mo–Fr) um 08:00 Uhr Europe/Berlin (06:00 UTC) läuft,
- den Prompt bekommt: *"Führe `pip install -r requirements.txt` und anschließend
  `python send_report.py` aus."*
