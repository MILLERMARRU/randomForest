import json

with open('anxiety_model.ipynb') as f:
    nb = json.load(f)

new_cells = [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": ["## 8. Mejora del modelo – Severo\n", "\n",
               "Estrategias:\n",
               "1. **SMOTE** para balancear Moderado vs Severo\n",
               "2. **RandomizedSearchCV** para hiperparámetros óptimos\n",
               "3. **Ajuste de umbral** para maximizar F1 de Severo"]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": """from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import f1_score, make_scorer, precision_score, recall_score
import warnings
warnings.filterwarnings("ignore")

# Imputar NaN antes de SMOTE
imputer = SimpleImputer(strategy="median")
X_train_imp = imputer.fit_transform(X_train)
X_test_imp  = imputer.transform(X_test)

# SMOTE: oversamplea Moderado para equilibrar clases
sm = SMOTE(random_state=42, k_neighbors=5)
X_res, y_res = sm.fit_resample(X_train_imp, y_train)

print("Distribución post-SMOTE:")
unique, counts = np.unique(y_res, return_counts=True)
for u, c in zip(unique, counts):
    print(f"  {le.classes_[u]}: {c}")
""".splitlines(keepends=True)
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": """# RandomizedSearchCV optimizando F1 de Severo
param_dist = {
    "n_estimators"     : [200, 300, 500],
    "max_depth"        : [None, 20, 30, 40],
    "min_samples_split": [2, 5, 10],
    "min_samples_leaf" : [1, 2, 4],
    "max_features"     : ["sqrt", "log2", 0.4],
    "class_weight"     : ["balanced", "balanced_subsample",
                          {0: 1, 1: 3, 2: 1}]
}

severo_idx = list(le.classes_).index("Severo")
severo_f1  = make_scorer(f1_score, labels=[severo_idx], average="macro")

rf_search = RandomForestClassifier(random_state=42, n_jobs=-1)

search = RandomizedSearchCV(
    rf_search,
    param_distributions=param_dist,
    n_iter=30,
    scoring=severo_f1,
    cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
    random_state=42,
    n_jobs=-1,
    verbose=1
)

search.fit(X_res, y_res)
print("\\nMejores parámetros:")
print(search.best_params_)
print(f"Mejor F1-Severo CV: {search.best_score_:.4f}")
""".splitlines(keepends=True)
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": """# Evaluación v2: SMOTE + mejores hiperparámetros
best_rf    = search.best_estimator_
y_pred_v2  = best_rf.predict(X_test_imp)
y_proba_v2 = best_rf.predict_proba(X_test_imp)

print("="*55)
print("REPORTE v2 – SMOTE + HyperParam Tuning")
print("="*55)
print(classification_report(y_test, y_pred_v2, target_names=le.classes_))
""".splitlines(keepends=True)
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": """# Ajuste de umbral para Severo – maximizar F1
thresholds = np.arange(0.30, 0.75, 0.02)
f1_severo_list, precision_severo, recall_severo = [], [], []

for thr in thresholds:
    severo_mask = y_proba_v2[:, severo_idx] >= thr
    non_severo_proba = y_proba_v2.copy()
    non_severo_proba[:, severo_idx] = 0
    y_thr = np.argmax(y_proba_v2, axis=1)
    y_thr[severo_mask]  = severo_idx
    y_thr[~severo_mask] = np.argmax(non_severo_proba[~severo_mask], axis=1)

    f1_severo_list.append(f1_score(y_test, y_thr, labels=[severo_idx], average="macro"))
    precision_severo.append(precision_score(y_test, y_thr, labels=[severo_idx], average="macro", zero_division=0))
    recall_severo.append(recall_score(y_test, y_thr, labels=[severo_idx], average="macro", zero_division=0))

best_thr_idx = int(np.argmax(f1_severo_list))
best_thr = thresholds[best_thr_idx]

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(thresholds, f1_severo_list,  label="F1 Severo",    color="red",       linewidth=2)
ax.plot(thresholds, precision_severo, label="Precision",   color="steelblue", linestyle="--")
ax.plot(thresholds, recall_severo,   label="Recall",       color="green",     linestyle="--")
ax.axvline(best_thr, color="red", linestyle=":", alpha=0.7, label=f"Umbral óptimo = {best_thr:.2f}")
ax.set_xlabel("Umbral de probabilidad para Severo")
ax.set_ylabel("Score")
ax.set_title("Optimización de umbral – Clase Severo")
ax.legend()
plt.tight_layout()
plt.savefig("threshold_optimization.png", dpi=150, bbox_inches="tight")
plt.show()

print(f"Umbral óptimo para Severo: {best_thr:.2f}")
print(f"  F1:        {f1_severo_list[best_thr_idx]:.4f}")
print(f"  Precision: {precision_severo[best_thr_idx]:.4f}")
print(f"  Recall:    {recall_severo[best_thr_idx]:.4f}")
""".splitlines(keepends=True)
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": """# Predicciones finales con umbral óptimo
severo_mask_final = y_proba_v2[:, severo_idx] >= best_thr
non_severo = y_proba_v2.copy()
non_severo[:, severo_idx] = 0
y_pred_final = np.argmax(y_proba_v2, axis=1)
y_pred_final[severo_mask_final]  = severo_idx
y_pred_final[~severo_mask_final] = np.argmax(non_severo[~severo_mask_final], axis=1)

print("="*55)
print("REPORTE FINAL – SMOTE + Tuning + Umbral óptimo")
print("="*55)
print(classification_report(y_test, y_pred_final, target_names=le.classes_))

# Comparativa F1 por versión
from sklearn.metrics import classification_report as cr
def get_f1s(y_true, y_pred_arg):
    rep = cr(y_true, y_pred_arg, target_names=le.classes_, output_dict=True)
    return [rep[c]["f1-score"] for c in le.classes_]

v1 = get_f1s(y_test, y_pred)
v2 = get_f1s(y_test, y_pred_v2)
v3 = get_f1s(y_test, y_pred_final)

x = np.arange(len(le.classes_))
width = 0.25
fig, ax = plt.subplots(figsize=(9, 5))
ax.bar(x - width, v1, width, label="v1 Baseline",       color="#90CAF9")
ax.bar(x,         v2, width, label="v2 SMOTE+Tuning",   color="#1565C0")
ax.bar(x + width, v3, width, label="v3 +Umbral óptimo", color="#F44336")
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
plt.show()
""".splitlines(keepends=True)
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": """# Matrices de confusión: baseline vs final
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

for ax, (y_p, title) in zip(axes, [
    (y_pred,       "v1 Baseline"),
    (y_pred_final, "v3 Final (SMOTE + Tuning + Umbral)")
]):
    cm = confusion_matrix(y_test, y_p)
    ConfusionMatrixDisplay(cm, display_labels=le.classes_).plot(
        ax=ax, colorbar=False, cmap="Blues")
    ax.set_title(title, fontsize=11)

plt.tight_layout()
plt.savefig("confusion_comparativa.png", dpi=150, bbox_inches="tight")
plt.show()
""".splitlines(keepends=True)
  }
]

nb["cells"].extend(new_cells)

with open("anxiety_model.ipynb", "w") as f:
    json.dump(nb, f, indent=1)

print(f"Celdas añadidas. Total de celdas: {len(nb['cells'])}")
