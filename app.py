"""Lokale Web-UI zur Verwaltung der Watchlist (watchlist.json).

Start: python app.py  ->  http://localhost:5000
"""
import json
import os

from flask import Flask, flash, redirect, render_template, request, url_for

from securities import ResolveError, resolve_wkn

app = Flask(__name__)
app.secret_key = "boersen-mailer-local-dev"  # nur lokal genutzt, kein Internetzugriff
WATCHLIST_PATH = os.path.join(os.path.dirname(__file__), "watchlist.json")

CATEGORIES = ("bestand", "watchlist")


def load_watchlist():
    with open(WATCHLIST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_watchlist(items):
    with open(WATCHLIST_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


@app.route("/")
def index():
    items = load_watchlist()
    bestand = [i for i in items if i.get("category") == "bestand"]
    watchlist = [i for i in items if i.get("category") != "bestand"]
    return render_template("index.html", bestand=bestand, watchlist=watchlist)


@app.route("/add", methods=["POST"])
def add():
    wkn = request.form["wkn"].strip().upper()
    category = request.form.get("category", "watchlist")
    if category not in CATEGORIES:
        category = "watchlist"

    items = load_watchlist()
    if any(i["wkn"] == wkn for i in items):
        flash(f"WKN {wkn} ist bereits in der Liste.")
        return redirect(url_for("index"))

    try:
        resolved = resolve_wkn(wkn)
    except ResolveError as e:
        flash(str(e))
        return redirect(url_for("index"))

    name = request.form.get("name", "").strip() or resolved["name"]
    items.append({
        "wkn": resolved["wkn"],
        "isin": resolved["isin"],
        "symbol": resolved["symbol"],
        "name": name,
        "category": category,
    })
    save_watchlist(items)
    flash(f"{name} ({resolved['symbol']}) hinzugefügt.")
    return redirect(url_for("index"))


@app.route("/edit/<wkn>", methods=["POST"])
def edit(wkn):
    items = load_watchlist()
    new_name = request.form.get("name", "").strip()
    new_category = request.form.get("category", "watchlist")
    if new_category not in CATEGORIES:
        new_category = "watchlist"
    for i in items:
        if i["wkn"] == wkn:
            if new_name:
                i["name"] = new_name
            i["category"] = new_category
    save_watchlist(items)
    return redirect(url_for("index"))


@app.route("/delete/<wkn>", methods=["POST"])
def delete(wkn):
    items = [i for i in load_watchlist() if i["wkn"] != wkn]
    save_watchlist(items)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
