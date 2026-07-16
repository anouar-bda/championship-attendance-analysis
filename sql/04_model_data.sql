-- ============================================================
-- 04_model_data.sql
-- Build match-level features, then join everything into model_data.
-- ============================================================


-- ------------------------------------------------------------
-- match_features: adds fill_rate, kickoff slot, and derby flag.
--
-- Kickoff times were cleaned first: a handful of delayed kickoffs
-- (15:01, 12:31, etc.) are mapped back to their scheduled times.
--
-- Slot categories:
--   midweek           : Tue / Wed / Thu
--   fri_mon_night     : Fri / Mon
--   weekend_standard  : Sat / Sun at 15:00
--   weekend_other     : any other weekend time
--
-- Derby = 7 researched rivalries, graded before modelling. A stricter
-- (3) and broader (13) definition are tested in the regression script.
-- ------------------------------------------------------------
DROP TABLE IF EXISTS match_features;

CREATE TABLE match_features AS
SELECT
    *,
    CASE
        WHEN Day IN ('Tue','Wed','Thu')                    THEN 'midweek'
        WHEN Day IN ('Fri','Mon')                          THEN 'fri_mon_night'
        WHEN Day IN ('Sat','Sun') AND time_clean = '15:00' THEN 'weekend_standard'
        ELSE 'weekend_other'
    END AS slot,

    CASE WHEN
        (Home = 'Sheffield United'  AND Away = 'Sheffield Weds')    OR
        (Home = 'Sheffield Weds'    AND Away = 'Sheffield United')  OR
        (Home = 'Norwich City'      AND Away = 'Ipswich Town')      OR
        (Home = 'Ipswich Town'      AND Away = 'Norwich City')      OR
        (Home = 'Charlton Athletic' AND Away = 'Millwall')          OR
        (Home = 'Millwall'          AND Away = 'Charlton Athletic') OR
        (Home = 'Blackburn'         AND Away = 'Preston')           OR
        (Home = 'Preston'           AND Away = 'Blackburn')         OR
        (Home = 'Stoke City'        AND Away = 'Derby County')      OR
        (Home = 'Derby County'      AND Away = 'Stoke City')        OR
        (Home = 'West Brom'         AND Away = 'Birmingham City')   OR
        (Home = 'Birmingham City'   AND Away = 'West Brom')         OR
        (Home = 'Leicester City'    AND Away = 'Coventry City')     OR
        (Home = 'Coventry City'     AND Away = 'Leicester City')
    THEN 1 ELSE 0 END AS derby

FROM (
    SELECT
        *,
        CASE Time
            WHEN '15:01' THEN '15:00'
            WHEN '12:31' THEN '12:30'
            WHEN '20:01' THEN '20:00'
            WHEN '12:01' THEN '12:00'
            ELSE Time
        END AS time_clean
    FROM matches
);


-- ------------------------------------------------------------
-- model_data: one row per match, with all model inputs.
--   home_form  : the HOME team's rolling form (join on Home)
--   away_ppg   : the AWAY team's points-per-game (join on Away)
--
-- LEFT JOINs keep all 552 matches. Early-season matches with no form
-- window carry NULLs and are dropped at model-fit time — not here.
-- This preserves the full sample for descriptive work.
-- ------------------------------------------------------------
DROP TABLE IF EXISTS model_data;

CREATE TABLE model_data AS
SELECT
    m.Date,
    m.Home,
    m.Away,
    m.Attendance,
    m.Capacity,
    m.FillRate,
    m.slot,
    m.derby,
    SUBSTR(m.Date, 6, 2) AS month,
    ROW_NUMBER() OVER (PARTITION BY m.Home ORDER BY m.Date) AS home_match_no,
    f.form_5 AS home_form,
    p.ppg    AS away_ppg
FROM match_features m
LEFT JOIN team_form f
    ON m.Date = f.Date AND m.Home = f.team
LEFT JOIN team_ppg p
    ON m.Date = p.Date AND m.Away = p.team;
