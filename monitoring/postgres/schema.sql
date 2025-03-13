CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    job_id VARCHAR(255),
    gre_score INTEGER,
    toefl_score INTEGER,
    university_rating INTEGER,
    sop FLOAT,
    lor FLOAT,
    cgpa FLOAT,
    research INTEGER CHECK (research IN (0, 1)),
    chance_of_admit FLOAT
);
