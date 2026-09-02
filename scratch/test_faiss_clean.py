import pickle, os, sqlite3, faiss
import pandas as pd, numpy as np

BASE_DIR = 'Codi_Projecte/ai'
FAISS_PKL = os.path.join(BASE_DIR, 'models', 'faiss_data.pkl')
DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed', 'clinic_data.sqlite')

with open(FAISS_PKL, 'rb') as f:
    faiss_data = pickle.load(f)

index = faiss.deserialize_index(faiss_data['index'])
scaler = faiss_data['scaler']
train_ids = faiss_data['train_ids']
feature_cols = faiss_data['features']
encoders = faiss_data['encoders']

conn = sqlite3.connect(DB_PATH)
df_maca = pd.read_sql_query("SELECT * FROM dataset_final_pcc WHERE cronic = 'MACA' LIMIT 3", conn)
df_pcc = pd.read_sql_query("SELECT * FROM dataset_final_pcc WHERE cronic = 'PCC' LIMIT 3", conn)
conn.close()

def encode_patient(pacient_series):
    row = pd.DataFrame([pacient_series])
    row['sexe_encoded'] = row['sexe'].map(encoders['sexe']).fillna(0).astype(int)
    row['edat_encoded'] = row['grup_edat'].map(encoders['grup_edat']).fillna(3).astype(int)
    for col in feature_cols:
        if col not in row.columns: row[col] = 0
    X = row[feature_cols].fillna(0).values.astype(np.float32)
    X_norm = np.ascontiguousarray(scaler.transform(X), dtype=np.float32)
    faiss.normalize_L2(X_norm)
    return X_norm

print("--- Test MACA patients ---")
for _, p in df_maca.iterrows():
    pid = p['id_pacient']
    X_norm = encode_patient(p)
    distances, indices = index.search(X_norm, 5)
    matched_pids = [int(train_ids[idx]) for idx in indices[0]]
    dists = [round(float(d), 4) for d in distances[0]]
    print(f"MACA Patient {pid} -> top 5 matches: {matched_pids}, dists: {dists}")

print("\n--- Test PCC patients ---")
for _, p in df_pcc.iterrows():
    pid = p['id_pacient']
    X_norm = encode_patient(p)
    distances, indices = index.search(X_norm, 5)
    matched_pids = [int(train_ids[idx]) for idx in indices[0]]
    dists = [round(float(d), 4) for d in distances[0]]
    print(f"PCC Patient {pid} -> top 5 matches: {matched_pids}, dists: {dists}")
