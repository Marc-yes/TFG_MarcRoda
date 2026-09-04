#!/usr/bin/env python3
import os
import json
import joblib
import warnings
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    precision_recall_fscore_support, 
    precision_recall_curve, 
    auc,
    fbeta_score,
    make_scorer,
    recall_score,
    brier_score_loss,
    confusion_matrix
)

warnings.filterwarnings("ignore")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "dataset_final_pcc.csv")
AI_DIR = os.path.join(BASE_DIR, "ai")
MODEL_S1_PATH = os.path.join(AI_DIR, "models", "model_stage1_v3.joblib")
MODEL_S2_PATH = os.path.join(AI_DIR, "models", "model_stage2_v3.joblib")
RANDOM_STATE = 42

def main():
    print("--- 1. Carregant dataset ---")
    df = pd.read_csv(DATA_PATH)
    print(f"Dataset carregat: {df.shape[0]} pacients, {df.shape[1]} columnes.")

    drop_cols = ["id_pacient", "target", "cronic", "prediccio_estat", "prob_maca", "prob_pcc"]
    X_all = df.drop(columns=[c for c in drop_cols if c in df.columns]).copy()

    # Separem les columnes segons la seva naturalesa clínica:
    # 1. Variables de laboratori (contínues: mitjanes i pendents)
    lab_cols = [c for c in X_all.columns if any(c.endswith(s) for s in ["_mean", "_slope"])]
    
    # 2. Categòriques
    cat_cols = X_all.select_dtypes(include=["object", "category"]).columns.tolist()
    
    # 3. Recomptes estructurals (fàrmacs, diagnòstics, visites, indicadors de laboratori)
    count_cols = [c for c in X_all.select_dtypes(include=["int64", "float64"]).columns if c not in lab_cols]

    print(f"Columnes recomptes (constant 0): {len(count_cols)}")
    print(f"Columnes laboratori (mediana):    {len(lab_cols)}")
    print(f"Columnes categòriques (moda):    {len(cat_cols)}")

    # Preprocessador especialitzat de 3 branques
    preprocessor = ColumnTransformer(
        transformers=[
            ("counts", Pipeline(steps=[
                ("imputer", SimpleImputer(strategy="constant", fill_value=0)),
                ("scaler", StandardScaler())
            ]), count_cols),
            ("labs", Pipeline(steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler())
            ]), lab_cols),
            ("cat", Pipeline(steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore"))
            ]), cat_cols),
        ]
    )

    y_target = df["target"].values

    print("\n--- 2. Entrenament final Model Stage 1 (Crònic vs No) ---")
    y1_all = (y_target > 0).astype(int)
    final_model1 = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(
            n_estimators=100, 
            max_depth=30, 
            min_samples_leaf=5, 
            class_weight="balanced", 
            random_state=RANDOM_STATE, 
            n_jobs=-1
        ))
    ])
    final_model1.fit(X_all, y1_all)
    print("Stage 1 entrenat correctament. [OK]")

    print("\n--- 3. Entrenament final Model Stage 2 (PCC vs MACA) ---")
    chronic_mask = (y_target > 0)
    X2_all = X_all[chronic_mask].copy()
    y2_all = (y_target[chronic_mask] == 2).astype(int)  # 0=PCC, 1=MACA

    final_base_model2 = HistGradientBoostingClassifier(
        max_iter=400,
        max_depth=15,
        learning_rate=0.01,
        class_weight="balanced",
        random_state=RANDOM_STATE
    )
    final_model2 = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", CalibratedClassifierCV(estimator=final_base_model2, cv=3))
    ])
    final_model2.fit(X2_all, y2_all)
    print("Stage 2 entrenat correctament. [OK]")

    # Desar models
    os.makedirs(os.path.dirname(MODEL_S1_PATH), exist_ok=True)
    joblib.dump(final_model1, MODEL_S1_PATH)
    joblib.dump(final_model2, MODEL_S2_PATH)
    print(f"Model Stage 1 desat a: {MODEL_S1_PATH}")
    print(f"Model Stage 2 desat a: {MODEL_S2_PATH}")

    print("\n--- 4. Generant prediccions per a tot el dataset ---")
    full_df = pd.read_csv(DATA_PATH)
    drop_cols_pred = ["id_pacient", "target", "cronic", "cronic_encoded", "sexe_encoded", "situacio_encoded", "edat_encoded", "prediccio_estat", "prob_maca", "prob_pcc"]
    X_full = full_df.drop(columns=[c for c in drop_cols_pred if c in full_df.columns], errors='ignore').copy()

    probs_s1 = final_model1.predict_proba(X_full)
    prob_chronic = probs_s1[:, 1]

    probs_s2 = final_model2.predict_proba(X_full)
    prob_pcc_cond = probs_s2[:, 0]
    prob_maca_cond = probs_s2[:, 1]

    prob_maca = prob_chronic * prob_maca_cond
    prob_pcc = prob_chronic * prob_pcc_cond

    pred_states = []
    for p_ch, p_ma_cond in zip(prob_chronic, prob_maca_cond):
        if p_ch < 0.50:
            pred_states.append("NO")
        else: 
            if p_ma_cond >= 0.40:
                pred_states.append("MACA")
            else:
                pred_states.append("PCC")

    full_df["prediccio_estat"] = pred_states
    full_df["prob_maca"] = prob_maca
    full_df["prob_pcc"] = prob_pcc

    full_df.to_csv(DATA_PATH, index=False)
    print(f"Dataset actualitzat amb noves prediccions a: {DATA_PATH}")

    print("\n--- 5. Actualitzant Jupyter Notebook trainIA_V3.ipynb ---")
    update_notebooks()

    print("\n--- 6. Reconstruint SQLite (clinic_data.sqlite) ---")
    import subprocess
    import sys
    migrate_script = os.path.join(BASE_DIR, "data", "migrate_csv_to_sqlite.py")
    subprocess.run([sys.executable, migrate_script], check=True, cwd=os.path.join(BASE_DIR, "data"))

    print("\n--- 7. Reconstruint index FAISS ---")
    faiss_script = os.path.join(AI_DIR, "build_faiss.py")
    subprocess.run([sys.executable, faiss_script], check=True, cwd=AI_DIR)

    print("\nTot el proces s'ha completat amb exit!")

