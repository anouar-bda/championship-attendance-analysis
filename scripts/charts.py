"""
charts.py
=========
The three static charts embedded in the README. (The interactive
Tableau story is the primary visual deliverable; these give the repo
inline visuals that render on GitHub without a click-through.)

Run after regression.py logic — expects model_data.csv and rebuilds
Model B for the residuals.
"""

import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

df = pd.read_csv("model_data.csv")
b = df.dropna(subset=["home_form", "away_ppg"]).copy()
mB = smf.ols(
    "FillRate ~ derby + away_ppg + C(slot) + home_match_no + home_form",
    data=b).fit()
b["predicted"] = mB.predict(b)
b["residual"]  = b["FillRate"] - b["predicted"]


# ------------------------------------------------------------------
# 1. Fill rate by club
# ------------------------------------------------------------------
fill = b.groupby("Home")["FillRate"].mean().sort_values() * 100

fig, ax = plt.subplots(figsize=(9, 8))
colors = ["#c0392b" if v < 75 else "#7f8c8d" for v in fill]
ax.barh(fill.index, fill.values, color=colors)
ax.axvline(fill.mean(), color="black", linestyle="--", linewidth=1)
ax.text(fill.mean() + 1, len(fill) - 0.5,
        f"league avg {fill.mean():.0f}%", fontsize=9)
ax.set_xlabel("Average fill rate (%)")
ax.set_xlim(0, 100)
ax.set_title("Championship 2025/26 — stadium fill rate by club",
             fontsize=13, pad=15)
plt.tight_layout()
plt.savefig("../images/fill_rate_by_club.png", dpi=150)
plt.close()


# ------------------------------------------------------------------
# 2. What moves attendance (regression coefficients)
# ------------------------------------------------------------------
effects = {
    "Derby": 8.0,
    "Home form\n(best vs worst)": 4.2,
    "Opponent quality": 0.0,
    "Midweek kickoff": -6.8,
}
labels = list(effects.keys())
vals = list(effects.values())
colors = ["#27ae60" if v > 0 else "#c0392b" if v < 0 else "#bdc3c7"
          for v in vals]

fig, ax = plt.subplots(figsize=(8, 4))
ax.barh(labels, vals, color=colors)
ax.axvline(0, color="black", linewidth=1)
for i, v in enumerate(vals):
    ax.text(v + (0.2 if v >= 0 else -0.2), i, f"{v:+.1f}",
            va="center", ha="left" if v >= 0 else "right", fontsize=10)
ax.text(0.3, 2, "no measurable effect (p = 0.95)",
        va="center", fontsize=8, color="#7f8c8d", style="italic")
ax.set_xlabel("Effect on fill rate (percentage points)")
ax.set_xlim(-9, 11)
ax.set_title("What actually moves Championship attendance?",
             fontsize=13, pad=15)
plt.tight_layout()
plt.savefig("../images/what_moves_attendance.png", dpi=150)
plt.close()


# ------------------------------------------------------------------
# 3. Residual gap — who leaves money in the stands
# ------------------------------------------------------------------
gap = b.groupby("Home")["residual"].mean().sort_values() * 100

fig, ax = plt.subplots(figsize=(9, 8))
colors = ["#c0392b" if v < 0 else "#27ae60" for v in gap]
ax.barh(gap.index, gap.values, color=colors)
ax.axvline(0, color="black", linewidth=1)
ax.set_xlabel("Actual fill rate minus model prediction (percentage points)")
ax.set_title("Who is leaving money in the stands?", fontsize=13, pad=15)
plt.tight_layout()
plt.savefig("../images/residual_gap.png", dpi=150)
plt.close()

print("saved 3 charts to ../images/")
