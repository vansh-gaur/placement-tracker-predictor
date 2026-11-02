"""Placement Tracker backend.

Flask + SQLite (stdlib sqlite3). Serves the application tracker API and
the placement-chance predictor, which loads the scikit-learn model saved
by ml/train.py (backend/model.pkl).

Run from the backend/ directory:
    pip install -r requirements.txt
    python app.py
"""

import os
import sqlite3

import joblib
from flask import Flask, g, jsonify, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "placements.db")
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")

STATUSES = ["Applied", "Shortlisted", "Interview", "Offer", "Rejected"]
TYPES = ["Job", "Internship"]
PREDICT_FEATURES = [
    "cgpa",
    "internships",
    "projects",
    "dsa_score",
    "communication_score",
    "backlogs",
]

app = Flask(__name__)
_model = None


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'Job',
            status TEXT NOT NULL DEFAULT 'Applied',
            applied_date TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT ''
        )
        """
    )
    db.commit()


@app.after_request
def add_cors_headers(response):
    # The Vite dev server runs on a different port, so allow it to call the API.
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response


def row_to_dict(row):
    return dict(row) if row is not None else None


def validate_application(data, partial=False):
    errors = []
    for field in ("company", "role"):
        if not partial or field in data:
            if not str(data.get(field, "")).strip():
                errors.append(f"{field} is required")
    if "status" in data and data["status"] not in STATUSES:
        errors.append(f"status must be one of: {', '.join(STATUSES)}")
    if "type" in data and data["type"] not in TYPES:
        errors.append(f"type must be one of: {', '.join(TYPES)}")
    return errors


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "model_loaded": os.path.exists(MODEL_PATH)})


@app.route("/api/stats")
def stats():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    by_status = {
        status: db.execute(
            "SELECT COUNT(*) FROM applications WHERE status = ?", (status,)
        ).fetchone()[0]
        for status in STATUSES
    }
    offers = by_status["Offer"]
    return jsonify({"total": total, "by_status": by_status, "offers": offers})


@app.route("/api/applications", methods=["GET", "POST", "OPTIONS"])
def applications():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    db = get_db()
    if request.method == "GET":
        status = request.args.get("status", "")
        if status and status not in STATUSES:
            return jsonify({"error": "invalid status filter"}), 400
        if status:
            rows = db.execute(
                "SELECT * FROM applications WHERE status = ? ORDER BY id DESC",
                (status,),
            ).fetchall()
        else:
            rows = db.execute("SELECT * FROM applications ORDER BY id DESC").fetchall()
        return jsonify([row_to_dict(row) for row in rows])

    data = request.get_json(silent=True) or {}
    errors = validate_application(data)
    if errors:
        return jsonify({"errors": errors}), 400
    cursor = db.execute(
        "INSERT INTO applications (company, role, type, status, applied_date, notes)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (
            data["company"].strip(),
            data["role"].strip(),
            data.get("type", "Job"),
            data.get("status", "Applied"),
            data.get("applied_date", ""),
            data.get("notes", ""),
        ),
    )
    db.commit()
    row = db.execute("SELECT * FROM applications WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify(row_to_dict(row)), 201


@app.route("/api/applications/<int:application_id>", methods=["GET", "PUT", "DELETE", "OPTIONS"])
def single_application(application_id):
    if request.method == "OPTIONS":
        return jsonify({}), 200

    db = get_db()
    row = db.execute("SELECT * FROM applications WHERE id = ?", (application_id,)).fetchone()
    if row is None:
        return jsonify({"error": "application not found"}), 404

    if request.method == "GET":
        return jsonify(row_to_dict(row))

    if request.method == "DELETE":
        db.execute("DELETE FROM applications WHERE id = ?", (application_id,))
        db.commit()
        return jsonify({"deleted": application_id})

    data = request.get_json(silent=True) or {}
    errors = validate_application(data, partial=True)
    if errors:
        return jsonify({"errors": errors}), 400
    updated = {
        "company": data.get("company", row["company"]),
        "role": data.get("role", row["role"]),
        "type": data.get("type", row["type"]),
        "status": data.get("status", row["status"]),
        "applied_date": data.get("applied_date", row["applied_date"]),
        "notes": data.get("notes", row["notes"]),
    }
    db.execute(
        "UPDATE applications SET company=?, role=?, type=?, status=?,"
        " applied_date=?, notes=? WHERE id=?",
        (*updated.values(), application_id),
    )
    db.commit()
    row = db.execute("SELECT * FROM applications WHERE id = ?", (application_id,)).fetchone()
    return jsonify(row_to_dict(row))


def load_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            return None
        _model = joblib.load(MODEL_PATH)
    return _model


def prediction_band(probability):
    if probability < 0.35:
        return "Low"
    if probability < 0.65:
        return "Moderate"
    return "Strong"


@app.route("/api/predict", methods=["POST", "OPTIONS"])
def predict():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    model = load_model()
    if model is None:
        return jsonify({"error": "model not trained yet. Run ml/train.py first."}), 503

    data = request.get_json(silent=True) or {}
    missing = [name for name in PREDICT_FEATURES if name not in data]
    if missing:
        return jsonify({"error": f"missing fields: {', '.join(missing)}"}), 400
    try:
        features = [float(data[name]) for name in PREDICT_FEATURES]
    except (TypeError, ValueError):
        return jsonify({"error": "all prediction fields must be numbers"}), 400

    probability = float(model.predict_proba([features])[0][1])
    return jsonify(
        {
            "probability": round(probability, 4),
            "percentage": round(probability * 100, 1),
            "band": prediction_band(probability),
            "note": (
                "Estimate from a model trained on synthetic data. "
                "It is not a guarantee of placement."
            ),
        }
    )


if __name__ == "__main__":
    with app.app_context():
        init_db()
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True)
