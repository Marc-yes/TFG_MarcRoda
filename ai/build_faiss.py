#!/usr/bin/env python3
"""
Construeix un índex FAISS amb split train/test (75/25).
  - Train (75%) → va a l'índex FAISS (pacients "coneguts")
  - Test (25%) → es guarden apart (pacients per "predir")

Genera: faiss_data.pkl (tot en un sol fitxer)
"""

import pandas as pd
import numpy as np
import faiss
import pickle
import os
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# ── Carregar ─────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "processed", "dataset_final_pcc.csv")
df = pd.read_csv(DATA_PATH)
print(f"Carregat: {df.shape[0]} pacients, {df.shape[1]} columnes")

# ── Split 75/25 ──────────────────────────────────────────────────
df_train, df_test = train_test_split(df, test_size=0.25, random_state=42)
print(f"Train: {len(df_train)} pacients | Test: {len(df_test)} pacients")

# ── Codificar categòriques ───────────────────────────────────────
ENCODERS = {
    "sexe": {"H": 1, "D": 0},
    "grup_edat": {"65-70": 0, "70-75": 1, "75-80": 2, "80-85": 3, "85-90": 4, "90>": 5},
}

def encode(dataframe):
    d = dataframe.copy()
    d["sexe_encoded"] = d["sexe"].map(ENCODERS["sexe"]).fillna(0).astype(int)
    d["edat_encoded"] = d["grup_edat"].map(ENCODERS["grup_edat"]).fillna(3).astype(int)
    return d

df_train = encode(df_train)
df_test = encode(df_test)

# feature_cols són totes les columnes clíniques excepte identificadors, variables objectiu i text
skip = {
    "id_pacient", "target", "cronic", "cronic_encoded", 
    "sexe", "grup_edat", "prediccio_estat", "prob_maca", "prob_pcc"
}
feature_cols = [c for c in df_train.columns if c not in skip]

# ── Normalitzar TRAIN ────────────────────────────────────────────
X_train = df_train[feature_cols].fillna(0).values.astype(np.float32)
scaler = StandardScaler()
X_train_norm = np.ascontiguousarray(scaler.fit_transform(X_train), dtype=np.float32)
faiss.normalize_L2(X_train_norm)

# ── Crear índex FAISS (només train) ──────────────────────────────
index = faiss.IndexFlatIP(X_train_norm.shape[1])
index.add(X_train_norm)
print(f"Índex FAISS: {index.ntotal} vectors (train), dim={X_train_norm.shape[1]}")

# ── Guardar ──────────────────────────────────────────────────────
data = {
    "index": faiss.serialize_index(index),
    "scaler": scaler,
    "train_ids": df_train["id_pacient"].values.tolist(),
    "test_ids": df_test["id_pacient"].values.tolist(),
    "features": feature_cols,
    "encoders": ENCODERS,
}
OUTPUT_PATH = os.path.join(BASE_DIR, "models", "faiss_data.pkl")
with open(OUTPUT_PATH, "wb") as f:
    pickle.dump(data, f)

print(f"\nGuardat: {OUTPUT_PATH}")
print(f"   Train IDs: {len(data['train_ids'])} | Test IDs: {len(data['test_ids'])}")
print(f"   Test IDs exemple: {data['test_ids'][:10]}")
