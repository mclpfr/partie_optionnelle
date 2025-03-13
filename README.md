# Service de Prédiction d'Admission d'Étudiants

Ce projet est un service API basé sur BentoML qui permet de prédire les chances d'admission d'un étudiant à l'université en fonction de divers paramètres académiques.

## Architecture

L'architecture du service se compose de trois composants principaux :

1. **Service API** - Gère les requêtes HTTP et l'authentification
2. **Runner Single** - Traite les prédictions individuelles
3. **Runner Batch** - Optimisé pour les prédictions par lots

```
┌─────────────────┐      ┌──────────────┐      ┌─────────────┐
│   Client HTTP   │─────>│  API Service │─────>│  Runner 1   │
│    (Tests)      │      │   (BentoML)  │      │ (Single)    │
└─────────────────┘      │              │      └─────────────┘
                         │              │      ┌─────────────┐
                         │              │─────>│  Runner 2   │
                         │              │      │  (Batch)    │
                         └──────────────┘      └─────────────┘
```

## Fonctionnalités

- **Authentification JWT** - Sécurisation des endpoints avec tokens JWT
- **Prédictions individuelles** - Prédiction pour un étudiant
- **Prédictions par lots** - Traitement de multiples prédictions en une seule requête
- **Gestion des jobs asynchrones** - Pour les requêtes batch avec suivi de statut
- **Monitoring** - Visualisation des prédictions avec Grafana et stockage dans PostgreSQL

## Prérequis

- Python 3.10
- Docker et Docker Compose
- Un modèle scikit-learn entraîné avec le tag "lopes_admission_lr:latest" dans BentoML

## Installation

### 1. Installer les dépendances

```bash
python3 -m venv venv
source venv/bin/activate  
pip install -r requirements.txt
```

### 2. Préparation des données

```python
python src/prepare_data.py
```

### 2. Entrainement et sauvegarde du modèle

```python
python src/train_model.py 
```

### 3. Construire le BentoML Service

```bash
bentoml build
```

### 4. Construire l'image Docker

```bash
bentoml containerize admission_service:latest --image-tag admission_service:latest
```

## Lancement

```bash
docker-compose up -d
```

## Utilisation de l'API

> **Important** : Après le lancement des conteneurs, il faut attendre quelques secondes que l'API s'initialise complètement avant d'exécuter les commandes curl. 

### Authentification

```bash
token=$(curl -s -X POST http://127.0.0.1:3000/login \
     -H "Content-Type: application/json" \
     -d '{"username": "user123", "password": "password123"}' | jq -r '.token')
```

### Prédiction individuelle

```bash
curl -X POST http://localhost:3000/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $token" \
  -d '{
    "gre_score": 309,
    "toefl_score": 108,
    "university_rating": 4,
    "sop": 3.0,
    "lor": 4.0,
    "cgpa": 7.94,
    "research": 0
  }'
```

### Prédiction par lots

```bash
curl -X POST http://localhost:3000/batch_predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $token" \
  -d '{
    "predictions": [
      {
        "gre_score": 309,
        "toefl_score": 108,
        "university_rating": 4,
        "sop": 3.0,
        "lor": 4.0,
        "cgpa": 7.94,
        "research": 0
      },
      {
        "gre_score": 320,
        "toefl_score": 110,
        "university_rating": 5,
        "sop": 4.5,
        "lor": 4.0,
        "cgpa": 9.0,
        "research": 1
      }
    ]
  }'
```

### Vérification du statut d'un job batch

```bash
curl -X POST http://localhost:3000/batch_status \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $token" \
  -d '{
    "job_id": "job_1"
  }'
```

## Monitoring

Le service inclut un système de monitoring complet basé sur PostgreSQL et Grafana:

1. **PostgreSQL** - Stocke les données de prédiction pour analyse ultérieure
2. **Grafana** - Visualise les données de prédiction via un dashboard

### Accès au dashboard Grafana

- URL: http://localhost:3001
- Identifiants par défaut:
  - Login: admin
  - Mot de passe: admin
- Lors de la première connexion, vous pouvez choisir "Skip" pour passer l'étape de changement de mot de passe

### Dashboard "Prédiction"

Le dashboard "Prédiction" affiche les données des prédictions effectuées via l'API, incluant:
- Historique des prédictions
- Statistiques sur les paramètres utilisés
- Chances d'admission calculées
- Suivi des jobs batch

## Tests

```bash
pytest -v tests/test_endpoints.py
```

## Structure du projet

```
project/
├── src/
│   ├── auth/
│   │   └── jwt_auth.py      # Authentification JWT
│   ├── models/
│   │   └── input_model.py   # Modèles Pydantic
│   └── service_batch.py     # Service BentoML principal
├── tests/
│   └── test_endpoints.py    # Tests des endpoints
├── monitoring/
│   ├── grafana/
│   │   ├── dashboards/      # Configurations des dashboards Grafana
│   │   └── provisioning/    # Configuration de provisioning Grafana
│   └── postgres/
│       ├── data/            # Données persistantes PostgreSQL
│       └── schema.sql       # Schéma de base de données
├── bentofile.yml           # Configuration BentoML
├── docker-compose.yml      # Configuration Docker
├── requirements.txt        # Dépendances Python
└── README.md               # Documentation
```
