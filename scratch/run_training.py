import os
import sys
import json
import shutil
import warnings
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
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

def main():
    os.chdir(r"c:\Users\1516m\Desktop\UNI\GEI\4t\2Q\TFG\Codi_Projecte\ai")
    DATA_PATH = "../data/processed/dataset_final_pcc.csv"
    MODEL_S1_PATH = "models/model_stage1_v3.joblib"
    MODEL_S2_PATH = "models/model_stage2_v3.joblib"
    RANDOM_STATE = 42

    print("--- Iniciant entrenament jeràrquic V3 (Ultra Precisió) ---", flush=True)
    df = pd.read_csv(DATA_PATH)
    print(f"Dataset carregat: {df.shape[0]} pacients, {df.shape[1]} columnes.", flush=True)

    drop_cols = ["id_pacient", "target", "cronic", "prediccio_estat", "prob_maca", "prob_pcc"]
    X_all = df.drop(columns=[c for c in drop_cols if c in df.columns]).copy()

    num_cols = X_all.select_dtypes(include=["int64", "float64"]).columns.tolist()
    cat_cols = X_all.select_dtypes(include=["object", "category"]).columns.tolist()

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline(steps=[("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), num_cols),
            ("cat", Pipeline(steps=[("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), cat_cols),
        ]
    )

    # Nested Cross-Validation
    y_target = df["target"].values
    outer_cv = StratifiedKFold(n_splits=4, shuffle=True, random_state=RANDOM_STATE)
    oof_preds = np.zeros(len(df))
    oof_probs = np.zeros((len(df), 3))

    print("\n--- Iniciant Bucle de Nested Cross-Validation (Mètriques Realistes) ---", flush=True)
    nested_cv_output_lines = ["--- Iniciant Bucle de Nested Cross-Validation (Mètriques Realistes) ---\n\n"]

    for fold, (train_idx, test_idx) in enumerate(outer_cv.split(X_all, y_target)):
        print(f" Processant fold exterior {fold + 1}...", flush=True)
        nested_cv_output_lines.append(f" Processant fold exterior {fold + 1}...\n")
        
        X_train_f, X_test_f = X_all.iloc[train_idx], X_all.iloc[test_idx]
        y_train_f, y_test_f = y_target[train_idx], y_target[test_idx]
        
        # Estat 1: CRÒNIC vs NO (classes {0, 1})
        y1_train_f = (y_train_f > 0).astype(int)
        model1 = Pipeline(steps=[
            ("preprocessor", preprocessor),
            ("classifier", RandomForestClassifier(n_estimators=100, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=1))
        ])
        model1_params = {
            "classifier__max_depth": [20, 30, 50],
            "classifier__min_samples_leaf": [1, 2, 5]
        }
        inner_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
        grid_model1 = GridSearchCV(
            estimator=model1,
            param_grid=model1_params,
            cv=inner_cv,
            scoring=make_scorer(recall_score, pos_label=1),
            n_jobs=-1
        )
        grid_model1.fit(X_train_f, y1_train_f)
        best_model1 = grid_model1.best_estimator_
        p1_str = f"  [Estat 1] Millors paràmetres: {grid_model1.best_params_}"
        print(p1_str, flush=True)
        nested_cv_output_lines.append(p1_str + "\n")
        
        # Estat 2: PCC vs MACA (classes {1, 2})
        chronic_mask = (y_train_f > 0)
        X2_train_f = X_train_f[chronic_mask]
        y2_train_f = y_train_f[chronic_mask]
        
        base_model2 = HistGradientBoostingClassifier(class_weight="balanced", random_state=RANDOM_STATE)
        model2 = Pipeline(steps=[
            ("preprocessor", preprocessor),
            ("classifier", CalibratedClassifierCV(estimator=base_model2, cv=3))
        ])
        model2_params = {
            "classifier__estimator__max_depth": [5, 10, 15],
            "classifier__estimator__learning_rate": [0.01, 0.05, 0.1]
        }
        grid_model2 = GridSearchCV(
            estimator=model2,
            param_grid=model2_params,
            cv=inner_cv,
            scoring=make_scorer(recall_score, pos_label=2),
            n_jobs=-1
        )
        grid_model2.fit(X2_train_f, y2_train_f)
        best_model2 = grid_model2.best_estimator_
        p2_str = f"  [Estat 2] Millors paràmetres: {grid_model2.best_params_}\n"
        print(p2_str, flush=True)
        nested_cv_output_lines.append(p2_str + "\n")
        
        # OOF Predictions
        p_chronic = best_model1.predict_proba(X_test_f)[:, 1]
        p_no = 1.0 - p_chronic
        probs_s2 = best_model2.predict_proba(X_test_f)
        p_pcc_given_chronic = probs_s2[:, 0]
        p_maca_given_chronic = probs_s2[:, 1]
        
        p_pcc = p_chronic * p_pcc_given_chronic
        p_maca = p_chronic * p_maca_given_chronic
        oof_probs[test_idx] = np.column_stack([p_no, p_pcc, p_maca])
        
        y_pred_fold = np.zeros_like(p_chronic, dtype=int)
        chronic_indices = np.where(p_chronic >= 0.55)[0]
        if len(chronic_indices) > 0:
            maca_mask = (p_maca_given_chronic[chronic_indices] >= 0.40)
            y_pred_fold[chronic_indices] = np.where(maca_mask, 2, 1)
        oof_preds[test_idx] = y_pred_fold

    nested_cv_output_lines.append("--- Bucle de Nested CV finalitzat correctament ---\n")
    print("--- Bucle de Nested CV finalitzat correctament ---", flush=True)

    # Metrics evaluation
    target_names = ["NO", "PCC", "MACA"]
    prec, rec, f1, sup = precision_recall_fscore_support(y_target, oof_preds, average=None)
    f2_scores = fbeta_score(y_target, oof_preds, beta=2, average=None)

    pr_aucs = []
    y_true_bin = pd.get_dummies(y_target).reindex(columns=[0, 1, 2], fill_value=0).values
    for i in range(3):
        precision_curve, recall_curve, _ = precision_recall_curve(y_true_bin[:, i], oof_probs[:, i])
        pr_aucs.append(auc(recall_curve, precision_curve))

    brier_scores = []
    for i in range(3):
        brier_scores.append(brier_score_loss(y_true_bin[:, i], oof_probs[:, i]))

    df_metrics = pd.DataFrame({
        "Precisió": prec,
        "Recall": rec,
        "F1-Score": f1,
        "F2-Score": f2_scores,
        "PR-AUC": pr_aucs,
        "Brier Score (Calibratge)": brier_scores,
        "Suport": sup
    }, index=target_names)

    macro_prec = np.mean(prec)
    macro_rec = np.mean(rec)
    macro_f1 = np.mean(f1)
    macro_f2 = np.mean(f2_scores)

    cm = confusion_matrix(y_target, oof_preds)
    df_cm = pd.DataFrame(cm, index=target_names, columns=["Pred_NO", "Pred_PCC", "Pred_MACA"])
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100
    df_cm_norm = pd.DataFrame(cm_norm, index=target_names, columns=["Pred_NO", "Pred_PCC", "Pred_MACA"])

    eval_output = f"""
==================================================
AVALUACIÓ REALISTA (NESTED CROSS-VALIDATION OOF)
==================================================

1. MÈTRIQUES PER CLASSE:
{df_metrics.round(4).to_string()}

----------------------------------------
2. MITJANES GENERALS (MACRO AVG):
----------------------------------------
Macro avg Precision: {macro_prec:.4f}
Macro avg Recall   : {macro_rec:.4f}
Macro avg F1-Score : {macro_f1:.4f}
Macro avg F2-Score : {macro_f2:.4f}

----------------------------------------
3. MATRIU DE CONFUSIÓ (ABSOLUTA):
----------------------------------------
{df_cm.to_string()}

----------------------------------------
4. MATRIU DE CONFUSIÓ NORMALITZADA (% SENSIVILITAT):
----------------------------------------
{df_cm_norm.apply(lambda x: x.map(lambda y: f"{y:.2f} %")).to_string()}
"""
    print(eval_output, flush=True)

    # Final Parameter Search
    print("\n--- Cerca de Paràmetres Finals per a l'Estat 1 (Random Forest) ---", flush=True)
    y1_all = (df["target"] > 0).astype(int)
    model1_final_search = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(n_estimators=100, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=1))
    ])
    grid_search1 = GridSearchCV(
        estimator=model1_final_search,
        param_grid=model1_params,
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE),
        scoring=make_scorer(recall_score, pos_label=1),
        n_jobs=-1
    )
    grid_search1.fit(X_all, y1_all)
    best_params1 = grid_search1.best_params_
    print("Millors paràmetres de l'Estat 1 (Random Forest):", best_params1, flush=True)

    print("\n--- Cerca de Paràmetres Finals per a l'Estat 2 (HistGradientBoosting) ---", flush=True)
    df_chronic = df[df["target"] > 0].copy()
    X2_all = df_chronic.drop(columns=[c for c in drop_cols if c in df_chronic.columns]).copy()
    y2_all = df_chronic["target"].copy()

    base_model2_search = HistGradientBoostingClassifier(class_weight="balanced", random_state=RANDOM_STATE)
    model2_final_search = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", CalibratedClassifierCV(estimator=base_model2_search, cv=3))
    ])
    grid_search2 = GridSearchCV(
        estimator=model2_final_search,
        param_grid=model2_params,
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE),
        scoring=make_scorer(recall_score, pos_label=2),
        n_jobs=-1
    )
    grid_search2.fit(X2_all, y2_all)
    best_params2 = grid_search2.best_params_
    print("Millors paràmetres de l'Estat 2 (HistGradientBoosting):", best_params2, flush=True)

    # Final Model Training
    print("\n--- Entrenant i desant els models finals de producció (100% de les dades) ---", flush=True)
    best_max_depth1 = best_params1["classifier__max_depth"]
    best_min_samples_leaf1 = best_params1["classifier__min_samples_leaf"]

    final_model1 = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(
            n_estimators=300,
            max_depth=best_max_depth1,
            min_samples_leaf=best_min_samples_leaf1,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1
        ))
    ])
    final_model1.fit(X_all, y1_all)
    print("Estat 1 entrenat correctament amb tot el dataset. ✅", flush=True)

    best_max_depth2 = best_params2["classifier__estimator__max_depth"]
    best_lr2 = best_params2["classifier__estimator__learning_rate"]

    final_base_model2 = HistGradientBoostingClassifier(
        max_iter=400,
        max_depth=best_max_depth2,
        learning_rate=best_lr2,
        class_weight="balanced",
        random_state=RANDOM_STATE
    )
    final_model2 = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", CalibratedClassifierCV(estimator=final_base_model2, cv=3))
    ])
    final_model2.fit(X2_all, y2_all)
    print("Estat 2 entrenat correctament amb tot el dataset de pacients crònics. ✅", flush=True)

    os.makedirs("models", exist_ok=True)
    joblib.dump(final_model1, MODEL_S1_PATH)
    joblib.dump(final_model2, MODEL_S2_PATH)
    print(f"Model Stage 1 desat a: {MODEL_S1_PATH}", flush=True)
    print(f"Model Stage 2 desat a: {MODEL_S2_PATH}", flush=True)

    print("\n--- Generant prediccions per a tot el dataset final ---", flush=True)
    full_df = pd.read_csv(DATA_PATH)
    drop_full_cols = ["id_pacient", "target", "cronic", "cronic_encoded", "sexe_encoded", "situacio_encoded", "edat_encoded", "prediccio_estat", "prob_maca", "prob_pcc"]
    X_full = full_df.drop(columns=[c for c in drop_full_cols if c in full_df.columns], errors='ignore').copy()

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
    print(f"Prediccions afegides a {DATA_PATH} correctament!", flush=True)
    print("\n🎉 Tot el procés ha finalitzat correctament!", flush=True)

    # Now update the notebook files
    with open("trainIA_V3.ipynb", "r", encoding="utf-8") as f:
        nb = json.load(f)

    # Cell 4 output
    nb["cells"][3]["outputs"] = [{
        "name": "stdout",
        "output_type": "stream",
        "text": nested_cv_output_lines
    }]

    # Cell 5 output
    nb["cells"][4]["outputs"] = [{
        "name": "stdout",
        "output_type": "stream",
        "text": [eval_output]
    }]

    # Cell 7 output
    final_search_lines = [
        "\n--- Cerca de Paràmetres Finals per a l'Estat 1 (Random Forest) ---\n",
        f"Millors paràmetres de l'Estat 1 (Random Forest): {best_params1}\n\n",
        "--- Cerca de Paràmetres Finals per a l'Estat 2 (HistGradientBoosting) ---\n",
        f"Millors paràmetres de l'Estat 2 (HistGradientBoosting): {best_params2}\n"
    ]
    nb["cells"][6]["outputs"] = [{
        "name": "stdout",
        "output_type": "stream",
        "text": final_search_lines
    }]

    # Cell 8 output
    cell8_lines = [
        "\n--- Entrenant i desant els models finals de producció (100% de les dades) ---\n",
        "Estat 1 entrenat correctament amb tot el dataset. ✅\n",
        "Estat 2 entrenat correctament amb tot el dataset de pacients crònics. ✅\n",
        f"Model Stage 1 desat a: {MODEL_S1_PATH}\n",
        f"Model Stage 2 desat a: {MODEL_S2_PATH}\n\n",
        "--- Generant prediccions per a tot el dataset final ---\n",
        f"Prediccions afegides a {DATA_PATH} correctament!\n\n",
        "🎉 Tot el procés ha finalitzat correctament!\n"
    ]
    nb["cells"][7]["outputs"] = [{
        "name": "stdout",
        "output_type": "stream",
        "text": cell8_lines
    }]

    with open("trainIA_V3.ipynb", "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        f.write("\n")

    os.chdir(r"c:\Users\1516m\Desktop\UNI\GEI\4t\2Q\TFG")
    shutil.copy("Codi_Projecte/ai/trainIA_V3.ipynb", "Principals/trainIA_V3.ipynb")
    print("Notebooks actualitzats amb èxit!", flush=True)

if __name__ == "__main__":
    main()
