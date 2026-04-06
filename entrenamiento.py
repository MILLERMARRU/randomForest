"""
Exporta el modelo final entrenado junto con todos los artefactos necesarios
para hacer predicciones desde cualquier aplicación.
"""
import pandas as pd
import numpy as np
import joblib
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report
from imblearn.over_sampling import SMOTE
import warnings
warnings.filterwarnings("ignore")

# ══ 1. Preparar datos ────────────────────────────────────────
print("Preparando datos...")
df = pd.read_csv("data.csv", sep="\t", low_memory=False)

ANXIETY_ITEMS = [2, 4, 7, 9, 15, 19, 20, 23, 25, 28, 30, 36, 40, 41]
anxiety_cols  = [f"Q{i}A" for i in ANXIETY_ITEMS]

df_clean = df.copy()
for col in anxiety_cols:
    df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")

df_clean["anxiety_score"] = df_clean[anxiety_cols].sub(1).clip(lower=0).sum(axis=1)

def classify_anxiety(score):
    if score <= 9:    return "Leve"
    elif score <= 14: return "Moderado"
    else:             return "Severo"

df_clean["anxiety_level"] = df_clean["anxiety_score"].apply(classify_anxiety)

all_q_cols   = [f"Q{i}A" for i in range(1, 43) if i not in ANXIETY_ITEMS]
tipi_cols    = [f"TIPI{i}" for i in range(1, 11)]
demo_cols    = ["age", "gender", "education", "urban", "religion",
                "orientation", "race", "married", "familysize"]
feature_cols = all_q_cols + tipi_cols + demo_cols

for col in feature_cols:
    if col in df_clean.columns:
        df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")

feature_cols = [c for c in feature_cols if c in df_clean.columns]
df_model     = df_clean[feature_cols + ["anxiety_level"]].dropna(subset=["anxiety_level"])

X     = df_model[feature_cols]
y     = df_model["anxiety_level"]
le    = LabelEncoder()
le.fit(["Leve", "Moderado", "Severo"])
y_enc = le.transform(y)

X_train, X_test, y_train, y_test = train_test_split(
    X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
)

# ══ 2. Entrenar modelo final ──────────────────────────────────
print("Entrenando modelo final sobre TODO el dataset...")

# Imputar → SMOTE → RF con mejores hiperparámetros encontrados
imputer     = SimpleImputer(strategy="median")
X_train_imp = imputer.fit_transform(X_train)
X_test_imp  = imputer.transform(X_test)

sm           = SMOTE(random_state=42, k_neighbors=5)
X_res, y_res = sm.fit_resample(X_train_imp, y_train)

best_rf = RandomForestClassifier(
    n_estimators=150,
    max_depth=None,
    max_features="sqrt",
    min_samples_split=5,
    min_samples_leaf=1,
    class_weight="balanced",
    random_state=42,
    n_jobs=1
)
best_rf.fit(X_res, y_res)

# Umbral óptimo para Severo
BEST_THRESHOLD = 0.38
SEVERO_IDX     = list(le.classes_).index("Severo")

y_proba = best_rf.predict_proba(X_test_imp)

def predict_with_threshold(proba, threshold, severo_idx):
    severo_mask  = proba[:, severo_idx] >= threshold
    non_severo   = proba.copy()
    non_severo[:, severo_idx] = 0
    y_out = np.argmax(proba, axis=1)
    y_out[severo_mask]  = severo_idx
    y_out[~severo_mask] = np.argmax(non_severo[~severo_mask], axis=1)
    return y_out

y_pred_final = predict_with_threshold(y_proba, BEST_THRESHOLD, SEVERO_IDX)

print("\nReporte final en test set:")
print(classification_report(y_test, y_pred_final, target_names=le.classes_))

# ══ 3. Exportar artefactos ───────────────────────────────────
print("Exportando artefactos...")

# Modelo y preprocesadores
joblib.dump(best_rf,  "model/rf_anxiety.joblib")
joblib.dump(imputer,  "model/imputer.joblib")
joblib.dump(le,       "model/label_encoder.joblib")

