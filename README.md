# Developer Productivity MVP

Developer Productivity MVP is a full-stack dashboard for an Individual Contributor (IC). It turns engineering activity data from an Excel workbook into clear metrics, plain-English insights, and practical recommended actions.

The goal is not only to show numbers. The product helps a developer understand what is happening in their workflow and what they can do next.

## Tech Stack

- Frontend: React.js with Vite
- Backend: Python Flask
- Data handling: Pandas + openpyxl
- API server: Gunicorn
- Deployment targets: Render for backend, Vercel for frontend

## Features

- IC dashboard with developer and month filters
- Metric cards for the five assignment metrics:
  - Lead Time for Changes
  - Cycle Time
  - Bug Rate
  - Deployment Frequency
  - PR Throughput
- Simple month-over-month trend view
- Insights section explaining what is happening
- Actions section recommending what to do next
- Source counts for easy metric explanation during an interview
- Flask `/metrics` API powered by the provided Excel workbook

## Project Structure

```text
Developer-Productivity-MVP/
|-- backend/
|   |-- app.py
|   |-- metrics_service.py
|   |-- requirements.txt
|   |-- runtime.txt
|   |-- Procfile
|   `-- data/
|       `-- developer_productivity_data.xlsx
|-- frontend/
|   |-- index.html
|   |-- package.json
|   |-- package-lock.json
|   |-- vercel.json
|   `-- src/
|       |-- main.jsx
|       `-- styles.css
|-- Procfile
|-- render.yaml
|-- .gitignore
`-- README.md
```

## Metric Definitions

The backend follows the assignment definitions exactly:

- Lead Time for Changes = PR opened to successful production deployment
- Cycle Time = issue in progress to done
- Bug Rate = escaped production bugs divided by completed issues
- Deployment Frequency = successful production deployments per month
- PR Throughput = merged pull requests per month

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The Flask API runs at:

```text
http://localhost:5000
```

Useful endpoints:

```text
GET /health
GET /metrics
GET /metrics?developer_id=DEV-002&month=2026-04
```

## Frontend Setup

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

If PowerShell blocks `npm`, use:

```bash
npm.cmd install
npm.cmd run dev
```

The React dashboard runs at:

```text
http://localhost:5173
```

## Demo Explanation

In the demo, start with one IC and one month. Explain that the dashboard is designed to help a developer move from raw metrics to decisions:

1. Select a developer and month.
2. Review the five required productivity metrics.
3. Read the interpretation to understand the likely story.
4. Review recommended next steps.
5. Use the source counts to explain how the numbers were calculated.

Example: for Noah Patel in April 2026, the dashboard shows improved lead time, elevated cycle time, and a non-zero bug rate. The recommended actions focus on reducing review wait time, splitting work smaller, and adding a quality check around the observed bug cause.

## Deployment Notes

Render backend settings:

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: gunicorn --bind 0.0.0.0:$PORT app:app
Health Check Path: /health
```

Vercel frontend settings:

```text
Root Directory: frontend
Build Command: npm run build
Output Directory: dist
Environment Variable: VITE_API_BASE_URL=<Render backend URL>
```

## Interview Notes

The backend reads the Excel workbook with Pandas and calculates metrics from source-like tables:

- Jira issues are used for completed issues and cycle time.
- Pull requests are used for opened and merged PR data.
- CI deployments are used for successful production deployment data.
- Bug reports are used for escaped production bugs.

The MVP is intentionally focused on the IC workflow so it is easy to explain, test, and extend.
