#!/usr/bin/env python3
import os
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "dataset_final_pcc.csv")
df = pd.read_csv(DATA_PATH)

drop_cols = ["id_pacient", "target", "cronic", "prediccio_estat", "prob_maca", "prob_pcc", "cronic_encoded", "sexe_encoded", "situacio_encoded", "edat_encoded"]
X = df.drop(columns=[c for c in drop_cols if c in df.columns]).copy()

# Old Preprocessor (2 branches: all num with median)
num_cols = X.select_dtypes(include=["int64", "float64"]).columns.tolist()
cat_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()

old_preprocessor = ColumnTransformer(
    transformers=[
        ("num", Pipeline(steps=[("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), num_cols),
        ("cat", Pipeline(steps=[("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), cat_cols),
    ]
)

# New Preprocessor (3 branches: counts with constant 0, labs with median, cat with most_frequent)
lab_cols = [c for c in X.columns if any(c.endswith(s) for s in ["_mean", "_slope"])]
count_cols = [c for c in X.select_dtypes(include=["int64", "float64"]).columns if c not in lab_cols]

new_preprocessor = ColumnTransformer(
    transformers=[
        ("counts", Pipeline(steps=[("imputer", SimpleImputer(strategy="constant", fill_value=0)), ("scaler", StandardScaler())]), count_cols),
        ("labs", Pipeline(steps=[("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), lab_cols),
        ("cat", Pipeline(steps=[("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), cat_cols),
    ]
)

X_old = old_preprocessor.fit_transform(X)
X_new = new_preprocessor.fit_transform(X)

print(f"X_old shape: {X_old.shape}")
print(f"X_new shape: {X_new.shape}")

# Note: column ordering in ColumnTransformer matches the order of transformers:
# Old has [num_cols, cat_cols]
# New has [count_cols, lab_cols, cat_cols]
# Because num_cols was [count_cols + lab_cols], the set of features is identical, only the column order within numeric features might differ.

# Let's map feature names and compare values column by column
old_names = old_preprocessor.get_feature_names_out()
new_names = new_preprocessor.get_feature_names_out()

import re
old_clean = [re.sub(r'^[a-zA-Z0-9_]+__', '', f) for f in old_names]
new_clean = [re.sub(r'^[a-zA-Z0-9_]+__', '', f) for f in new_names]

df_old = pd.DataFrame(X_old, columns=old_clean)
df_new = pd.DataFrame(X_new, columns=new_clean)

# Reorder df_new to match df_old
df_new_reordered = df_new[old_clean]

for col in old_clean:
    diff = np.max(np.abs(df_old[col].values - df_new[col].values))
    if diff > 1e-5:
        # Check what the median was in old vs 0 in new
        old_med = df[col].median()
        null_count = df[col].isnull().sum()
        print(f"Column '{col}' differs! Max diff: {diff:.4f} | Old median: {old_med} | Null count: {null_count}")
