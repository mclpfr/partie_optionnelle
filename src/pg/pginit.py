import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

DATABASE_CONFIG = {
    "dbname": "predictions",
    "user": "grafana",
    "password": "grafana",
    "host": "partie_optionnelle_postgres_1", 
    "port": "5432"
}

def init_db():
    conn = None
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id SERIAL PRIMARY KEY,
                job_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW(),
                gre_score INT,
                toefl_score INT,
                university_rating INT,
                sop FLOAT,
                lor FLOAT,
                cgpa FLOAT,
                research INT,
                chance_of_admit FLOAT
            );
        """)
        cur.close()
        conn.commit()
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données: {e}")
    finally:
        if conn:
            conn.close()