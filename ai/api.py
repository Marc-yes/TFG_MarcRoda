#!/usr/bin/env python3
"""
API Flask per al Portal Sanitari (Versió 4.1 - Fix de Seguretat i Independència).
- Predicció V3: Autoritat matemàtica.
- FAISS: Evidència històrica.
- Ollama: Segona opinió clínica (Independent).
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import faiss
import numpy as np
import pandas as pd
import requests as http_requests
import joblib
import os
import re
import time
import shap

app = Flask(__name__)
CORS(app)

# ── CONFIGURACIÓ DE RUTES ────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_CSV = os.path.join(BASE_DIR, "..", "data", "processed", "dataset_final_pcc.csv")
FAISS_PKL = os.path.join(BASE_DIR, "..", "data", "processed", "faiss_data.pkl")
MODEL_S1_PATH = os.path.join(BASE_DIR, "..", "data", "processed", "model_stage1_v3.joblib")
MODEL_S2_PATH = os.path.join(BASE_DIR, "..", "data", "processed", "model_stage2_v3.joblib")

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3:1b"

# ── CÀRREGA DE RECURSOS ──────────────────────────────────────────
print("🧠 Carregant motors d'intel·ligència artificial...")

try:
    with open(FAISS_PKL, "rb") as f:
        faiss_data = pickle.load(f)
    index = faiss.deserialize_index(faiss_data["index"])
    scaler = faiss_data["scaler"]
    train_ids = faiss_data["train_ids"]
    test_ids = faiss_data["test_ids"]
    feature_cols = faiss_data["features"]
    encoders = faiss_data["encoders"]

    model_v3_s1 = joblib.load(MODEL_S1_PATH)
    model_v3_s2 = joblib.load(MODEL_S2_PATH)

    df = pd.read_csv(DATA_CSV)
    if "situacio" not in df.columns:
        df["situacio"] = "A"
    df_indexed = df.set_index("id_pacient")
    
    print("🔮 Inicialitzant explicadors SHAP...")
    explainer_s1 = shap.TreeExplainer(model_v3_s1.named_steps["classifier"])
    classifier_s2_base = model_v3_s2.named_steps["classifier"].calibrated_classifiers_[0].estimator
    explainer_s2 = shap.TreeExplainer(classifier_s2_base)
    
    print("✅ Sistema llest i explicadors SHAP inicialitzats.")
except Exception as e:
    print(f"❌ ERROR CRÍTIC: {e}")
    exit(1)

# ── FUNCIONS AUXILIARS ───────────────────────────────────────────

def safe_int(val):
    return 0 if pd.isna(val) else int(val)

def netejar_text(text):
    return text.replace('*', '').replace('#', '').strip()

def fer_prediccio_v3(pacient_series):
    # 1. Convertim en DataFrame (el Pipeline necessita noms de columnes)
    row_df = pd.DataFrame([pacient_series])
    
    # 2. SELECCIÓ DE COLUMNES: Molt important!
    # El Pipeline (ColumnTransformer) espera trobar exactament les columnes 'sexe', 'grup_edat', etc.
    # NO li passis 'sexe_encoded', ell vol 'sexe' (text).
    
    # Columnes que hem de treure perquè no s'han usat en el .fit()
    drop_cols = ["id_pacient", "target", "cronic", "cronic_encoded", "sexe_encoded", "situacio_encoded", "edat_encoded"]
    X = row_df.drop(columns=[c for c in drop_cols if c in row_df.columns], errors='ignore')

    try:
        # 3. PREDICCIÓ STAGE 1
        # Passem el DataFrame X directament. El preprocessor intern farà la màgia.
        probs_s1 = model_v3_s1.predict_proba(X)[0]
        prob_no = float(probs_s1[0])
        prob_chronic = float(probs_s1[1])
        
        # Llindar de 0.5 per a la demo (més equilibrat)
        if prob_chronic < 0.50:
            return "NO", prob_no
        
        # 4. PREDICCIÓ STAGE 2
        probs_s2 = model_v3_s2.predict_proba(X)[0]
        # En el teu script V3: 0=PCC (target 1), 1=MACA (target 2)
        prob_pcc = float(probs_s2[0])
        prob_maca = float(probs_s2[1])
        
        if prob_maca >= 0.40:
            return "MACA", prob_maca
        else:
            return "PCC", prob_pcc
            
    except Exception as e:
        print(f"DEBUG Error: {e}")
        return "ERROR", str(e)

def calcular_explicabilitat_shap(pacient_series):
    try:
        row_df = pd.DataFrame([pacient_series])
        drop_cols = ["id_pacient", "target", "cronic", "cronic_encoded", "sexe_encoded", "situacio_encoded", "edat_encoded"]
        X = row_df.drop(columns=[c for c in drop_cols if c in row_df.columns], errors='ignore')
        
        preprocessor = model_v3_s1.named_steps["preprocessor"]
        X_trans = preprocessor.transform(X)
        feature_names = list(preprocessor.get_feature_names_out())
        
        # Netejar prefixos de variables
        clean_feature_names = [f.replace("num__", "").replace("cat__", "") for f in feature_names]
        
        # 1. SHAP Stage 1 (Crònic vs NO)
        shap_values_s1 = explainer_s1.shap_values(X_trans)
        if isinstance(shap_values_s1, list):
            values_s1 = shap_values_s1[1][0]
        elif len(shap_values_s1.shape) == 3:
            values_s1 = shap_values_s1[0, :, 1]
        elif len(shap_values_s1.shape) == 2 and shap_values_s1.shape[0] == 1:
            values_s1 = shap_values_s1[0]
        else:
            values_s1 = shap_values_s1
            
        contributions_s1 = []
        for col, val in zip(clean_feature_names, values_s1):
            if abs(val) > 1e-5:
                contributions_s1.append({
                    "variable": col,
                    "valor_original": str(row_df[col.split("_")[0]].values[0]) if col.split("_")[0] in row_df.columns else None,
                    "shap_value": round(float(val), 5)
                })
        contributions_s1 = sorted(contributions_s1, key=lambda x: abs(x["shap_value"]), reverse=True)
        
        # 2. SHAP Stage 2 (MACA vs PCC)
        shap_values_s2 = explainer_s2.shap_values(X_trans)
        if isinstance(shap_values_s2, list):
            values_s2 = shap_values_s2[1][0]
        elif len(shap_values_s2.shape) == 3:
            values_s2 = shap_values_s2[0, :, 1]
        elif len(shap_values_s2.shape) == 2 and shap_values_s2.shape[0] == 1:
            values_s2 = shap_values_s2[0]
        else:
            values_s2 = shap_values_s2
            
        contributions_s2 = []
        for col, val in zip(clean_feature_names, values_s2):
            if abs(val) > 1e-5:
                contributions_s2.append({
                    "variable": col,
                    "valor_original": str(row_df[col.split("_")[0]].values[0]) if col.split("_")[0] in row_df.columns else None,
                    "shap_value": round(float(val), 5)
                })
        contributions_s2 = sorted(contributions_s2, key=lambda x: abs(x["shap_value"]), reverse=True)
        
        return {
            "stage1_chronic_vs_no": contributions_s1[:10],
            "stage2_maca_vs_pcc": contributions_s2[:10]
        }
    except Exception as e:
        print(f"⚠️ Error calculant SHAP: {e}")
        return {
            "error": str(e),
            "stage1_chronic_vs_no": [],
            "stage2_maca_vs_pcc": []
        }

# Mètode per a codificar les dades categòriques del pacient, i normalitzar les numèriques
def encode_patient(pacient_series):
    row = pd.DataFrame([pacient_series])
    row["sexe_encoded"] = row["sexe"].map(encoders["sexe"]).fillna(0).astype(int)
    row["cronic_encoded"] = row["cronic"].map(encoders["cronic"]).fillna(0).astype(int)
    row["edat_encoded"] = row["grup_edat"].map(encoders["grup_edat"]).fillna(3).astype(int)
    for col in feature_cols:
        if col not in row.columns: row[col] = 0
    X = row[feature_cols].fillna(0).values.astype(np.float32)
    X_norm = np.ascontiguousarray(scaler.transform(X), dtype=np.float32)
    faiss.normalize_L2(X_norm)
    return X_norm

def buscar_similars(id_pacient, k=10):
    pacient = df_indexed.loc[id_pacient]
    X_norm = encode_patient(pacient)
    distances, indices = index.search(X_norm, k)
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        pid = train_ids[idx]
        p = df_indexed.loc[pid]
        results.append({
            "id_pacient": int(pid),
            "similitud": round(float(dist), 4),
            "cronic": str(p["cronic"]),
            "situacio": str(p["situacio"]),
            "diags_totals": safe_int(p.get("diags_totals", 0)),
            "farmacs_totals": safe_int(p.get("farmacs_totals", 0)),
            "urg_total_visites": safe_int(p.get("urg_total_visites", 0)),
            "hosp_total_visites": safe_int(p.get("hosp_total_visites", 0))
        })
    return results

# ── INFORME CLÍNIC SENSE BIAIX ───────────────────────────────────

def generar_informe(context):
    """
    Usem un prompt més tècnic i asèptic per evitar bloquejos de seguretat
    relacionats amb temes de final de vida.
    """
    prompt = f"""Ets un sistema d'anàlisi de dades per a suport a la gestió clínica (CDSS).
