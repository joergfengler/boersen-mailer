# Börsenmailer

E-Mail mit Kurs, Tagesveränderung und News-Schlagzeilen zu einer selbst gepflegten Watchlist,
ausgelöst manuell per Klick in einer lokalen Web-UI. Zwei Teile:

1. **Lokale Web-UI** (`app.py`) zum Pflegen der Watchlist (`watchlist.json`) — läuft nur auf
   deinem PC. Wertpapiere werden über die **WKN** eingegeben und in zwei Blöcke unterteilt:
   "Wertpapiere im Bestand" und "Watchlist". Die WKN wird über die freie OpenFIGI-API zu
   allen Handelsplätzen aufgelöst und daraus das an einem deutschen Handelsplatz (bevorzugt
   Xetra) gehandelte Yahoo-Finance-Symbol samt Name ermittelt. Das funktioniert für alle an
   deutschen Börsen gehandelten Wertpapiere — auch für ausländische Aktien/ETFs mit
   deutscher WKN, die keine deutsche ISIN haben (z. B. US-Werte).
2. **`send_report.py`** — holt Kurse/News per `yfinance` und verschickt die Mail per SMTP.
   Wird lokal ausgelöst, sofort bei jedem Klick auf "Watchlist committen & pushen" in der
   lokalen UI (nutzt dafür die lokal in `.env` hinterlegten SMTP-Zugangsdaten, siehe Schritt 3).

> **Kein automatischer täglicher Versand.** Ein Versuch, `send_report.py` täglich über einen
> Claude Scheduled Cloud Agent laufen zu lassen, ist an einer Netzwerk-Restriktion der
> Cloud-Sandbox gescheitert: ausgehende SMTP-Verbindungen (Port 587) werden dort blockiert
> (`TimeoutError: [Errno 110] Connection timed out`) — vermutlich eine generelle
> Anti-Spam-Maßnahme des Sandbox-Anbieters, unabhängig von Zugangsdaten oder
> Netzwerk-Einstellungen. Der Bericht wird daher nur noch manuell per Button-Klick versendet.
> Falls du später doch eine automatische, PC-unabhängige Lösung willst, bräuchte es einen
> E-Mail-Versand über eine HTTPS-API (z. B. Resend/SendGrid) statt klassischem SMTP.

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

## 2. Gmail-App-Passwort erstellen

Der Versand läuft über `smtp.gmail.com`. Voraussetzung: 2-Faktor-Authentifizierung ist für
das Gmail-Konto aktiviert.

1. https://myaccount.google.com/apppasswords öffnen, anmelden.
2. App-Passwort erstellen (z. B. Name "Börsenmailer").
3. Das erzeugte 16-stellige Passwort notieren (wird nur einmal angezeigt).

## 3. Mailversand konfigurieren

`.env.example` nach `.env` kopieren und ausfüllen:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<deine-gmail-adresse>
SMTP_PASS=<Gmail-App-Passwort>
MAIL_TO=<empfänger-adresse>
```

Testlauf:

```bash
python send_report.py
```

## 4. Auf GitHub sichern (optional)

Nicht für den Mailversand erforderlich, aber praktisch als Backup/Versionierung der
Watchlist. `.env` wird durch `.gitignore` nie mit hochgeladen — dein Passwort bleibt lokal.

```bash
git init
git add .
git commit -m "Initial commit: Börsenmailer"
git remote add origin https://github.com/<dein-user>/boersen-mailer.git
git branch -M main
git push -u origin main
```

## 5. Watchlist pflegen und Bericht versenden

In der lokalen UI (`python app.py`) Wertpapiere pflegen, dann unten auf
"Watchlist committen & pushen" klicken:

- committet und pusht `watchlist.json` (falls ein Git-Remote eingerichtet ist, siehe Schritt 4),
- verschickt danach sofort einen aktuellen Bericht per Mail (setzt `.env` aus Schritt 3 voraus
  — ohne `.env` wird trotzdem committet/gepusht, nur der Mailversand entfällt mit
  entsprechendem Hinweis).
