import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from car_search_core.scrapers.suv_scraper import search_suvs
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, session, url_for
from auth import require_login, validate_passcode
import os

app = Flask(__name__)
app.secret_key = "crx_tracker_secret_key_change_later"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        passcode = request.form.get("passcode")
        if validate_passcode(passcode):
            session["authenticated"] = True
            return redirect(url_for("index"))
        return render_template("login.html", error="Invalid passcode")
    return render_template("login.html")

@app.route("/")
@require_login
def index():
    return render_template("dashboard.html")

@app.route("/crx")
@require_login
def crx():
    return render_template("crx.html")

@app.route("/suv")
@require_login
def suv():
    results = search_suvs(["toyota","honda","nissan"], 2023, 40000, "37401", 250)
    return render_template("suv.html", results=results)

@app.route("/test-suv")
@require_login
def test_suv():
    results = search_suvs(["toyota","honda","nissan"], 2023, 40000, "37401", 250)
    return {"count": len(results), "results": results}

if __name__ == "__main__":
    port = 5000
    app.run(host="127.0.0.1", port=port)
