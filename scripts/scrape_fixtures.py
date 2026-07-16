"""
scrape_fixtures.py
==================
Parse the FBref 2025/26 Championship Scores & Fixtures page into a clean
matches table, attach stadium capacities, compute fill rate, and validate.

FBref blocks automated requests (bot detection), so the page is saved
manually from a browser (Ctrl+S, "Webpage, HTML only") and parsed locally.

Output: championship_matches_validated.csv
"""

import pandas as pd

# ------------------------------------------------------------------
# 1. Load the saved FBref page
# ------------------------------------------------------------------
# The page contains three tables. Table index 0 has a `Round` column
# (regular season + play-offs); table index 1 is the regular season only.
# We use index 1 and confirm 552 rows (24 clubs x 46 games).
tables = pd.read_html("championship_fixtures_25_26.html")
df = tables[1]
df = df[df["Wk"].notna()].copy()          # drop matchweek separator rows

assert df.shape[0] == 552, f"expected 552 matches, got {df.shape[0]}"
assert df["Attendance"].isna().sum() == 0, "missing attendance values"

# ------------------------------------------------------------------
# 2. Stadium capacities (2025/26 configuration)
# ------------------------------------------------------------------
# Sourced from the Wikipedia 2025-26 EFL Championship season table and
# validated against maximum observed attendance (see notes below).
#
#   Wrexham: 12,600 is a judgment call. Wikipedia lists 10,771 (Kop
#   removed) but the observed max of 11,873 rules that out. 12,600 is the
#   smallest figure consistent with the data. Excluding Wrexham entirely
#   leaves all coefficients unchanged (see regression.py robustness checks).
#
#   Sheffield Weds: 39,732 used as primary; 34,835 (temporary safety
#   reduction) tested as a sensitivity in regression.py.
#
# Club names match FBref's spelling exactly (Blackburn, Preston, QPR,
# West Brom, Sheffield Weds) — mismatches would silently break the join.
capacities = {
    "Birmingham City": 29409,
    "Blackburn":       31367,
    "Bristol City":    26462,
    "Charlton Athletic": 27111,
    "Coventry City":   32609,
    "Derby County":    32926,
    "Hull City":       25586,
    "Ipswich Town":    30056,
    "Leicester City":  32259,
    "Middlesbrough":   34742,
    "Millwall":        20146,
    "Norwich City":    27359,
    "Oxford United":   12500,
    "Portsmouth":      20867,
    "Preston":         23408,
    "QPR":             18439,
    "Sheffield United": 32050,
    "Sheffield Weds":  39732,
    "Southampton":     32384,
    "Stoke City":      30089,
    "Swansea City":    21088,
    "Watford":         22200,
    "West Brom":       26850,
    "Wrexham":         12600,
}

df["Capacity"] = df["Home"].map(capacities)
assert df["Capacity"].isna().sum() == 0, "a club name did not match a capacity key"

# ------------------------------------------------------------------
# 3. Data validation — correct the one confirmed transcription error
# ------------------------------------------------------------------
# FBref reported Stoke v West Brom (30 Aug 2025) as 35,328 = 117% fill.
# Sky Sports confirms 25,328. Corrected here.
#
# (Wrexham v Charlton, 11,873, was flagged by the same check but CONFIRMED
#  genuine by Sky Sports — an anomaly is a prompt to check, not to delete.)
mask = (df["Home"] == "Stoke City") & (df["Date"] == "2025-08-30")
df.loc[mask, "Attendance"] = 25328

df["FillRate"] = df["Attendance"] / df["Capacity"]

# No match should exceed ~102% fill after correction.
over = df[df["FillRate"] > 1.02]
assert len(over) == 0, f"{len(over)} matches still exceed 102% fill"

# ------------------------------------------------------------------
# 4. Save
# ------------------------------------------------------------------
df.to_csv("championship_matches_validated.csv", index=False)
print(f"saved {len(df)} validated matches")
print(df.groupby("Home")["FillRate"].mean().sort_values().round(3))
