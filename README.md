# Project PRAN Streamlit App

Project PRAN is a Google Sheets-backed Streamlit application for recording and monitoring teacher-led adolescent noncommunicable disease prevention sessions.

## Sections

- Project Overview
- Teacher Entry Panel
- Admin Monitoring Dashboard

## Setup

1. Create a Google Sheet. The app writes to the first worksheet by default.
2. In Google Cloud, create a service account and download its JSON key.
3. Share the Google Sheet with the service account email address.
4. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
5. Paste your spreadsheet URL and service account credentials into `.streamlit/secrets.toml`.
6. Install dependencies:

```bash
pip install -r requirements.txt
```

7. Run the app:

```bash
streamlit run app.py
```

The app writes teacher submissions directly to Google Sheets through `st-gsheets-connection`; it does not use a local database or local file tracking for submitted data.