def update_notebooks():
    nb_path = os.path.join(AI_DIR, "trainIA_V3.ipynb")
    principals_nb_path = os.path.join(BASE_DIR, "..", "Principals", "trainIA_V3.ipynb")
    
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    # Cel·la 3 (definició de preprocessor)
    new_source_cell3 = [
        "drop_cols = [\"id_pacient\", \"target\", \"cronic\"]\n",
        "X_all = df.drop(columns=[c for c in drop_cols if c in df.columns]).copy()\n",
        "\n",
        "# Separem les columnes per la seva naturalesa clínica:\n",
        "# 1. Laboratori (contínues: mitjanes i tendències)\n",
        "lab_cols = [c for c in X_all.columns if any(c.endswith(s) for s in [\"_mean\", \"_slope\"])]\n",
        "\n",
        "# 2. Categòriques\n",
        "cat_cols = X_all.select_dtypes(include=[\"object\", \"category\"]).columns.tolist()\n",
        "\n",
        "# 3. Recomptes estructurals (fàrmacs, diagnòstics, visites, indicadors de laboratori)\n",
        "count_cols = [c for c in X_all.select_dtypes(include=[\"int64\", \"float64\"]).columns if c not in lab_cols]\n",
        "\n",
        "# Preprocessador especialitzat de 3 branques\n",
        "preprocessor = ColumnTransformer(\n",
        "    transformers=[\n",
        "        # A) Recomptes i fàrmacs: Imputació amb valor constant 0 (absència estructural de registre)\n",
        "        (\"counts\", Pipeline(steps=[(\"imputer\", SimpleImputer(strategy=\"constant\", fill_value=0)), (\"scaler\", StandardScaler())]), count_cols),\n",
        "        # B) Laboratori: Imputació per mediana (robusta a valors atípics extrems)\n",
        "        (\"labs\", Pipeline(steps=[(\"imputer\", SimpleImputer(strategy=\"median\")), (\"scaler\", StandardScaler())]), lab_cols),\n",
        "        # C) Categòriques: Imputació per moda i one-hot\n",
        "        (\"cat\", Pipeline(steps=[(\"imputer\", SimpleImputer(strategy=\"most_frequent\")), (\"onehot\", OneHotEncoder(handle_unknown=\"ignore\"))]), cat_cols),\n",
        "    ]\n",
        ")"
    ]

    for cell in nb["cells"]:
        if cell["cell_type"] == "code" and "preprocessor = ColumnTransformer" in "".join(cell["source"]):
            cell["source"] = new_source_cell3
            break

    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print(f"Notebook {nb_path} actualitzat.")

    if os.path.exists(principals_nb_path):
        with open(principals_nb_path, "w", encoding="utf-8") as f:
            json.dump(nb, f, indent=1, ensure_ascii=False)
        print(f"Notebook {principals_nb_path} sincronitzat.")

    # Baselines notebook
    base_nb_path = os.path.join(AI_DIR, "baselines.ipynb")
    if os.path.exists(base_nb_path):
        with open(base_nb_path, "r", encoding="utf-8") as f:
            base_nb = json.load(f)
        
        for cell in base_nb["cells"]:
            if cell["cell_type"] == "code" and "preprocessor = ColumnTransformer" in "".join(cell["source"]):
                cell["source"] = new_source_cell3
                break
                
        with open(base_nb_path, "w", encoding="utf-8") as f:
            json.dump(base_nb, f, indent=1, ensure_ascii=False)
        print(f"Notebook {base_nb_path} actualitzat.")

if __name__ == "__main__":
    main()
