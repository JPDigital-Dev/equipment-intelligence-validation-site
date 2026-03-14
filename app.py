import os
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, url_for


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "leads.db"


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            company_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            industry TEXT NOT NULL,
            company_size TEXT NOT NULL,
            interest_type TEXT NOT NULL,
            biggest_challenge TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    db.commit()
    db.close()


@app.before_request
def before_request():
    init_db()


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def sanitize_field(value):
    return " ".join((value or "").split())


def get_form_data():
    return {
        "full_name": sanitize_field(request.form.get("full_name", "")),
        "company_name": sanitize_field(request.form.get("company_name", "")),
        "email": sanitize_field(request.form.get("email", "")),
        "phone": sanitize_field(request.form.get("phone", "")),
        "industry": sanitize_field(request.form.get("industry", "")),
        "company_size": sanitize_field(request.form.get("company_size", "")),
        "interest_type": sanitize_field(request.form.get("interest_type", "")),
        "biggest_challenge": sanitize_field(request.form.get("biggest_challenge", "")),
    }


def validate_form(data):
    required_fields = [
        "full_name",
        "company_name",
        "email",
        "phone",
        "industry",
        "biggest_challenge",
    ]
    errors = {}

    if not any(data.values()):
        errors["form"] = "Please complete the form before submitting."
        return errors

    for field in required_fields:
        if not data.get(field):
            errors[field] = "This field is required."

    if data.get("email") and "@" not in data["email"]:
        errors["email"] = "Please enter a valid email address."

    if data.get("interest_type") not in {
        "Early Access",
        "Pilot Program",
        "Demo Request",
        "Just Keep Me Updated",
    }:
        errors["interest_type"] = "Please select a valid interest type."

    if not data.get("company_size"):
        data["company_size"] = "Not specified"

    return errors


@app.route("/")
def index():
    form_data = {
        "full_name": "",
        "company_name": "",
        "email": "",
        "phone": "",
        "industry": "",
        "company_size": "",
        "interest_type": "",
        "biggest_challenge": "",
    }
    return render_template("index.html", form_data=form_data, errors={})


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/thank-you")
def thank_you():
    return render_template("thank-you.html")


@app.route("/early-access", methods=["POST"])
def early_access():
    form_data = get_form_data()
    errors = validate_form(form_data)

    if errors:
        flash("Please correct the highlighted fields and try again.", "error")
        return render_template("index.html", form_data=form_data, errors=errors), 400

    db = get_db()
    db.execute(
        """
        INSERT INTO leads (
            full_name,
            company_name,
            email,
            phone,
            industry,
            company_size,
            interest_type,
            biggest_challenge,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            form_data["full_name"],
            form_data["company_name"],
            form_data["email"],
            form_data["phone"],
            form_data["industry"],
            form_data["company_size"],
            form_data["interest_type"],
            form_data["biggest_challenge"],
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        ),
    )
    db.commit()

    flash("Thanks. Your request has been received.", "success")
    return redirect(url_for("thank_you"))


@app.route("/admin/leads")
def admin_leads():
    db = get_db()
    leads = db.execute(
        """
        SELECT id, full_name, company_name, email, phone, industry,
               company_size, interest_type, biggest_challenge, created_at
        FROM leads
        ORDER BY id DESC
        """
    ).fetchall()
    # Production note: this route should be protected with authentication.
    return render_template("admin-leads.html", leads=leads, total_leads=len(leads))


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
