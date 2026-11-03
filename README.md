# Placement Tracker and Predictor

A web app for tracking job and internship applications, with a
placement-chance predictor trained on clearly labelled synthetic data.

It combines a full-stack CRUD app with user accounts, a reproducible
machine learning model, and a production-style deployment setup,
rather than a demo that only shows one side or the other.

## Features

- User accounts: register and log in; each account only sees its own
  applications (passwords are bcrypt-hashed, API access is by JWT)
- Add, edit and delete job and internship applications
- Dashboard stats: total applications, offers, and counts by status
- Filter applications by status: Applied, Shortlisted, Interview, Offer, Rejected
- Placement chance predictor: enter CGPA, internships, projects,
  DSA score, communication score, and backlogs, and get a
  probability with a Low / Moderate / Strong band
- The predictor is explicit about its limits: it is an estimate from
  synthetic training data, not a guarantee of placement, and it does
  not use company, role, or interview performance — those are not in
  the training data

## Tech stack

- Frontend: React with Vite, plain CSS, no UI framework
- Backend: Python Flask, SQLAlchemy (SQLite locally, PostgreSQL via
  DATABASE_URL in production), JWT auth, bcrypt
- Machine learning: scikit-learn pipeline (preprocessing + model),
  saved with joblib
- Deployment: Docker and docker-compose (backend, frontend, Postgres),
  gunicorn for the backend in production instead of the Flask dev server
- The Vite dev server proxies `/api` requests to the Flask backend

## Project structure

```
placement-tracker-predictor/
  README.md
  .gitignore
  docker-compose.yml
  backend/
    app.py                 # Flask API, auth, applications, prediction
    config.py              # Environment configuration, no hardcoded secrets
    models.py              # SQLAlchemy User and Application models
    auth.py                # bcrypt passwords, JWT tokens
    requirements.txt
    .env.example
    Dockerfile
    tests/test_api.py      # pytest: health, auth, CRUD, predict
  frontend/
    index.html
    package.json
    vite.config.js
    nginx.conf
    Dockerfile
    src/
      main.jsx
      App.jsx
      App.css
      api.js               # API calls, JWT from localStorage
      components/
        AuthPage.jsx
        ApplicationForm.jsx
        PredictorForm.jsx
        StatsCards.jsx
  ml/
    generate_data.py       # Generates the synthetic training data (seed 42)
    placement_data.csv     # Synthetic training data, generated locally
    train.py               # Trains and evaluates the model, saves metrics
    requirements.txt
    metrics.json           # Metrics from the last training run
```

## How to run locally

### 1. Train the model first

