import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path

import requests
from flask import Flask, flash, g, redirect, render_template, request, url_for
from google.oauth2 import service_account
from googleapiclient.discovery import build


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "leads.db"
GOOGLE_SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


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


def utc_timestamp():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


def get_google_sheets_service():
    service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not service_account_json:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON is not configured.")

    service_account_info = json.loads(service_account_json)
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=GOOGLE_SHEETS_SCOPES,
    )
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


def append_lead_to_google_sheets(lead_data, timestamp):
    spreadsheet_id = os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID")
    target_range = os.environ.get("GOOGLE_SHEETS_RANGE")

    if not spreadsheet_id or not target_range:
        raise ValueError("Google Sheets environment variables are not fully configured.")

    values = [[
        timestamp,
        lead_data["full_name"],
        lead_data["company_name"],
        lead_data["email"],
        lead_data["phone"],
        lead_data["industry"],
        lead_data["company_size"],
        lead_data["interest_type"],
        lead_data["biggest_challenge"],
        "landing_page",
        "new",
        "",
    ]]

    service = get_google_sheets_service()
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=target_range,
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": values},
    ).execute()


def get_first_name(full_name):
    return (full_name or "there").split()[0]


def send_resend_email(to_email, subject, text_body):
    resend_api_key = os.environ.get("RESEND_API_KEY")
    from_email = os.environ.get("FROM_EMAIL")

    if not resend_api_key or not from_email:
        raise ValueError("Resend environment variables are not fully configured.")

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {resend_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "text": text_body,
        },
        timeout=15,
    )
    response.raise_for_status()


def send_internal_alert_email(lead_data, timestamp):
    alert_to_email = os.environ.get("ALERT_TO_EMAIL")
    if not alert_to_email:
        raise ValueError("ALERT_TO_EMAIL is not configured.")

    subject = f"New Equipment Intelligence Lead \u2014 {lead_data['company_name']}"
    text_body = "\n".join(
        [
            "A new Equipment Intelligence lead has been submitted.",
            "",
            f"Full Name: {lead_data['full_name']}",
            f"Company Name: {lead_data['company_name']}",
            f"Email: {lead_data['email']}",
            f"Phone: {lead_data['phone']}",
            f"Industry: {lead_data['industry']}",
            f"Company Size: {lead_data['company_size']}",
            f"Interest Type: {lead_data['interest_type']}",
            f"Biggest Challenge: {lead_data['biggest_challenge']}",
            f"Timestamp: {timestamp}",
        ]
    )
    send_resend_email(alert_to_email, subject, text_body)


def send_lead_confirmation_email(lead_data):
    first_name = get_first_name(lead_data["full_name"])
    subject = "Thanks for your interest in Equipment Intelligence"
    text_body = "\n".join(
        [
            f"Hi {first_name},",
            "",
            "Thanks for your interest in Equipment Intelligence.",
            "",
            "We are currently speaking with field-operations businesses to understand where equipment tracking, accountability, and replacement visibility break down the most.",
            "",
            "We have received your request and will keep you updated as the platform develops.",
            "",
            "If your company looks like a strong fit for early access or pilot feedback, we may also reach out directly.",
            "",
            "Regards,",
            "JP Digital",
            "Equipment Intelligence Platform",
        ]
    )
    send_resend_email(lead_data["email"], subject, text_body)


def run_post_submission_integrations(lead_data, timestamp):
    integrations = [
        ("Google Sheets append", append_lead_to_google_sheets, (lead_data, timestamp)),
        ("internal alert email", send_internal_alert_email, (lead_data, timestamp)),
        ("lead confirmation email", send_lead_confirmation_email, (lead_data,)),
    ]

    for integration_name, integration_func, integration_args in integrations:
        try:
            integration_func(*integration_args)
        except Exception:
            logger.exception("Lead submission succeeded, but %s failed.", integration_name)


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

    timestamp = utc_timestamp()

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
            timestamp,
        ),
    )
    db.commit()

    run_post_submission_integrations(form_data, timestamp)

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
