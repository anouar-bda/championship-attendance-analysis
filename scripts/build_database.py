"""
build_database.py
=================
Load the validated matches into SQLite and run the four SQL scripts in
order to build every derived table:

    matches -> team_matches -> team_form / team_ppg -> match_features -> model_data

Output: championship.db  (+ model_data.csv for the modelling step)
"""

import sqlite3
import pandas as pd

DB = "championship.db"

# ------------------------------------------------------------------
# 1. Load the validated matches into the database
# ------------------------------------------------------------------
df = pd.read_csv("championship_matches_validated.csv")

conn = sqlite3.connect(DB)
df.to_sql("matches", conn, if_exists="replace", index=False)
print(f"loaded {len(df)} matches into {DB}")

# ------------------------------------------------------------------
# 2. Run each SQL script in order
# ------------------------------------------------------------------
# Only files 02, 03, 04 create tables. File 01 is validation/inspection
# queries that are documented but not required to build the pipeline.
sql_files = [
    "../sql/02_team_matches.sql",
    "../sql/03_form_and_ppg.sql",
    "../sql/04_model_data.sql",
]

for path in sql_files:
    with open(path, "r", encoding="utf-8") as f:
        script = f.read()
    conn.executescript(script)
    print(f"ran {path}")

conn.commit()

# ------------------------------------------------------------------
# 3. Sanity checks
# ------------------------------------------------------------------
checks = {
    "team_matches rows (expect 1104)":
        "SELECT COUNT(*) FROM team_matches",
    "team_form rows (expect 984)":
        "SELECT COUNT(*) FROM team_form",
    "model_data rows (expect 552)":
        "SELECT COUNT(*) FROM model_data",
}
for label, q in checks.items():
    n = pd.read_sql(q, conn).iloc[0, 0]
    print(f"{label}: {n}")

# ------------------------------------------------------------------
# 4. Export model_data for the regression step
# ------------------------------------------------------------------
model_data = pd.read_sql("SELECT * FROM model_data", conn)
model_data.to_csv("model_data.csv", index=False)
print(f"exported model_data.csv ({len(model_data)} rows)")

conn.close()