The trained model file is generated locally and not committed, so run
this once before starting the backend:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r ml/requirements.txt
python ml/generate_data.py
python ml/train.py
```

On Windows, use `.venv\Scripts\activate` instead of
`source .venv/bin/activate`.

This writes `ml/placement_data.csv` (synthetic, seed 42) and then
`backend/model.pkl`, which the API loads on startup.

### 2. Backend

From the project root, in a second terminal (or a new virtual
environment — the backend requirements include everything the API
needs, including the model libraries):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

The API runs at http://127.0.0.1:5000. With no DATABASE_URL set it
uses SQLite (`backend/placements.db`, gitignored). Set JWT_SECRET in
`.env` before using it anywhere other than locally — without it, a
development-only secret is used and a warning is logged.

### 3. Frontend

From the project root, in a third terminal:

```bash
cd frontend
npm install
npm run dev
```

The app runs at http://localhost:5173. The Vite proxy forwards `/api`
requests to the backend, so no extra configuration is needed for local
development. A production build can be made with `npm run build`.
Register an account on the login screen first — applications are
per-user, so the tracker is empty until you add your own.

## How to run with Docker

Docker was not available in the environment where this project was
built, so the Docker files below have not been build-tested here.
They are provided as the production setup to run and verify on a
machine with Docker installed.

```bash
# Generate synthetic data and train first, so backend/model.pkl exists
# for the image build.
python ml/generate_data.py
python ml/train.py
cp backend/.env.example backend/.env
# Set a real JWT_SECRET in backend/.env first.
docker compose up --build
```

The frontend is then at http://localhost:8080, the backend at
http://localhost:5000, and Postgres at localhost:5432. The backend in
the compose file uses the Postgres service via DATABASE_URL.

## Production run

Do not use `python app.py` in production — that is the Flask
development server. Use gunicorn, as in `backend/Dockerfile`:

```bash
gunicorn -w 2 -b 0.0.0.0:$PORT app:app
```

Set, at minimum: `JWT_SECRET` (a long random string),
`DATABASE_URL` (Postgres), and `CORS_ORIGINS` (only your frontend
origin, not `*` — the API only allows origins listed there).

## API endpoints

| Method | Endpoint | Auth | Purpose |
| ------ | -------- | ---- | ------- |
| GET | /api/health | No | Backend and model status |
| POST | /api/auth/register | No | Create an account (password >= 8 chars) |
| POST | /api/auth/login | No | Log in, returns a JWT |
| GET | /api/auth/me | Yes | Current user |
| GET | /api/stats | Yes | Total, offers, and counts by status, for this user |
| GET | /api/applications | Yes | List this user's applications, optionally `?status=Interview` |
| POST | /api/applications | Yes | Create an application |
| GET | /api/applications/{id} | Yes | Get one of this user's applications (404 for others') |
| PUT | /api/applications/{id} | Yes | Update one of this user's applications |
| DELETE | /api/applications/{id} | Yes | Delete one of this user's applications |
| POST | /api/predict | No | Placement chance prediction (no personal data in, estimate out) |

Breaking changes from the original version: application endpoints
now require a JWT and return only the calling user's data (the
predictor endpoint itself is public, as before, but the frontend
sits behind the login screen).

Example prediction request:

```bash
curl -X POST http://127.0.0.1:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"cgpa": 9.0, "internships": 2, "projects": 3, "dsa_score": 85, "communication_score": 80, "backlogs": 0}'
```

## How the model was trained

The training data is synthetic, generated by `ml/generate_data.py`
with a fixed seed so the run can be reproduced exactly:

```bash
python ml/generate_data.py
python ml/train.py
```

Generation process (seed 42, 5000 rows):

- CGPA: clipped Gaussian, mean 7.5, SD 1.0, range 5–10
- Internships: choices [0, 1, 2, 3], weights [35, 35, 20, 10]
- Projects: choices [0, 1, 2, 3, 4, 5], weights [10, 25, 30, 20, 10, 5]
- DSA score: clipped Gaussian, mean 60, SD 20, range 0–100
- Communication score: clipped Gaussian, mean 65, SD 18, range 0–100
- Backlogs: choices [0, 1, 2], weights [80, 15, 5]
- Logit = -6.0 + 0.55*CGPA + 0.45*internships + 0.35*projects
  + 0.03*DSA + 0.02*communication - 0.80*backlogs + Gaussian noise SD 0.5
- Placed = 1 if a random draw is below sigmoid(logit), else 0

Details:

- Features: cgpa, internships, projects, dsa_score,
  communication_score, backlogs
- Model selection: Logistic Regression, Random Forest and
  HistGradientBoosting compared with 5-fold cross-validation on the
  training set, best by ROC-AUC wins
- Split: 80% train / 20% test, stratified, seed 42
- Saved artefact: one sklearn Pipeline (scaling + model) to
  `backend/model.pkl` by `ml/train.py` (generated locally, not
  committed — see "Train the model first" above)

Results from the last training run are in `ml/metrics.json` and are
updated by every retrain — read them there rather than trusting any
number copied here, since they change if the generator or the split
changes.

Read the metrics together: the data is imbalanced (about 85%
placed in the synthetic data), so accuracy on its own looks better
than the model really is — a model predicting "placed" for everyone
would already get about 85%. ROC-AUC is the more useful figure, and
balanced accuracy shows the weak spot: the model is much better at
spotting placed students than not-placed ones. There is also a hard
ceiling here, and it is not a tuning problem: placement is sampled
probabilistically, so a strong profile can still miss out and a
weaker one can still get in. Even a model trained on 50,000 rows
from the same process tops out around ROC-AUC 0.77–0.78 on fresh
data. A higher number would only come from making the data
artificially easy, or from leaking the test set — neither was done.

Prediction bands used by the API:

- Below 35%: Low
- 35% to 65%: Moderate
- Above 65%: Strong

## Tests

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest
python -m pytest tests/ -v
```

Tests use a temporary SQLite database and a tiny test-only fixture
model for the predict endpoint. They never touch the production database
or the training data.

## Limitations

- The model was trained on synthetic data, not on Chandigarh
  University data, and not on this project's users. It should not be
  used to make real decisions about applying or preparing.
- The predictor uses only 6 features. It does not account for
  company, role, interview performance, or other factors that matter
  in practice.
- JWT tokens are stored in localStorage by the frontend, which is
  convenient for a portfolio project but less secure than httpOnly
  cookies for a real production app with sensitive data.
- Docker files have not been build-tested in the environment where
  this project was built (Docker was not available there) — verify
  `docker compose up --build` on a machine with Docker before relying
  on it.

## Future improvements

- Application deadlines and reminders
- Import from a spreadsheet or job board
- httpOnly-cookie auth instead of localStorage tokens
- Model calibration and a clearer explanation of which inputs moved a prediction
- Retraining on real, anonymised placement data with proper consent,
  from a dataset that is not rule-generated
- CI (tests + lint on every push) and hosted deployment
