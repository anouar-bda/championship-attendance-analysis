-- ============================================================
-- 03_form_and_ppg.sql
-- Feature engineering with window functions.
--
--   home_form : points from the previous 5 matches (rolling)
--   away_ppg  : cumulative points-per-game before the current match
--
-- CRITICAL — NO DATA LEAKAGE:
--   Both features EXCLUDE the current match (ROWS ... AND 1 PRECEDING).
--   Including the current result would leak the outcome into a variable
--   used to predict attendance AT that match.
-- ============================================================


-- ------------------------------------------------------------
-- team_form: rolling 5-match points, with match number.
-- Matches 1–5 of each team's season have no complete window and are
-- dropped (match_no > 5), removing ~120 team-rows.
-- ------------------------------------------------------------
DROP TABLE IF EXISTS team_form;

CREATE TABLE team_form AS
SELECT * FROM (
    SELECT
        Date,
        team,
        venue,
        points,
        ROW_NUMBER() OVER (
            PARTITION BY team
            ORDER BY Date
        ) AS match_no,
        SUM(points) OVER (
            PARTITION BY team
            ORDER BY Date
            ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING   -- previous 5, excl. current
        ) AS form_5
    FROM (
        SELECT
            Date, team, venue,
            CASE WHEN goals_for >  goals_against THEN 3
                 WHEN goals_for =  goals_against THEN 1
                 ELSE 0 END AS points
        FROM team_matches
    )
)
WHERE match_no > 5;


-- ------------------------------------------------------------
-- team_ppg: cumulative points-per-game BEFORE the current match.
--   UNBOUNDED PRECEDING ... 1 PRECEDING = all prior matches, excl. current
--   CAST(... AS REAL) prevents integer division (6/7 = 0 without it)
--   First match of season has 0 prior games -> ppg is NULL (not 0)
-- ------------------------------------------------------------
DROP TABLE IF EXISTS team_ppg;

CREATE TABLE team_ppg AS
SELECT
    Date,
    team,
    pts_so_far,
    games_so_far,
    CASE
        WHEN games_so_far = 0 THEN NULL
        ELSE CAST(pts_so_far AS REAL) / games_so_far
    END AS ppg
FROM (
    SELECT
        Date,
        team,
        SUM(points) OVER (
            PARTITION BY team ORDER BY Date
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS pts_so_far,
        ROW_NUMBER() OVER (
            PARTITION BY team ORDER BY Date
        ) - 1 AS games_so_far
    FROM (
        SELECT
            Date, team,
            CASE WHEN goals_for >  goals_against THEN 3
                 WHEN goals_for =  goals_against THEN 1
                 ELSE 0 END AS points
        FROM team_matches
    )
);
