import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import matplotlib.pyplot as plt
import bentoml

# Chargement des données préparées
X_train = pd.read_csv('data/processed/X_train.csv').values
X_test = pd.read_csv('data/processed/X_test.csv').values
y_train = pd.read_csv('data/processed/y_train.csv').values.ravel()
y_test = pd.read_csv('data/processed/y_test.csv').values.ravel()

# Création et entraînement du modèle
model = LinearRegression()
model.fit(X_train, y_train)

# Prédictions sur l'ensemble de test
y_pred = model.predict(X_test)

# Évaluation de la performance du modèle
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)

print(f"Performance du modèle :")
print(f"MSE: {mse:.4f}")
print(f"RMSE: {rmse:.4f}")
print(f"R²: {r2:.4f}")
print(f"MAE: {mae:.4f}")

# Visualisation des résultats
plt.figure(figsize=(10, 6))
plt.scatter(y_test, y_pred, alpha=0.5)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--')
plt.xlabel('Valeurs réelles')
plt.ylabel('Prédictions')
plt.title('Comparaison des valeurs réelles et des prédictions')
plt.savefig('models/prediction_vs_actual.png')
plt.close()

# Sauvegarde du modèle avec BentoML
bentoml.sklearn.save_model("lopes_admission_lr", model, signatures={"predict": {"batchable": True,}},)

print("\nModèle enregistré avec BentoML sous le nom 'lopes_admission_lr'")