# Metadata (feature names, umbral, clases)
metadata = {
    "feature_cols"    : feature_cols,
    "anxiety_items"   : ANXIETY_ITEMS,
    "classes"         : list(le.classes_),
    "severo_threshold": BEST_THRESHOLD,
    "severo_idx"      : SEVERO_IDX,
    "scoring_notes": {
        "scale"      : "Respuestas en escala 1-4 (el modelo espera 1-4)",
        "Leve"       : "Score DASS-42 ansiedad 0-9",
        "Moderado"   : "Score DASS-42 ansiedad 10-14",
        "Severo"     : "Score DASS-42 ansiedad 15+"
    }
}
with open("model/metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

print("\nArtefactos exportados en model/:")
print("  rf_anxiety.joblib    → modelo Random Forest")
print("  imputer.joblib       → imputador de valores faltantes")
print("  label_encoder.joblib → codificador de etiquetas")
print("  metadata.json        → feature names, umbral y configuración")

# ══ 4. Función de predicción lista para usar ─────────────────
PREDICT_TEMPLATE = '''
import joblib, json, numpy as np, pandas as pd

# Cargar artefactos
rf  = joblib.load("model/rf_anxiety.joblib")
imp = joblib.load("model/imputer.joblib")
le  = joblib.load("model/label_encoder.joblib")
with open("model/metadata.json") as f:
    meta = json.load(f)

def predecir_ansiedad(respuestas: dict) -> dict:
    """
    Parámetros
    ----------
    respuestas : dict
        Valores para las features del modelo.
        Ejemplo: {"Q1A": 3, "Q3A": 2, "age": 21, "gender": 2, ...}
        Las claves no incluidas se imputarán con la mediana de entrenamiento.

    Retorna
    -------
    dict con "nivel" (str) y "probabilidades" (dict)
    """
    row = pd.DataFrame([respuestas]).reindex(columns=meta["feature_cols"])
    row_imp = imp.transform(row)
    proba   = rf.predict_proba(row_imp)[0]

    # Aplicar umbral optimizado para Severo
    thr  = meta["severo_threshold"]
    sidx = meta["severo_idx"]

    if proba[sidx] >= thr:
        pred = sidx
    else:
        proba_no_severo = proba.copy()
        proba_no_severo[sidx] = 0
        pred = int(np.argmax(proba_no_severo))

    nivel = le.classes_[pred]
    probs = {le.classes_[i]: round(float(p) * 100, 1) for i, p in enumerate(proba)}
    return {"nivel": nivel, "probabilidades": probs}


# ── Ejemplo de uso ──────────────────────────────────────────
if __name__ == "__main__":
    ejemplo = {f"Q{i}A": 3 for i in range(1, 43)
               if i not in meta["anxiety_items"]}
    ejemplo.update({"age": 22, "gender": 2, "education": 3})

    resultado = predecir_ansiedad(ejemplo)
    print(f"Nivel de ansiedad: {resultado[\'nivel\']}")
    print(f"Probabilidades:    {resultado[\'probabilidades\']}")
'''

with open("predecir.py", "w", encoding="utf-8") as f:
    f.write(PREDICT_TEMPLATE.strip())

print("  predecir.py          → script listo para usar el modelo")

# ══ 5. Verificación rápida ───────────────────────────────────
print("\nVerificación de carga y predicción...")
import os; os.system("")   # flush

rf2  = joblib.load("model/rf_anxiety.joblib")
imp2 = joblib.load("model/imputer.joblib")
le2  = joblib.load("model/label_encoder.joblib")

ejemplo = {f"Q{i}A": 3 for i in range(1, 43) if i not in ANXIETY_ITEMS}
ejemplo.update({"age": 22, "gender": 2, "education": 3})
row     = pd.DataFrame([ejemplo]).reindex(columns=feature_cols)
row_imp = imp2.transform(row)
proba   = rf2.predict_proba(row_imp)[0]

sidx  = meta["severo_idx"] if "meta" in dir() else SEVERO_IDX
nivel = le2.classes_[sidx if proba[sidx] >= BEST_THRESHOLD
                     else int(np.argmax([p if i != sidx else 0
                                         for i, p in enumerate(proba)]))]
probs = {le2.classes_[i]: round(float(p)*100, 1) for i, p in enumerate(proba)}

print(f"  Predicción de prueba: {nivel}")
print(f"  Probabilidades: {probs}")
print("\nExportación completada con éxito.")
