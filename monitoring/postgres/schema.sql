CREATE TABLE IF NOT EXISTS predictions (
  id SERIAL PRIMARY KEY,
  created_at TIMESTAMP DEFAULT NOW(),
  job_id VARCHAR(255),
  gre_score INT,
  toefl_score INT,
  university_rating INT,
  sop REAL,
  lor REAL,
  cgpa REAL,
  research INT,
  chance_of_admit REAL
);
