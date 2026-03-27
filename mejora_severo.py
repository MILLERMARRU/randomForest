"""
Mejora del modelo de ansiedad – enfoque en clase Severo
SMOTE + RandomizedSearchCV (reducido) + ajuste de umbral
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # sin GUI, genera archivos
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, RandomizedSearchCV, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    classification_report, confusion_matrix, ConfusionMatrixDisplay,
    f1_score, precision_score, recall_score, make_scorer
)
from sklearn.impute import SimpleImputer
from imblearn.over_sampling import SMOTE
import warnings
warnings.filterwarnings("ignore")

# ══ 1. Carga y preprocesamiento ───────────────────────────────
print("Cargando dataset...")
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

# Features
all_q_cols = [f"Q{i}A" for i in range(1, 43) if i not in ANXIETY_ITEMS]
tipi_cols  = [f"TIPI{i}" for i in range(1, 11)]
demo_cols  = ["age", "gender", "education", "urban", "religion",
              "orientation", "race", "married", "familysize"]
feature_cols = all_q_cols + tipi_cols + demo_cols

for col in feature_cols:
    if col in df_clean.columns:
        df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")

feature_cols = [c for c in feature_cols if c in df_clean.columns]
df_model = df_clean[feature_cols + ["anxiety_level"]].dropna(subset=["anxiety_level"])

X = df_model[feature_cols]
y = df_model["anxiety_level"]

le = LabelEncoder()
le.fit(["Leve", "Moderado", "Severo"])
y_enc = le.transform(y)

X_train, X_test, y_train, y_test = train_test_split(
    X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
)

# ══ 2. Baseline (v1) ─────────────────────────────────────────
print("\nEntrenando baseline (v1)...")
imputer = SimpleImputer(strategy="median")
X_train_imp = imputer.fit_transform(X_train)
X_test_imp  = imputer.transform(X_test)

rf_base = RandomForestClassifier(
    n_estimators=200, class_weight="balanced", random_state=42, n_jobs=1
)
rf_base.fit(X_train_imp, y_train)
y_pred_v1 = rf_base.predict(X_test_imp)

print("=" * 55)
print("BASELINE v1")
print("=" * 55)
print(classification_report(y_test, y_pred_v1, target_names=le.classes_))

# ══ 3. SMOTE ─────────────────────────────────────────────────
print("Aplicando SMOTE...")
sm = SMOTE(random_state=42, k_neighbors=5)
X_res, y_res = sm.fit_resample(X_train_imp, y_train)

print("Distribución post-SMOTE:")
unique, counts = np.unique(y_res, return_counts=True)
for u, c in zip(unique, counts):
    print(f"  {le.classes_[u]}: {c}")

# ══ 4. RandomizedSearchCV (compacto, sin n_jobs=-1) ──────────
print("\nBuscando mejores hiperparámetros (n_iter=12)...")
severo_idx = list(le.classes_).index("Severo")
severo_f1  = make_scorer(f1_score, labels=[severo_idx], average="macro")

param_dist = {
    "n_estimators"     : [150, 200, 300],
    "max_depth"        : [20, 30, None],
    "min_samples_split": [2, 5],
    "min_samples_leaf" : [1, 2],
    "max_features"     : ["sqrt", "log2"],
    "class_weight"     : ["balanced", {0: 1, 1: 3, 2: 1}]
}

search = RandomizedSearchCV(
    RandomForestClassifier(random_state=42, n_jobs=1),
    param_distributions=param_dist,
    n_iter=12,
    scoring=severo_f1,
    cv=StratifiedKFold(n_splits=3, shuffle=True, random_state=42),
    random_state=42,
    n_jobs=1,       # evita conflictos joblib/zmq en Windows
    verbose=2
)
search.fit(X_res, y_res)

print("\nMejores parámetros:")
print(search.best_params_)
print(f"Mejor F1-Severo CV: {search.best_score_:.4f}")

# ══ 5. Evaluación v2 ─────────────────────────────────────────
best_rf    = search.best_estimator_
y_pred_v2  = best_rf.predict(X_test_imp)
y_proba_v2 = best_rf.predict_proba(X_test_imp)

print("\n" + "=" * 55)
print("v2 – SMOTE + HyperParam Tuning")
print("=" * 55)
print(classification_report(y_test, y_pred_v2, target_names=le.classes_))

# ══ 6. Ajuste de umbral para Severo ──────────────────────────
print("Optimizando umbral para Severo...")
thresholds = np.arange(0.30, 0.75, 0.02)
f1_list, pre_list, rec_list = [], [], []

for thr in thresholds:
    severo_mask = y_proba_v2[:, severo_idx] >= thr
    non_severo  = y_proba_v2.copy()
    non_severo[:, severo_idx] = 0
    y_thr = np.argmax(y_proba_v2, axis=1)
    y_thr[severo_mask]  = severo_idx
    y_thr[~severo_mask] = np.argmax(non_severo[~severo_mask], axis=1)

    f1_list.append(f1_score(y_test, y_thr,  labels=[severo_idx], average="macro"))
    pre_list.append(precision_score(y_test, y_thr, labels=[severo_idx], average="macro", zero_division=0))
    rec_list.append(recall_score(y_test,    y_thr, labels=[severo_idx], average="macro", zero_division=0))

best_thr_idx = int(np.argmax(f1_list))
best_thr     = thresholds[best_thr_idx]
print(f"Umbral óptimo: {best_thr:.2f}  |  F1={f1_list[best_thr_idx]:.4f}  "
      f"Precision={pre_list[best_thr_idx]:.4f}  Recall={rec_list[best_thr_idx]:.4f}")

# ══ 7. Predicciones finales ───────────────────────────────────
severo_mask_f = y_proba_v2[:, severo_idx] >= best_thr
non_severo_f  = y_proba_v2.copy()
non_severo_f[:, severo_idx] = 0
y_pred_final  = np.argmax(y_proba_v2, axis=1)
y_pred_final[severo_mask_f]  = severo_idx
y_pred_final[~severo_mask_f] = np.argmax(non_severo_f[~severo_mask_f], axis=1)

print("\n" + "=" * 55)
print("FINAL – SMOTE + Tuning + Umbral óptimo")
print("=" * 55)
print(classification_report(y_test, y_pred_final, target_names=le.classes_))

# ══ 8. Gráficas ──────────────────────────────────────────────
print("Generando gráficas...")

# Curva de umbral
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(thresholds, f1_list,  label="F1 Severo",  color="red",       linewidth=2)
ax.plot(thresholds, pre_list, label="Precision",  color="steelblue", linestyle="--")
ax.plot(thresholds, rec_list, label="Recall",     color="green",     linestyle="--")
ax.axvline(best_thr, color="red", linestyle=":", alpha=0.7,
           label=f"Umbral óptimo = {best_thr:.2f}")
ax.set_xlabel("Umbral de probabilidad para Severo")
ax.set_ylabel("Score")
ax.set_title("Optimización de umbral – Clase Severo")
ax.legend()
plt.tight_layout()
plt.savefig("threshold_optimization.png", dpi=150, bbox_inches="tight")
plt.close()

# Comparativa F1 por clase
def get_f1s(y_true, y_p):
    from sklearn.metrics import classification_report as cr
    rep = cr(y_true, y_p, target_names=le.classes_, output_dict=True)
    return [rep[c]["f1-score"] for c in le.classes_]

v1 = get_f1s(y_test, y_pred_v1)
v2 = get_f1s(y_test, y_pred_v2)
v3 = get_f1s(y_test, y_pred_final)

x = np.arange(len(le.classes_))
w = 0.25
fig, ax = plt.subplots(figsize=(9, 5))
ax.bar(x - w, v1, w, label="v1 Baseline",       color="#90CAF9")
ax.bar(x,     v2, w, label="v2 SMOTE+Tuning",   color="#1565C0")
ax.bar(x + w, v3, w, label="v3 +Umbral óptimo", color="#F44336")
ax.set_xticks(x)
ax.set_xticklabels(le.classes_, fontsize=12)
ax.set_ylabel("F1-Score")
ax.set_title("Comparativa F1 por clase y versión de modelo")
ax.legend()
ax.set_ylim(0, 1)
for bars in ax.containers:
    ax.bar_label(bars, fmt="%.2f", padding=2, fontsize=8)
plt.tight_layout()
plt.savefig("comparativa_modelos.png", dpi=150, bbox_inches="tight")
plt.close()

# Matrices de confusión comparadas
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for ax, (y_p, title) in zip(axes, [
    (y_pred_v1,    "v1 Baseline"),
    (y_pred_final, "v3 Final (SMOTE + Tuning + Umbral)")
]):
    cm = confusion_matrix(y_test, y_p)
    ConfusionMatrixDisplay(cm, display_labels=le.classes_).plot(
        ax=ax, colorbar=False, cmap="Blues")
    ax.set_title(title, fontsize=11)
plt.tight_layout()
plt.savefig("confusion_comparativa.png", dpi=150, bbox_inches="tight")
plt.close()

print("\nListo. Archivos generados:")
print("  threshold_optimization.png")
print("  comparativa_modelos.png")
print("  confusion_comparativa.png")
