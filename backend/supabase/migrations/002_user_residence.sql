-- Adds the user's current place of residence to the users table.
-- Used by tools that need the *current* location (panchang, current sky,
-- daily transits) versus tools that need the *birth* place (birth chart,
-- dasha, nakshatra, sade sati).

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS residence_place_name TEXT,
    ADD COLUMN IF NOT EXISTS residence_lat DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS residence_lng DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS residence_timezone TEXT;
