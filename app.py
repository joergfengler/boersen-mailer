"""Lokale Web-UI zur Verwaltung der Watchlist (watchlist.json).

Start: python app.py  ->  http://localhost:5000
"""
import json
import os

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)
WATCHLIST_PATH = os.path.join(os.path.dirname(__file__), "watchlist.json")


def load_watchlist():
    with open(WATCHLIST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_watchlist(items):
    with open(WATCHLIST_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


@app.route("/")
def index():
    return render_template("index.html", items=load_watchlist())


@app.route("/add", methods=["POST"])
def add():
    items = load_watchlist()
    symbol = request.form["symbol"].strip().upper()
    name = request.form.get("name", "").strip()
    if symbol and not any(i["symbol"] == symbol for i in items):
        items.append({"symbol": symbol, "name": name})
        save_watchlist(items)
    return redirect(url_for("index"))


@app.route("/edit/<symbol>", methods=["POST"])
def edit(symbol):
    items = load_watchlist()
    new_name = request.form.get("name", "").strip()
    for i in items:
        if i["symbol"] == symbol:
            i["name"] = new_name
    save_watchlist(items)
    return redirect(url_for("index"))


@app.route("/delete/<symbol>", methods=["POST"])
def delete(symbol):
    items = [i for i in load_watchlist() if i["symbol"] != symbol]
    save_watchlist(items)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
