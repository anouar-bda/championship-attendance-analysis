-- ============================================================
-- 01_load_and_clean.sql
-- Championship attendance analysis — 2025/26 EFL Championship
--
-- The `matches` table is loaded from championship_matches_validated.csv
-- (see scripts/build_database.py). This file documents the parsing and
-- cleaning logic applied to the raw FBref data.
--
-- NOTE ON THE SCORE DELIMITER:
--   FBref writes scores with an EN-DASH (–, U+2013), not a hyphen (-).
--   INSTR/SUBSTR must search for the en-dash or parsing silently fails.
-- ============================================================


-- ------------------------------------------------------------
-- Sanity check: every match should have a valid, parseable score.
-- This query returns 0 rows if all 552 scores parse to integers.
-- ------------------------------------------------------------
SELECT COUNT(*) AS unparseable_scores
FROM matches
WHERE CAST(SUBSTR(Score, 1, INSTR(Score, '–') - 1) AS INTEGER) IS NULL
   OR CAST(SUBSTR(Score, INSTR(Score, '–') + 1)    AS INTEGER) IS NULL;


-- ------------------------------------------------------------
-- Parse the score into home_goals / away_goals.
--   SUBSTR(Score, 1, INSTR(Score,'–') - 1)  -> everything before the dash
--   SUBSTR(Score, INSTR(Score,'–') + 1)     -> everything after the dash
--   CAST(... AS INTEGER)                     -> text '3' becomes number 3
-- ------------------------------------------------------------
SELECT
    Date,
    Home,
    Away,
    Score,
    CAST(SUBSTR(Score, 1, INSTR(Score, '–') - 1) AS INTEGER) AS home_goals,
    CAST(SUBSTR(Score, INSTR(Score, '–') + 1)    AS INTEGER) AS away_goals
FROM matches
LIMIT 10;


-- ------------------------------------------------------------
-- Data-validation check: no match should exceed ~102% fill rate.
-- This is how the Stoke v West Brom transcription error was caught
-- (FBref reported 35,328; the correct figure, per Sky Sports, was 25,328).
-- After correction, this query returns 0 rows above 1.02.
-- ------------------------------------------------------------
SELECT Home, Away, Date, Attendance, Capacity,
       CAST(Attendance AS REAL) / Capacity AS fill_rate
FROM matches
WHERE CAST(Attendance AS REAL) / Capacity > 1.02;
