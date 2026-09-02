import os
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (
    confusion_matrix, 
    precision_recall_fscore_support, 
    precision_recall_curve, 
    auc,
    fbeta_score,
    brier_score_loss
)
import warnings
warnings.filterwarnings("ignore")

DATA_PATH = "Codi_Projecte/data/processed/dataset_final_pcc.csv"
RANDOM_STATE = 42

df = pd.read_csv(DATA_PATH)
drop_cols = ["id_pacient", "target", "cronic"]
X_all = df.drop(columns=[c for c in drop_cols if c in df.columns]).copy()

num_cols = X_all.select_dtypes(include=["int64", "float64"]).columns.tolist()
cat_cols = X_all.select_dtypes(include=["object", "category"]).columns.tolist()

preprocessor = ColumnTransformer(
    transformers=[
        ("num", Pipeline(steps=[("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), num_cols),
        ("cat", Pipeline(steps=[("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), cat_cols),
    ]
)

y_target = df["target"].values
target_names = ["NO", "PCC", "MACA"]

# Validació encreuada de 4 FOLDS (idèntic a outer_cv de trainIA_V3)
CV_KFold = StratifiedKFold(n_splits=4, shuffle=True, random_state=RANDOM_STATE)

def run_cross_validation_pipeline(MODEL1, MODEL2, model_name):
    print(f"\n" + "="*60)
    print(f"AVALUACIÓ (CROSS-VALIDATION 4 FOLDS - LLINDAR 0.55) - {model_name.upper()}")
    print("="*60 + "\n")
    
    oof_preds = np.zeros(len(df))
    oof_probs = np.zeros((len(df), len(target_names)))
    
    print(f"--- Iniciant Cross-Validation ({CV_KFold.n_splits} folds) ---")
    
    for fold, (train_idx, val_idx) in enumerate(CV_KFold.split(X_all, y_target)):
        print(f"Entrenant Fold {fold + 1}/{CV_KFold.n_splits}...")
        
        X_train_fold, X_val_fold = X_all.iloc[train_idx], X_all.iloc[val_idx]
        y_train_fold = y_target[train_idx]
        
        # --- ESTAT 1: Crònic (1) vs NO (0) ---
        y1_train_fold = (y_train_fold > 0).astype(int)
        model1_fold = Pipeline(steps=[
            ("preprocessor", clone(preprocessor)),
            ("classifier", clone(MODEL1))
        ])
        model1_fold.fit(X_train_fold, y1_train_fold)
        
        # --- ESTAT 2: PCC (1) vs MACA (2) ---
        chronic_train_mask = y_train_fold > 0
        X2_train_fold = X_train_fold[chronic_train_mask]
        y2_train_fold = y_train_fold[chronic_train_mask]
        
        model2_fold = Pipeline(steps=[
            ("preprocessor", clone(preprocessor)),
            ("classifier", clone(MODEL2))
        ])
        model2_fold.fit(X2_train_fold, y2_train_fold)
        
        # --- Predicció del Fold de Validació ---
        y1_prob = model1_fold.predict_proba(X_val_fold)[:, 1]
        # LLINDAR 0.55 (Idèntic a V3)
        y1_pred = (y1_prob >= 0.55).astype(int)
        
        # Predicció dels PCC o MACA entre els crònics
        y_pred = np.zeros_like(y1_pred)
        chronic_indices = np.where(y1_pred == 1)[0]
        
        if len(chronic_indices) > 0:
            X_chronic = X_val_fold.iloc[chronic_indices]
            y2_probs = model2_fold.predict_proba(X_chronic)
            p_maca_detected = y2_probs[:, 1]
            
            THRESHOLD_MACA = 0.40
            y2_pred = np.where(p_maca_detected >= THRESHOLD_MACA, 2, 1)
            y_pred[chronic_indices] = y2_pred
            
        oof_preds[val_idx] = y_pred
        
        # Càlcul de probabilitats globals out-of-fold per a PR-AUC i Brier Score
        p_no = 1.0 - y1_prob
        p_chronic = y1_prob
        
        y2_probs_all = model2_fold.predict_proba(X_val_fold)
        p_pcc_s2 = y2_probs_all[:, 0]
        p_maca_s2 = y2_probs_all[:, 1]
        
        p_pcc_val = p_chronic * p_pcc_s2
        p_maca_val = p_chronic * p_maca_s2
        
        oof_probs[val_idx] = np.column_stack([p_no, p_pcc_val, p_maca_val])
        
    print("--- Cross-Validation finalitzada! ---\n")
    
    # --- AVALUACIÓ --- 
    prec, rec, f1, support = precision_recall_fscore_support(y_target, oof_preds, average=None, labels=[0,1,2])
    
    f2 = []
    for i in range(len(target_names)):
        y_true_bin = (y_target == i).astype(int)
        y_pred_bin = (oof_preds == i).astype(int)
        f2.append(fbeta_score(y_true_bin, y_pred_bin, beta=2))
        
    y_final_true_bin = pd.get_dummies(y_target).reindex(columns=[0, 1, 2], fill_value=0).values
    
    pr_aucs = []
    brier_scores = []
    for i in range(len(target_names)):
        precision_curve, recall_curve, _ = precision_recall_curve(y_final_true_bin[:, i], oof_probs[:, i])
        pr_aucs.append(auc(recall_curve, precision_curve))
        brier_scores.append(brier_score_loss(y_final_true_bin[:, i], oof_probs[:, i]))
        
    df_metrics = pd.DataFrame({
        "Precisió": prec,
        "Recall": rec,
        "F1-Score": f1,
        "F2-Score": f2,
        "PR-AUC": pr_aucs,
        "Brier Score (Calibratge)": brier_scores,
        "Suport": support
    }, index=target_names)
    
    print("-" * 50)
    print("1. MÈTRIQUES DETALLADES (CV):")
    print("-" * 50)
    print(df_metrics.round(4).to_string())
    
    macro_f2 = np.mean(f2)
    print("\n" + "-" * 50)
    print("2. MITJANES GENERALS (MACRO AVG - CV):")
    print("-" * 50)
    print(f"Macro avg Precision: {np.mean(prec):.4f}")
    print(f"Macro avg Recall   : {np.mean(rec):.4f}")
    print(f"Macro avg F1-Score : {np.mean(f1):.4f}")
    print(f"Macro avg F2-Score : {macro_f2:.4f}")
    
    cm = confusion_matrix(y_target, oof_preds)
    df_cm = pd.DataFrame(cm, index=target_names, columns=["Pred_NO", "Pred_PCC", "Pred_MACA"])
    print("\n" + "-" * 50)
    print("3. MATRIU DE CONFUSIÓ (ABSOLUTA - CV):")
    print("-" * 50)
    print(df_cm.to_string())
    
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    df_cm_norm = pd.DataFrame(cm_norm, index=target_names, columns=["Pred_NO", "Pred_PCC", "Pred_MACA"])
    print("\n" + "-" * 50)
    print("4. MATRIU DE CONFUSIÓ NORMALITZADA (CV):")
    print("-" * 50)
    print((df_cm_norm * 100).round(2).astype(str) + " %")

print("Executant Dummy (prior)...")
run_cross_validation_pipeline(DummyClassifier(strategy="prior"), DummyClassifier(strategy="prior"), "Dummy Classifier (prior)")

print("\nExecutant Dummy (stratified)...")
run_cross_validation_pipeline(DummyClassifier(strategy="stratified", random_state=RANDOM_STATE), DummyClassifier(strategy="stratified", random_state=RANDOM_STATE), "Dummy Classifier (stratified)")

print("\nExecutant Logistic Regression (balanced)...")
run_cross_validation_pipeline(LogisticRegression(class_weight="balanced", max_iter=1000, random_state=RANDOM_STATE), LogisticRegression(class_weight="balanced", max_iter=1000, random_state=RANDOM_STATE), "Logistic Regression (Balanced)")
