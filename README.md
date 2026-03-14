# Equipment Intelligence Validation Site

This project is a Flask-based market-validation website for an upcoming SaaS concept focused on turning receipts and invoices into trackable equipment records for field operations businesses.

The goal of the site is to validate demand, capture qualified leads, and start early-access, demo, and pilot-program conversations with operations-heavy companies.

## What The Site Is For

The concept is positioned as **Equipment Intelligence for Field Operations**.

The website is designed to help validate whether target businesses care about solving problems such as:

- duplicate equipment purchases
- missing responsibility chains
- poor asset visibility
- unclear failure and replacement reasons
- lack of supplier and lifespan intelligence over time

This is not the full SaaS platform yet. It is a premium lead-capture and concept-validation site.

## Folder Structure

```text
equipment-intelligence-validation-site/
|-- app.py
|-- requirements.txt
|-- README.md
|-- .gitignore
|-- leads.db
|-- templates/
|   |-- index.html
|   |-- privacy.html
|   |-- thank-you.html
|   `-- admin-leads.html
`-- static/
    |-- style.css
    |-- main.js
    `-- images/
        |-- dashboard-mockup.svg
        |-- timeline-mockup.svg
        |-- scanner-mockup.svg
        `-- accountability-mockup.svg
```

`leads.db` is created automatically the first time the app runs.

## Local Setup

1. Make sure Python 3.10+ is installed.
2. Open a terminal in the project folder.
3. Create and activate a virtual environment.

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

## How To Run Flask Locally

```bash
python app.py
```

The app will run on:

- `http://127.0.0.1:5000`
- `http://localhost:5000`

The Flask service binds using:

- host: `0.0.0.0`
- port: `os.environ.get("PORT", 5000)`

## Lead Storage

Lead submissions are stored locally in SQLite inside `leads.db`.

The `leads` table includes:

- `id`
- `full_name`
- `company_name`
- `email`
- `phone`
- `industry`
- `company_size`
- `interest_type`
- `biggest_challenge`
- `created_at`

SQLite is fine for validation and early market testing, but should later be replaced with a production-grade managed database for scale, backup, and access control.

## Lead Automation

Successful lead submissions follow this sequence:

1. Save to SQLite
2. Append to Google Sheets
3. Send an internal alert email
4. Send a confirmation email to the lead
5. Redirect to `/thank-you`

SQLite remains the primary action. If Google Sheets or email fails, the submission still succeeds and the errors are logged server-side.

### Required Environment Variables

- `SECRET_KEY`
- `GOOGLE_SHEETS_SPREADSHEET_ID`
- `GOOGLE_SHEETS_RANGE`
- `GOOGLE_SERVICE_ACCOUNT_JSON`
- `RESEND_API_KEY`
- `ALERT_TO_EMAIL`
- `FROM_EMAIL`

### Google Sheets Setup

1. Create a Google Sheet for lead capture.
2. Add a worksheet and decide which append range you want to use, for example `Leads!A:L`.
3. Add these columns in order:

```text
timestamp
full_name
company_name
email
phone
industry
company_size
interest_type
biggest_challenge
source
status
notes
```

4. Create a Google Cloud service account with access to the Google Sheets API.
5. Download the service account JSON key.
6. Store the full JSON contents in `GOOGLE_SERVICE_ACCOUNT_JSON`.
7. Share the Google Sheet with the service account email address so it can append rows.

### Email Setup With Resend

The app uses Resend to send:

- an internal notification to `ALERT_TO_EMAIL`
- an automatic confirmation email to the lead

Make sure:

- `RESEND_API_KEY` is set
- `FROM_EMAIL` uses a domain or sender identity verified in Resend
- `ALERT_TO_EMAIL` points to the inbox that should receive lead alerts

## Admin Leads View

The internal leads view is available at:

```text
/admin/leads
```

Example:

```text
http://localhost:5000/admin/leads
```

This route intentionally has no authentication for validation-stage convenience. In production, it should be protected with proper authentication and authorization.

## How To Upload To GitHub

1. Create a new repository on GitHub.
2. In the project folder, initialize git:

```bash
git init
git add .
git commit -m "Initial validation site"
```

3. Connect the GitHub repository:

```bash
git remote add origin https://github.com/your-username/your-repo-name.git
git branch -M main
git push -u origin main
```

Once the repository is linked, future pushes can trigger automatic deployments on Render.

## Deploying To Render

Render can deploy this app directly from a linked GitHub repository and can auto-deploy on every push to the selected branch.

### Render Settings

- Runtime: `Python`
- Build Command: `pip install -r requirements.txt`
- Start Command: `python app.py`

### Render Deployment Steps

1. Push this project to GitHub.
2. Log in to Render.
3. Create a new Web Service.
4. Connect your GitHub repository.
5. Select the repository containing this project.
6. Use the settings below:

```text
Runtime: Python
Build Command: pip install -r requirements.txt
Start Command: python app.py
```

7. Add the required environment variables in the Render dashboard.
8. Deploy the service.

Render can auto-deploy from a linked GitHub repository on future pushes.

## Notes

- This project is designed as a serious validation website for a future SaaS platform.
- The frontend uses HTML, CSS, and vanilla JavaScript.
- The backend uses Flask and SQLite.
- The site includes a lead form, thank-you flow, privacy page, and internal leads dashboard.
- External integrations are intentionally non-blocking so lead capture remains reliable.