Analitza aquest cas de cronicitat complexa basant-te en dades biomèdiques.

PACIENT: {context['grup_edat']} anys, {context['diags_totals']} patologies, {context['farmacs_totals']} fàrmacs.
DADES DE GRUP (FAISS):
- Estabilitat: {context['pct_no']}%
- Complexitat (PCC): {context['pct_pcc']}%
- Avançat (MACA): {context['pct_maca']}%
- Risc de mortalitat històrica: {context['pct_mort_veins']}%

INSTRUCCIONS TÈCNIQUES:
1. CLASSIFICACIÓ RECOMANADA: (NO/PCC/MACA).
2. ARGUMENTACIÓ: Justifica segons la càrrega de malaltia i els casos similars.
3. PROGNOSI: Si és MACA, calcula l'estimació de supervivència estadística (en dies) basada en el {context['pct_mort_veins']}% de mortalitat del grup. Si no, indica 'Estable'.
4. ACCIÓ: Suggeriment pel metge.

Respon en CATALÀ, format professional i directe. No incloguis advertències sobre suïcidi, és una anàlisi clínica de dades històriques."""

    start_time = time.time()

    try:
        resp = http_requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL, 
                "prompt": prompt, 
                "stream": False,
                "options": {"num_predict": 250, "temperature": 0}
            },
            timeout=120
        )
        elapsed = time.time() - start_time
        print(f"⏱️ [generar_informe] Ollama ha trigat {elapsed:.2f} segons.")
        return netejar_text(resp.json()["response"]), elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ [generar_informe] Error després de {elapsed:.2f} segons: {e}")
        return f"Error en el raonament independent: {str(e)}", elapsed

# ── ENDPOINTS ────────────────────────────────────────────────────

@app.route("/api/analyze", methods=["POST"])
def analyze():
    body = request.get_json() or {}
    id_pacient = body.get("id_pacient")
    if not id_pacient:
        return jsonify({"error": "Cal id_pacient"}), 400
    
    id_pacient = int(id_pacient)
    if id_pacient not in df_indexed.index:
        return jsonify({"error": "Pacient no trobat"}), 404

    pacient_series = df_indexed.loc[id_pacient]
    pred_v3, conf_v3 = fer_prediccio_v3(pacient_series)
    veins = buscar_similars(id_pacient, k=10)
    cronics_veins = [v["cronic"] for v in veins]

    context = {
        "id_pacient": id_pacient,
        "grup_edat": str(pacient_series["grup_edat"]),
        "sexe": str(pacient_series["sexe"]),
        "cronic_actual": str(pacient_series["cronic"]),
        "diags_totals": safe_int(pacient_series.get("diags_totals", 0)),
        "farmacs_totals": safe_int(pacient_series.get("farmacs_totals", 0)),
        "n_veins": len(veins),
        "pct_pcc": round(cronics_veins.count("PCC") / len(veins) * 100),
        "pct_maca": round(cronics_veins.count("MACA") / len(veins) * 100),
        "pct_no": round(cronics_veins.count("NO") / len(veins) * 100),
        "pct_mort_veins": round(sum(1 for v in veins if v["situacio"] == "D") / len(veins) * 100)
    }

    informe_final, temps_ollama = generar_informe(context)
    
    explicacio_shap = calcular_explicabilitat_shap(pacient_series)

    return jsonify({
        "pacient": context,
        "prediccio_v3": {
            "resultat": pred_v3,
            "confianca": round(float(conf_v3), 4) if isinstance(conf_v3, (int, float)) else conf_v3
        },
        "veins_similars": veins,
        "informe": informe_final,
        "explicabilitat_shap": explicacio_shap,
        "temps_generacio_segons": round(temps_ollama, 2)
    })

@app.route("/api/pacient-info", methods=["POST"])
def pacient_info():
    body = request.get_json() or {}
    id_pacient = body.get("id_pacient")
    if not id_pacient:
        return jsonify({"error": "Cal id_pacient"}), 400
        
    id_pacient = int(id_pacient)
    if id_pacient not in df_indexed.index:
        return jsonify({"error": "Pacient no trobat"}), 404

    pacient_series = df_indexed.loc[id_pacient]
    veins = buscar_similars(id_pacient, k=10)
    
    # Calcular la mitjana del grup (veïns similars)
    mitjana_farmacs = sum([v.get("farmacs_totals", 0) for v in veins]) / len(veins)
    mitjana_diags = sum([v.get("diags_totals", 0) for v in veins]) / len(veins)
    mitjana_urg = sum([v.get("urg_total_visites", 0) for v in veins]) / len(veins)
    mitjana_hosp = sum([v.get("hosp_total_visites", 0) for v in veins]) / len(veins)

    context = {
        "grup_edat": str(pacient_series["grup_edat"]),
        "situacio": str(pacient_series.get("situacio", "A")),
        "diags_totals": safe_int(pacient_series.get("diags_totals", 0)),
        "farmacs_totals": safe_int(pacient_series.get("farmacs_totals", 0)),
        "urg_totals": safe_int(pacient_series.get("urg_total_visites", 0)),
        "hosp_totals": safe_int(pacient_series.get("hosp_total_visites", 0)),
        "mitjana_grup_farmacs": round(mitjana_farmacs, 2),
        "mitjana_grup_diags": round(mitjana_diags, 2),
        "mitjana_grup_urg": round(mitjana_urg, 2),
        "mitjana_grup_hosp": round(mitjana_hosp, 2)
    }

    prompt = f"""Ets un assistent de salut intel·ligent, empàtic i clar. 
