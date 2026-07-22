"""Holt Kurse + News fuer die Watchlist und verschickt einen taeglichen Boersenbericht per Mail.

Wird ueber einen Claude Scheduled Cloud Agent an Boersentagen ausgefuehrt.

Benoetigte Umgebungsvariablen:
  SMTP_HOST   (Default: smtp-mail.outlook.com)
  SMTP_PORT   (Default: 587)
  SMTP_USER   Absender-Login (z.B. joerg_fengler@hotmail.com)
  SMTP_PASS   App-Passwort fuer das Konto
  MAIL_TO     Empfaengeradresse (Default: SMTP_USER)
"""
import json
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import yfinance as yf

BASE_DIR = os.path.dirname(__file__)
WATCHLIST_PATH = os.path.join(BASE_DIR, "watchlist.json")

MAX_NEWS_PER_SYMBOL = 3


def load_watchlist():
    with open(WATCHLIST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_symbol_data(symbol):
    ticker = yf.Ticker(symbol)

    price = change = change_pct = None
    try:
        fi = ticker.fast_info
        price = fi.get("lastPrice") or fi.get("last_price")
        prev_close = fi.get("previousClose") or fi.get("previous_close")
        if price is not None and prev_close:
            change = price - prev_close
            change_pct = (change / prev_close) * 100
    except Exception:
        pass

    if price is None:
        hist = ticker.history(period="5d")
        if len(hist) >= 2:
            price = float(hist["Close"].iloc[-1])
            prev_close = float(hist["Close"].iloc[-2])
            change = price - prev_close
            change_pct = (change / prev_close) * 100

    headlines = []
    try:
        for item in (ticker.news or [])[:MAX_NEWS_PER_SYMBOL]:
            content = item.get("content", item)
            title = content.get("title") or item.get("title")
            link = (content.get("canonicalUrl") or {}).get("url") or item.get("link")
            if title:
                headlines.append({"title": title, "link": link})
    except Exception:
        pass

    return {"price": price, "change": change, "change_pct": change_pct, "headlines": headlines}


def build_email_html(watchlist, results):
    today = datetime.now().strftime("%d.%m.%Y")
    rows = []
    for item in watchlist:
        symbol = item["symbol"]
        name = item.get("name") or symbol
        data = results[symbol]
        if data["price"] is None:
            rows.append(f"<tr><td>{name} ({symbol})</td><td colspan='2'>Keine Kursdaten verfuegbar</td></tr>")
            continue

        color = "#1a7f37" if (data["change"] or 0) >= 0 else "#c0392b"
        sign = "+" if (data["change"] or 0) >= 0 else ""
        rows.append(
            f"<tr><td>{name} ({symbol})</td>"
            f"<td>{data['price']:.2f}</td>"
            f"<td style='color:{color}'>{sign}{data['change']:.2f} ({sign}{data['change_pct']:.2f}%)</td></tr>"
        )
        for h in data["headlines"]:
            link_html = f"<a href='{h['link']}'>{h['title']}</a>" if h.get("link") else h["title"]
            rows.append(f"<tr><td colspan='3' style='padding-left:1.5em;color:#555;font-size:0.9em'>&bull; {link_html}</td></tr>")

    table_rows = "\n".join(rows) if rows else "<tr><td>Watchlist ist leer.</td></tr>"

    return f"""
    <html><body style="font-family:sans-serif">
      <h2>Boersenbericht vom {today}</h2>
      <table cellspacing="0" cellpadding="6" style="border-collapse:collapse;width:100%">
        <thead>
          <tr style="border-bottom:2px solid #333;text-align:left">
            <th>Wertpapier</th><th>Kurs</th><th>Veraenderung</th>
          </tr>
        </thead>
        <tbody>
          {table_rows}
        </tbody>
      </table>
      <p style="color:#888;font-size:0.8em;margin-top:2em">Automatisch erstellt.</p>
    </body></html>
    """


def send_email(html_body, subject):
    smtp_host = os.environ.get("SMTP_HOST", "smtp-mail.outlook.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASS"]
    mail_to = os.environ.get("MAIL_TO", smtp_user)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = mail_to
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [mail_to], msg.as_string())


def main():
    watchlist = load_watchlist()
    if not watchlist:
        print("Watchlist ist leer, kein Versand.")
        return

    results = {item["symbol"]: fetch_symbol_data(item["symbol"]) for item in watchlist}
    html_body = build_email_html(watchlist, results)
    subject = f"Boersenbericht {datetime.now().strftime('%d.%m.%Y')}"
    send_email(html_body, subject)
    print("Bericht versendet.")


if __name__ == "__main__":
    main()
