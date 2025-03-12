import bentoml
import numpy as np
from bentoml.io import JSON
from src.models.input_model import AdmissionInput, BatchAdmissionInput
from src.auth.jwt_auth import JWTAuthMiddleware, generate_token, get_current_user
from src.pg.pginit import init_db, DATABASE_CONFIG
from starlette.responses import JSONResponse
from typing import Optional, Dict, Any
import asyncio
from fastapi import HTTPException
from bentoml import Context
import time
import json
import os
import threading
import psycopg2

# Configuration des runners
runner1 = bentoml.sklearn.get("lopes_admission_lr:latest").to_runner(name="lopes_admission_lr_single")
runner2 = bentoml.sklearn.get("lopes_admission_lr:latest").to_runner(name="lopes_admission_lr_batch")

# Model scaler
scaler = bentoml.sklearn.load_model("lopes_admission_scaler:latest")

# Service avec middleware d'authentification
svc = bentoml.Service("admission_service", runners=[runner1, runner2])

# Chemin du fichier pour stocker les jobs
JOBS_FILE = "/tmp/batch_jobs.json"

# Verrou pour éviter les conflits d'accès au fichier
file_lock = threading.Lock()

# Fonction pour charger les jobs depuis le fichier
def load_jobs():
    if not os.path.exists(JOBS_FILE):
        return {}
    
    try:
        with file_lock:
            with open(JOBS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Erreur lors du chargement des jobs: {e}")
        return {}

# Fonction pour sauvegarder les jobs dans le fichier
def save_jobs(jobs):
    try:
        with file_lock:
            with open(JOBS_FILE, 'w') as f:
                json.dump(jobs, f)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des jobs: {e}")

@svc.on_startup
async def startup_tasks(*args):
    init_db()

@svc.api(input=JSON(), output=JSON())
async def login(input_data, ctx: Context):
    username = input_data.get("username")
    password = input_data.get("password")
    if username == "user123" and password == "password123":
        token = generate_token(username)
        return {"token": token}
    else:
        ctx.response.status_code = 401
        return {"detail": "Invalid credentials"}

@svc.api(input=JSON(pydantic_model=AdmissionInput), output=JSON())
async def predict(data: AdmissionInput, ctx: bentoml.Context):
    auth_header = ctx.request.headers.get("Authorization")  
    
    try:
        get_current_user(auth_header)
    except ValueError as e:
        ctx.response.status_code = 401
        return {"message": str(e)}

    input_data = np.array([[
        data.gre_score, 
        data.toefl_score, 
        data.university_rating, 
        data.sop, 
        data.lor, 
        data.cgpa, 
        data.research
    ]])

    input_data_scaled = scaler.transform(input_data)

    prediction = await runner1.async_run(input_data_scaled)

    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO predictions (
                gre_score, toefl_score, university_rating, sop, lor, cgpa, research, chance_of_admit
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.gre_score,
            data.toefl_score,
            data.university_rating,
            data.sop,
            data.lor,
            data.cgpa,
            data.research,
            float(prediction[0])
        ))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erreur d'insertion: {e}")
    
    return {"chance_of_admit": float(prediction[0])}

# Endpoint pour soumission de job batch
@svc.api(input=JSON(pydantic_model=BatchAdmissionInput), output=JSON())
async def batch_predict(input_data, ctx: bentoml.Context):
    auth_header = ctx.request.headers.get("Authorization")  
    
    try:
        get_current_user(auth_header)
    except ValueError as e:
        ctx.response.status_code = 401
        return {"message": str(e)}
    
    # Charger les jobs existants
    jobs = load_jobs()
    
    # Déterminer le prochain job_id
    if jobs:
        last_job_id = max(int(key.split('_')[1]) for key in jobs.keys() if key.startswith("job_"))
        job_id = f"job_{last_job_id + 1}"
    else:
        job_id = "job_1"  # Si aucun job n'existe, commencer par job_1
    
    # Stockage des données et du statut initial
    jobs[job_id] = {
        "status": "pending", 
        "data": input_data.dict()["predictions"],
        "created_at": time.time()
    }
    
    # Sauvegarder les jobs
    save_jobs(jobs)
    
    print(f"Job créé: {job_id}")
    
    try:
        input_list = []
        for item in jobs[job_id]["data"]:
            input_list.append([
                item["gre_score"],
                item["toefl_score"],
                item["university_rating"],
                item["sop"],
                item["lor"],
                item["cgpa"],
                item["research"]
            ])
        
        data = np.array(input_list)
        
        # Mise à l'échelle des données
        data_scaled = scaler.transform(data)
        
        # Prédiction
        predictions = await runner2.async_run(data_scaled)
        
        # Formatage des résultats
        results = []
        for pred in predictions:
            results.append({"chance_of_admit": float(pred)})
        
        # Charger à nouveau les jobs (ils pourraient avoir changé)
        jobs = load_jobs()
            
        # Mise à jour du statut du job
        jobs[job_id] = {
            "status": "completed",
            "predictions": results,
            "completed_at": time.time()
        }
        
        # Sauvegarder les jobs mis à jour
        save_jobs(jobs)
    except Exception as e:
        # Charger à nouveau les jobs
        jobs = load_jobs()
        
        jobs[job_id] = {
            "status": "failed",
            "error": str(e),
            "completed_at": time.time()
        }
        
        # Sauvegarder les jobs mis à jour
        save_jobs(jobs)

        # Stockage dans PostgreSQL
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cur = conn.cursor()
        for item, pred in zip(input_data.predictions, predictions):
            cur.execute("""
                INSERT INTO predictions (
                    job_id, gre_score, toefl_score, university_rating, sop, lor, cgpa, research, chance_of_admit
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                job_id,
                item.gre_score,
                item.toefl_score,
                item.university_rating,
                item.sop,
                item.lor,
                item.cgpa,
                item.research,
                float(pred)
            ))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erreur batch: {e}")
        return {"job_id": job_id, "status": "failed"}
    
    return {"job_id": job_id, "status": "pending"}

# Endpoint pour vérifier le statut d'un job batch
@svc.api(input=JSON(), output=JSON())
def batch_status(input_data, ctx: bentoml.Context):
    job_id = input_data.get("job_id")
    
    # Charger les jobs
    jobs = load_jobs()
    
    print(f"Vérification du statut pour le job: {job_id}")
    print(f"Jobs disponibles: {list(jobs.keys())}")
    
    if job_id not in jobs:
        print(f"Job non trouvé: {job_id}")
        ctx.response.status_code = 404
        return {"detail": f"Job {job_id} not found"}
    
    return jobs[job_id]