Estàs parlant directament amb un pacient d'entre {context['grup_edat']} anys. 
DADES CLÍNIQUES (no les repeteixis directament com a dades fredes):
- Té {context['diags_totals']} patologies cròniques (la mitjana del seu grup és {context['mitjana_grup_diags']}).
- Pren {context['farmacs_totals']} fàrmacs diaris (la mitjana del seu grup és {context['mitjana_grup_farmacs']}).

INSTRUCCIONS:
Escriu 3 consells pràctics i motivadors per ajudar-lo a cuidar-se i seguir bé la seva medicació, tenint en compte breument si està per sobre o sota la mitjana (amb to amable i optimista).
Ha de ser un missatge curt (màxim de 4 o 5 frases en total), càlid i esperançador. No utilitzis la paraula pacient, parla-li de tu.
No parlis de metges, estadístiques complexes ni riscos."""
    
    start_time = time.time()
    
    try:
        resp = http_requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL, 
                "prompt": prompt, 
                "stream": False,
                "options": {"temperature": 0.4}
            },
            timeout=120
        )
        consells = netejar_text(resp.json()["response"])
        elapsed = time.time() - start_time
        print(f"⏱️ [/api/pacient-info] Ollama ha trigat {elapsed:.2f} segons.")
    except Exception as e:
        consells = "T'animem a mantenir hàbits saludables, passejar una mica cada dia, i seguir puntualment la teva medicació."
        elapsed = time.time() - start_time
        print(f"❌ [/api/pacient-info] Error després de {elapsed:.2f} segons: {e}")

    return jsonify({
        "pacient": context,
        "consells": consells,
        "temps_generacio_segons": round(elapsed, 2)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
    ##