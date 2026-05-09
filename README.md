# Developer Productivity MVP

A small full-stack MVP for the intern assignment. It focuses on an Individual Contributor dashboard that helps a developer understand their productivity metrics, interpret what is happening, and choose practical next steps.

## Tech Stack

- Frontend: React.js with Vite
- Backend: Python Flask
- Data: Pandas reads the provided Excel workbook
- Deployment-ready: Render for the Flask API and Vercel for the React app

## Project Structure

```text
developer-productivity-mvp/
├── backend/
│   ├── app.py
│   ├── metrics_service.py
│   ├── requirements.txt
│   └── data/
│       └── developer_productivity_data.xlsx
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vercel.json
│   └── src/
│       ├── main.jsx
│       └── styles.css
├── render.yaml
└── README.md
```

## Metrics Implemented

The app follows the assignment definitions:

- Lead Time for Changes: average time from PR opened to successful production deployment
- Cycle Time: average time from issue in progress to done
- Bug Rate: escaped production bugs divided by completed issues
- Deployment Frequency: successful production deployments per month
- PR Throughput: merged pull requests per month

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The API runs at `http://localhost:5000`.

Useful endpoints:

- `GET /health`
- `GET /metrics`
- `GET /metrics?developer_id=DEV-002&month=2026-04`

## Frontend Setup

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

On Windows PowerShell, use `npm.cmd` if script execution blocks `npm`:

```bash
npm.cmd install
npm.cmd run dev
```

The dashboard runs at the Vite URL, usually `http://localhost:5173`.

## Product Scope

This MVP intentionally starts with one clear user journey:

1. Select an Individual Contributor and month.
2. See the five required productivity metrics.
3. Read a plain-English interpretation of what is happening.
4. Review recommended next steps.
5. Use source counts as a lightweight audit trail for interview explanation.

## Render Deployment

1. Push this repository to GitHub.
2. Create a new Render web service from the repository.
3. Render can use `render.yaml`, or configure manually:
   - Root directory: `backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
4. Copy the deployed API URL.

## Vercel Deployment

1. Import the repository into Vercel.
2. Set the frontend root directory to `frontend`.
3. Add an environment variable:
   - `VITE_API_BASE_URL=<your Render API URL>`
4. Deploy.

## Interview Explanation Notes

The backend reads the Excel workbook with Pandas and calculates metrics from the source-like sheets:

- Jira issues provide completed issue counts and cycle time.
- Pull requests provide opened and merged PR data.
- CI deployments provide successful production deployment data.
- Bug reports provide escaped production bugs.

The frontend keeps the dashboard simple so the reviewer can see product thinking, not just charts: metrics, interpretation, recommended action, and enough audit detail to trust the numbers.
