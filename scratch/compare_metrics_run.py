#!/usr/bin/env python3
import os
import warnings
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import precision_recall_fscore_support, fbeta_score, roc_auc_score

warnings.filterwarnings("ignore")

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "dataset_final_pcc.csv")
df = pd.read_csv(DATA_PATH)

drop_cols = ["id_pacient", "target", "cronic", "prediccio_estat", "prob_maca", "prob_pcc", "cronic_encoded", "sexe_encoded", "situacio_encoded", "edat_encoded"]
X = df.drop(columns=[c for c in drop_cols if c in df.columns]).copy()
y = df["target"].values
y1 = (y > 0).astype(int)

# 1. Old Preprocessor
num_cols = X.select_dtypes(include=["int64", "float64"]).columns.tolist()
cat_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()

old_preprocessor = ColumnTransformer(
    transformers=[
        ("num", Pipeline(steps=[("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), num_cols),
        ("cat", Pipeline(steps=[("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), cat_cols),
    ]
)

# 2. New Preprocessor
lab_cols = [c for c in X.columns if any(c.endswith(s) for s in ["_mean", "_slope"])]
count_cols = [c for c in X.select_dtypes(include=["int64", "float64"]).columns if c not in lab_cols]

new_preprocessor = ColumnTransformer(
    transformers=[
        ("counts", Pipeline(steps=[("imputer", SimpleImputer(strategy="constant", fill_value=0)), ("scaler", StandardScaler())]), count_cols),
        ("labs", Pipeline(steps=[("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), lab_cols),
        ("cat", Pipeline(steps=[("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), cat_cols),
    ]
)

print("=== COMPARING METRICS ON 4-FOLD CV (STAGE 1: RANDOM FOREST) ===")

cv = StratifiedKFold(n_splits=4, shuffle=True, random_state=42)

for name, prep in [("OLD (All Median)", old_preprocessor), ("NEW (Counts Constant 0 + Labs Median)", new_preprocessor)]:
    rf = Pipeline(steps=[
        ("prep", prep),
        ("clf", RandomForestClassifier(n_estimators=100, max_depth=30, min_samples_leaf=5, class_weight="balanced", random_state=42, n_jobs=-1))
    ])
    
    recalls = []
    precisions = []
    f1s = []
    
    for train_idx, test_idx in cv.split(X, y1):
        rf.fit(X.iloc[train_idx], y1[train_idx])
        preds = rf.predict(X.iloc[test_idx])
        p, r, f, _ = precision_recall_fscore_support(y1[test_idx], preds, average="binary")
        recalls.append(r)
        precisions.append(p)
        f1s.append(f)
        
    print(f"\n{name}:")
    print(f"  Recall Crònic:    {np.mean(recalls):.4f}")
    print(f"  Precisió Crònic: {np.mean(precisions):.4f}")
    print(f"  F1-Score Crònic: {np.mean(f1s):.4f}")

print("\n=== COMPARING LOGISTIC REGRESSION BASELINE ===")
for name, prep in [("OLD (All Median)", old_preprocessor), ("NEW (Counts Constant 0 + Labs Median)", new_preprocessor)]:
    lr = Pipeline(steps=[
        ("prep", prep),
        ("clf", LogisticRegression(class_weight="balanced", max_iter=500, random_state=42))
    ])
    recalls = []
    precisions = []
    f1s = []
    for train_idx, test_idx in cv.split(X, y1):
        lr.fit(X.iloc[train_idx], y1[train_idx])
        preds = lr.predict(X.iloc[test_idx])
        p, r, f, _ = precision_recall_fscore_support(y1[test_idx], preds, average="binary")
        recalls.append(r)
        precisions.append(p)
        f1s.append(f)
    print(f"\n{name}:")
    print(f"  Recall Crònic:    {np.mean(recalls):.4f}")
    print(f"  Precisió Crònic: {np.mean(precisions):.4f}")
    print(f"  F1-Score Crònic: {np.mean(f1s):.4f}")
