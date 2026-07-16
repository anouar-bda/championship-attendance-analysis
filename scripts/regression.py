"""
regression.py
=============
The full attendance analysis: three nested models, residual analysis
(who under/over-fills), and every robustness check.

Findings (Model C, club fixed effects):
    derby              +8.0pp   (p < 0.001)
    midweek kickoff    -6.8pp   (p < 0.001)
    opponent quality   ~0       (p = 0.95)   -- no measurable effect
    home form          +0.28pp per point (p = 0.005) -- real but tiny

    Club identity (Model B -> C) lifts R^2 from 0.14 to 0.82:
    whether a Championship stadium fills is mostly about WHICH club it is.

Business question:
    What fills a Championship stadium, and which clubs leave money in
    the stands? Answer: the residuals. Blackburn under-fill by 34.5pp
    (~10,800 empty seats/match) after controlling for fixtures.
"""

import pandas as pd
import statsmodels.formula.api as smf

df = pd.read_csv("model_data.csv")


# ==================================================================
# 1. THREE NESTED MODELS
# ==================================================================
# A: fixtures only (no form)     -- keeps most matches
# B: + home form                 -- drops early-season matches (no form window)
# C: + club identity             -- the structural finding

a = df.dropna(subset=["away_ppg"]).copy()
mA = smf.ols(
    "FillRate ~ derby + away_ppg + C(slot) + home_match_no",
    data=a).fit()

b = df.dropna(subset=["home_form", "away_ppg"]).copy()
mB = smf.ols(
    "FillRate ~ derby + away_ppg + C(slot) + home_match_no + home_form",
    data=b).fit()

mC = smf.ols(
    "FillRate ~ derby + away_ppg + C(slot) + home_match_no + home_form + C(Home)",
    data=b).fit()

print("=" * 60)
print(f"Model A (fixtures only): {len(a)} matches, R2 = {mA.rsquared:.3f}")
print(f"Model B (+ form):        {len(b)} matches, R2 = {mB.rsquared:.3f}")
print(f"Model C (+ club):        {len(b)} matches, R2 = {mC.rsquared:.3f}")
print("=" * 60)
print(mC.summary())


# ==================================================================
# 2. RESIDUALS — who leaves money in the stands
# ==================================================================
# Uses Model B (NO club identity). With club fixed effects the model
# already "expects" each club's level, so residuals would be ~0. Without
# them, the residual is how much a club deviates from a GENERIC club with
# the same fixture list -- i.e. the structural gap.

b["predicted"] = mB.predict(b)
b["residual"]  = b["FillRate"] - b["predicted"]

gaps = (b.groupby("Home")
          .agg(actual=("FillRate", "mean"),
               predicted=("predicted", "mean"),
               gap=("residual", "mean"))
          .sort_values("gap"))

gaps_pct = (gaps * 100).round(1)
gaps_pct["empty_seats"] = (
    -gaps["gap"] * b.groupby("Home")["Capacity"].first()
).round(0)

print("\nRESIDUAL GAPS (actual - predicted fill, percentage points)")
print(gaps_pct.to_string())


# ==================================================================
# 3. ROBUSTNESS CHECKS
# ==================================================================
# Every discretionary choice is stress-tested. No finding depends on one.

def coefs(name, model, derby_col="derby"):
    return {
        "specification": name,
        "n": int(model.nobs),
        "derby": round(model.params.get(derby_col, float("nan")), 4),
        "midweek": round(model.params.get("C(slot)[T.midweek]", float("nan")), 4),
        "home_form": round(model.params.get("home_form", float("nan")), 4),
        "R2": round(model.rsquared, 3),
    }

rows = [coefs("Primary (7 derbies)", mC)]

# --- 3a. Strict derby definition (3 unambiguous rivalries) ---
strict_pairs = [
    {"Sheffield United", "Sheffield Weds"},
    {"Norwich City", "Ipswich Town"},
    {"Charlton Athletic", "Millwall"},
]
b["derby_strict"] = b.apply(
    lambda r: 1 if {r["Home"], r["Away"]} in strict_pairs else 0, axis=1)
r_strict = smf.ols(
    "FillRate ~ derby_strict + away_ppg + C(slot) + home_match_no + home_form + C(Home)",
    data=b).fit()
rows.append(coefs("Strict (3 derbies)", r_strict, "derby_strict"))

# --- 3b. Broad derby definition (13 rivalries incl. marginal) ---
broad_pairs = strict_pairs + [
    {"Blackburn", "Preston"}, {"Stoke City", "Derby County"},
    {"West Brom", "Birmingham City"}, {"Leicester City", "Coventry City"},
    {"Millwall", "QPR"}, {"QPR", "Charlton Athletic"},
    {"Swansea City", "Bristol City"}, {"Hull City", "Middlesbrough"},
    {"Watford", "QPR"}, {"Oxford United", "Coventry City"},
]
b["derby_broad"] = b.apply(
    lambda r: 1 if {r["Home"], r["Away"]} in broad_pairs else 0, axis=1)
r_broad = smf.ols(
    "FillRate ~ derby_broad + away_ppg + C(slot) + home_match_no + home_form + C(Home)",
    data=b).fit()
rows.append(coefs("Broad (13 derbies)", r_broad, "derby_broad"))

# --- 3c. Exclude Sheffield Wednesday (administration + boycott) ---
r_no_sw = smf.ols(
    "FillRate ~ derby + away_ppg + C(slot) + home_match_no + home_form + C(Home)",
    data=b[b["Home"] != "Sheffield Weds"]).fit()
rows.append(coefs("Excl. Sheffield Weds", r_no_sw))

# --- 3d. Exclude Wrexham (celebrity ownership, atypical demand) ---
r_no_wx = smf.ols(
    "FillRate ~ derby + away_ppg + C(slot) + home_match_no + home_form + C(Home)",
    data=b[b["Home"] != "Wrexham"]).fit()
rows.append(coefs("Excl. Wrexham", r_no_wx))

print("\nROBUSTNESS CHECKS")
print(pd.DataFrame(rows).to_string(index=False))


# ==================================================================
# 4. HILLSBOROUGH CAPACITY SENSITIVITY
# ==================================================================
# Sheffield Wednesday's 2025/26 capacity is uncertain: 39,732 (EFL listing)
# vs 34,835 (temporary safety reduction). Re-run at 34,835.
# All league-wide coefficients are stable; only Sheff Weds' residual moves.

alt = df.copy()
m = alt["Home"] == "Sheffield Weds"
alt.loc[m, "Capacity"] = 34835
alt.loc[m, "FillRate"] = alt.loc[m, "Attendance"] / 34835

alt_b = alt.dropna(subset=["home_form", "away_ppg"]).copy()
mC_alt = smf.ols(
    "FillRate ~ derby + away_ppg + C(slot) + home_match_no + home_form + C(Home)",
    data=alt_b).fit()

print("\nHILLSBOROUGH SENSITIVITY (capacity 39,732 vs 34,835)")
print(pd.DataFrame([
    coefs("Sheff Weds @ 39,732", mC),
    coefs("Sheff Weds @ 34,835", mC_alt),
]).to_string(index=False))
