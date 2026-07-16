-- ============================================================
-- 02_team_matches.sql
-- Reshape 552 match rows into 1,104 team-match rows.
--
-- Form is a property of a TEAM, not a match. To compute it we need
-- each team's full season (home and away) in one column. UNION ALL
-- stacks two views of the match table: one from the home team's
-- perspective, one from the away team's.
--
-- Note the goals SWAP in the second block: from the away team's point
-- of view, the away score is THEIR goals_for.
-- ============================================================

DROP TABLE IF EXISTS team_matches;

CREATE TABLE team_matches AS

-- Home team's perspective
SELECT
    Date,
    Home AS team,
    'H'  AS venue,
    CAST(SUBSTR(Score, 1, INSTR(Score, '–') - 1) AS INTEGER) AS goals_for,
    CAST(SUBSTR(Score, INSTR(Score, '–') + 1)    AS INTEGER) AS goals_against
FROM matches

UNION ALL

-- Away team's perspective (goals swapped)
SELECT
    Date,
    Away AS team,
    'A'  AS venue,
    CAST(SUBSTR(Score, INSTR(Score, '–') + 1)    AS INTEGER) AS goals_for,
    CAST(SUBSTR(Score, 1, INSTR(Score, '–') - 1) AS INTEGER) AS goals_against
FROM matches;


-- ------------------------------------------------------------
-- Checks: 1,104 rows total, 46 games per club.
-- ------------------------------------------------------------
SELECT COUNT(*) AS total_rows FROM team_matches;                 -- expect 1104
SELECT team, COUNT(*) AS games FROM team_matches GROUP BY team;  -- each expect 46
