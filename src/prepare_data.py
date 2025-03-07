import pandas as pd 
import numpy as np  
from sklearn.model_selection import train_test_split  
from sklearn.preprocessing import StandardScaler  
import os  
import bentoml
import requests

os.makedirs('data/raw', exist_ok=True)  
os.makedirs('data/processed', exist_ok=True) 

dataset_url = "https://assets-datascientest.s3.eu-west-1.amazonaws.com/MLOPS/bentoml/admission.csv"
raw_data_path = "data/raw/admission.csv"

# Télécharger le fichier s'il n'existe pas déjà
if not os.path.exists(raw_data_path):
    response = requests.get(dataset_url)
    with open(raw_data_path, 'wb') as file:
        file.write(response.content)
    print(f"Fichier téléchargé et enregistré à {raw_data_path}")
else:
    print(f"Le fichier existe déjà à {raw_data_path}")

data = pd.read_csv(raw_data_path)

print("\nValeurs manquantes par colonne :")
print(data.isnull().sum())

# Suppression de la colonne "Serial No." si elle existe
if 'Serial No.' in data.columns:
    data = data.drop('Serial No.', axis=1)

# Définir les caractéristiques et la variable cible
X = data.drop('Chance of Admit ', axis=1)
y = data['Chance of Admit ']

# Diviser les données en ensembles d'entraînement et de test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Normaliser les données
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Enregistrer le scaler avec bentoML
bentoml.sklearn.save_model("lopes_admission_scaler", scaler)
print("Scaler enregistré avec bentoML")

# Sauvegarder les données au format CSV
print("Sauvegarde des données au format CSV...")

# Convertir les données normalisées en DataFrame
X_train_df = pd.DataFrame(X_train_scaled, columns=X_train.columns)
X_test_df = pd.DataFrame(X_test_scaled, columns=X_test.columns)

# Sauvegarder les fichiers séparément
X_train_df.to_csv('data/processed/X_train.csv', index=False)
X_test_df.to_csv('data/processed/X_test.csv', index=False)
y_train.to_csv('data/processed/y_train.csv', index=False)
y_test.to_csv('data/processed/y_test.csv', index=False)

print("Traitement des données terminé. Fichiers CSV sauvegardés dans le répertoire data/processed/.")
