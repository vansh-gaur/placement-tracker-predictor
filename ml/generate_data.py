"""Generate synthetic training data for the placement predictor.

This data is synthetic, on purpose and labelled as such everywhere
it is used. It models how placement outcomes tend to vary with CGPA,
internships, projects, DSA score, communication score, and backlogs,
so the predictor can be trained and demoed without real student
records. It is not Chandigarh University data, and it is not any
other institution's real placement data.

Run from the project root:
    python ml/generate_data.py
"""

import csv
import os
import random

SEED = 42
ROWS = 5000
OUTPUT = os.path.join(os.path.dirname(__file__), "placement_data.csv")


def sigmoid(x):
    return 1 / (1 + 2.718281828459045 ** (-x))


def main():
    rng = random.Random(SEED)

    rows = []
    for _ in range(ROWS):
        cgpa = round(min(10.0, max(5.0, rng.gauss(7.5, 1.0))), 2)
        internships = rng.choices([0, 1, 2, 3], weights=[35, 35, 20, 10])[0]
        projects = rng.choices([0, 1, 2, 3, 4, 5], weights=[10, 25, 30, 20, 10, 5])[0]
        dsa_score = int(min(100, max(0, rng.gauss(60, 20))))
        communication_score = int(min(100, max(0, rng.gauss(65, 18))))
        backlogs = rng.choices([0, 1, 2], weights=[80, 15, 5])[0]

        logit = (
            -6.0
            + 0.55 * cgpa
            + 0.45 * internships
            + 0.35 * projects
            + 0.03 * dsa_score
            + 0.02 * communication_score
            - 0.80 * backlogs
            + rng.gauss(0, 0.5)
        )
        placed = 1 if rng.random() < sigmoid(logit) else 0

        rows.append(
            {
                "cgpa": cgpa,
                "internships": internships,
                "projects": projects,
                "dsa_score": dsa_score,
                "communication_score": communication_score,
                "backlogs": backlogs,
                "placed": placed,
            }
        )

    with open(OUTPUT, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    placed_count = sum(r["placed"] for r in rows)
    print(f"Wrote {len(rows)} rows to {OUTPUT} ({placed_count} placed, {len(rows) - placed_count} not placed)")


if __name__ == "__main__":
    main()
