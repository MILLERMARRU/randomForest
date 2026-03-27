from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import joblib, json, numpy as np, pandas as pd
from pathlib import Path

# ══ Cargar artefactos ────────────────────────────────────────
BASE = Path(__file__).parent.parent / "model"

rf  = joblib.load(BASE / "rf_anxiety.joblib")
imp = joblib.load(BASE / "imputer.joblib")
le  = joblib.load(BASE / "label_encoder.joblib")

with open(BASE / "metadata.json", encoding="utf-8") as f:
    meta = json.load(f)

FEATURE_COLS      = meta["feature_cols"]
ANXIETY_ITEMS     = meta["anxiety_items"]         # [2,4,7,9,15,19,20,23,25,28,30,36,40,41]
SEVERO_THR        = meta["severo_threshold"]       # 0.38
SEVERO_IDX        = meta["severo_idx"]
CLASSES           = meta["classes"]                # ["Leve","Moderado","Severo"]

# ══ DASS-42: cutoffs clínicos de ansiedad ────────────────────
# Score = suma ítems ansiedad (escala 0-3); el dataset usa 1-4 → restamos 1
DASS_CUTOFFS = {"Leve": (0, 9), "Moderado": (10, 14), "Severo": (15, 99)}

app = FastAPI(title="Anxiety Classifier API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://t81rg91w-5173.brs.devtunnels.ms",
    ],
    # Los subdominios de devtunnels pueden cambiar al reiniciar el túnel.
    allow_origin_regex=r"https://[a-z0-9-]+-5173\.brs\.devtunnels\.ms",
    allow_methods=["*"],
    allow_headers=["*"],
)

# ══ Schema de entrada ────────────────────────────────────────
class TestRequest(BaseModel):
    # 42 respuestas DASS (escala 1-4)
    Q1A:  int = Field(..., ge=1, le=4)
    Q2A:  int = Field(..., ge=1, le=4)
    Q3A:  int = Field(..., ge=1, le=4)
    Q4A:  int = Field(..., ge=1, le=4)
    Q5A:  int = Field(..., ge=1, le=4)
    Q6A:  int = Field(..., ge=1, le=4)
    Q7A:  int = Field(..., ge=1, le=4)
    Q8A:  int = Field(..., ge=1, le=4)
    Q9A:  int = Field(..., ge=1, le=4)
    Q10A: int = Field(..., ge=1, le=4)
    Q11A: int = Field(..., ge=1, le=4)
    Q12A: int = Field(..., ge=1, le=4)
    Q13A: int = Field(..., ge=1, le=4)
    Q14A: int = Field(..., ge=1, le=4)
    Q15A: int = Field(..., ge=1, le=4)
    Q16A: int = Field(..., ge=1, le=4)
    Q17A: int = Field(..., ge=1, le=4)
    Q18A: int = Field(..., ge=1, le=4)
    Q19A: int = Field(..., ge=1, le=4)
    Q20A: int = Field(..., ge=1, le=4)
    Q21A: int = Field(..., ge=1, le=4)
    Q22A: int = Field(..., ge=1, le=4)
    Q23A: int = Field(..., ge=1, le=4)
    Q24A: int = Field(..., ge=1, le=4)
    Q25A: int = Field(..., ge=1, le=4)
    Q26A: int = Field(..., ge=1, le=4)
    Q27A: int = Field(..., ge=1, le=4)
    Q28A: int = Field(..., ge=1, le=4)
    Q29A: int = Field(..., ge=1, le=4)
    Q30A: int = Field(..., ge=1, le=4)
    Q31A: int = Field(..., ge=1, le=4)
    Q32A: int = Field(..., ge=1, le=4)
    Q33A: int = Field(..., ge=1, le=4)
    Q34A: int = Field(..., ge=1, le=4)
    Q35A: int = Field(..., ge=1, le=4)
    Q36A: int = Field(..., ge=1, le=4)
    Q37A: int = Field(..., ge=1, le=4)
    Q38A: int = Field(..., ge=1, le=4)
    Q39A: int = Field(..., ge=1, le=4)
    Q40A: int = Field(..., ge=1, le=4)
    Q41A: int = Field(..., ge=1, le=4)
    Q42A: int = Field(..., ge=1, le=4)
    # Datos demográficos opcionales
    age:       Optional[int]   = 20
    gender:    Optional[int]   = 2     # 1=M 2=F 3=otro
    education: Optional[int]   = 3


# ══ Helpers ──────────────────────────────────────────────────
def dass_anxiety_score(data: dict) -> int:
    """Suma los 14 ítems de ansiedad DASS (escala 0-3)."""
    return sum(
        max(0, data[f"Q{i}A"] - 1)
        for i in ANXIETY_ITEMS
    )

def classify_dass(score: int) -> str:
    for nivel, (lo, hi) in DASS_CUTOFFS.items():
        if lo <= score <= hi:
            return nivel
    return "Severo"

def ml_predict(data: dict) -> dict:
    """Prediccion del modelo Random Forest."""
    row     = pd.DataFrame([data]).reindex(columns=FEATURE_COLS)
    row_imp = imp.transform(row)
    proba   = rf.predict_proba(row_imp)[0]

    if proba[SEVERO_IDX] >= SEVERO_THR:
        pred = SEVERO_IDX
    else:
        proba_aux = proba.copy()
        proba_aux[SEVERO_IDX] = 0
        pred = int(np.argmax(proba_aux))

    return {
        "nivel":          CLASSES[pred],
        "probabilidades": {
            CLASSES[i]: round(float(p) * 100, 1)
            for i, p in enumerate(proba)
        }
    }


# ══ Endpoints ────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "modelo": "DASS-42 Anxiety Classifier"}


@app.post("/predict")
def predict(body: TestRequest):
    data = body.model_dump()

    # Score clínico DASS
    score         = dass_anxiety_score(data)
    nivel_clinico = classify_dass(score)

    # Prediccion ML
    ml = ml_predict(data)

    return {
        "clinico": {
            "score": score,
            "nivel": nivel_clinico,
            "max_score": 42,
            "porcentaje": round(score / 42 * 100, 1)
        },
        "ml": ml,
        # Si ambos coinciden la confianza es mayor
        "coinciden": nivel_clinico == ml["nivel"]
    }


@app.get("/questions")
def get_questions():
    """Devuelve los metadatos de los ítems para el frontend."""
    return {
        "anxiety_items": ANXIETY_ITEMS,
        "scale": ["Nunca", "A veces", "Frecuentemente", "Casi siempre"]
    }
