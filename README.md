# Placement Tracker and Predictor

A web app for tracking job and internship applications, with a simple
placement-chance predictor built on top of the same profile data.

It was built as a portfolio project that combines a full-stack CRUD app
with a small, reproducible machine learning model, rather than a demo
that only shows one side or the other.

## Features

- Add, edit and delete job and internship applications
- Dashboard stats: total applications, offers, and counts by status
- Filter applications by status: Applied, Shortlisted, Interview, Offer, Rejected
- Placement chance predictor: enter CGPA, internships, projects, DSA score,
  communication score and backlogs, and get a probability with a
  Low / Moderate / Strong band
- The predictor is explicit about its limits: it is an estimate from
  synthetic training data, not a guarantee of placement

## Tech stack

- Frontend: React with Vite, plain CSS, no UI framework
- Backend: Python Flask, SQLite through the standard library `sqlite3`
- Machine learning: scikit-learn Logistic Regression, saved with joblib
- The Vite dev server proxies `/api` requests to the Flask backend

## Project structure

```
placement-tracker-predictor/
  README.md
  .gitignore
  backend/
    app.py               # Flask API, SQLite storage, prediction endpoint
    model.pkl            # Trained model, loaded by app.py
    requirements.txt
    .env.example
  frontend/
    index.html
    package.json
    vite.config.js
    src/
      main.jsx
      App.jsx
      App.css
      api.js
      components/
        ApplicationForm.jsx
        PredictorForm.jsx
        StatsCards.jsx
  ml/
    generate_data.py     # Generates the synthetic training dataset
    placement_data.csv   # 600 synthetic rows
    train.py             # Trains and evaluates the model
    requirements.txt     # scikit-learn and joblib, needed by train.py
    metrics.json         # Test metrics from the last training run
```

## How to run

### Train the model first

The trained model file is generated locally and not committed, so run
this once before starting the backend. Training needs scikit-learn and
joblib, which are listed in `ml/requirements.txt` — install those first
(the data generation script itself needs no extra packages, which is why
it runs even before this step):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r ml/requirements.txt
python ml/generate_data.py
python ml/train.py
```

On Windows, use `.venv\Scripts\activate` instead of
`source .venv/bin/activate`. If you already installed
`backend/requirements.txt` in a virtual environment, that environment
already has scikit-learn and joblib, so you can just run the two
`python ml/...` commands in it instead.

This writes `backend/model.pkl`, which the API loads on startup.

### Backend

From the project root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

The API runs at http://127.0.0.1:5000. It creates `placements.db` in the
`backend/` directory on first run. That file is gitignored.

### Frontend

From the project root, in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The app runs at http://localhost:5173. The Vite proxy forwards `/api`
requests to the backend, so no extra configuration is needed for local
development. A production build can be made with `npm run build`.

## API endpoints

| Method | Endpoint | Purpose |
| ------ | -------- | ------- |
| GET | /api/health | Backend and model status |
| GET | /api/stats | Total, offers, and counts by status |
| GET | /api/applications | List applications, optionally `?status=Interview` |
| POST | /api/applications | Create an application |
| GET | /api/applications/{id} | Get one application |
| PUT | /api/applications/{id} | Update an application |
| DELETE | /api/applications/{id} | Delete an application |
| POST | /api/predict | Placement chance prediction |

Example prediction request:

```bash
curl -X POST http://127.0.0.1:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"cgpa": 9.0, "internships": 2, "projects": 3, "dsa_score": 85, "communication_score": 80, "backlogs": 0}'
```

## How the model was trained

The training data is synthetic, generated with a fixed seed so the run
can be reproduced exactly:

```bash
python ml/generate_data.py
python ml/train.py
```

Details:

- 600 rows, seed 42
- Features: cgpa, internships, projects, dsa_score, communication_score, backlogs
- Model: StandardScaler followed by Logistic Regression (scikit-learn pipeline)
- Split: 80% train / 20% test, stratified, seed 42
- Saved to `backend/model.pkl` by `ml/train.py` (generated locally, not
  committed — see "Train the model first" above)

Results from the last training run (120 held-out test rows):

- Accuracy: 0.8917
- ROC-AUC: 0.7473

Read those two numbers together. The synthetic data is imbalanced
(508 placed, 92 not placed), so accuracy on its own looks better than
the model really is. ROC-AUC is the more useful figure here, and it
shows a useful but far from perfect model, which is expected from six
simple features and synthetic data.

Prediction bands used by the API:

- Below 35%: Low
- 35% to 65%: Moderate
- Above 65%: Strong

## Limitations

- The model was trained on synthetic data, not real placement outcomes.
  It should not be used to make real decisions about applying or preparing.
- There is no user authentication; it is a single-user local tracker.
- SQLite and the Flask development server are for local use, not production.
- The predictor uses only six features. It does not account for the company,
  role, interview performance, or other factors that matter in practice.

## Future improvements

- User accounts and authentication
- Application deadlines and reminders
- Import from a spreadsheet or job board
- Retraining on real, anonymised placement data with proper consent
- Model calibration and a clearer explanation of which inputs moved a prediction
- Deployment with a production WSGI server instead of the Flask dev server
