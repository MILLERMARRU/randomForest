"""
Prediccion de nivel de ansiedad usando el modelo entrenado.
Uso: python predecir.py
"""
import joblib
import json
import numpy as np
import pandas as pd

# Cargar artefactos
rf  = joblib.load("model/rf_anxiety.joblib")
imp = joblib.load("model/imputer.joblib")
le  = joblib.load("model/label_encoder.joblib")

with open("model/metadata.json", encoding="utf-8") as f:
    meta = json.load(f)


def predecir_ansiedad(respuestas: dict) -> dict:
    """
    Predice el nivel de ansiedad de un estudiante.

    Parametros
    ----------
    respuestas : dict
        Valores para las features del modelo.
        Ejemplo: {"Q1A": 3, "Q3A": 2, "age": 21, "gender": 2, ...}
        Escala de respuestas Q*A: 1 (nunca) a 4 (siempre).
        Las claves faltantes se imputaran con la mediana de entrenamiento.

    Retorna
    -------
    dict:
        "nivel"          -> "Leve" | "Moderado" | "Severo"
        "probabilidades" -> {"Leve": float, "Moderado": float, "Severo": float}
    """
    row     = pd.DataFrame([respuestas]).reindex(columns=meta["feature_cols"])
    row_imp = imp.transform(row)
    proba   = rf.predict_proba(row_imp)[0]

    # Umbral optimizado para Severo (0.38 vs default 0.5)
    thr  = meta["severo_threshold"]
    sidx = meta["severo_idx"]

    if proba[sidx] >= thr:
        pred = sidx
    else:
        proba_sin_severo = proba.copy()
        proba_sin_severo[sidx] = 0
        pred = int(np.argmax(proba_sin_severo))

    nivel = le.classes_[pred]
    probs = {le.classes_[i]: round(float(p) * 100, 1) for i, p in enumerate(proba)}
    return {"nivel": nivel, "probabilidades": probs}


# Ejemplo de uso
if __name__ == "__main__":
    # Respuestas de ejemplo (todas en 3 = "a veces")
    ejemplo = {f"Q{i}A": 3 for i in range(1, 43)
               if i not in meta["anxiety_items"]}
    ejemplo.update({"age": 22, "gender": 2, "education": 3})

    resultado = predecir_ansiedad(ejemplo)
    print(f"Nivel de ansiedad : {resultado['nivel']}")
    print(f"Probabilidades    : {resultado['probabilidades']}")
