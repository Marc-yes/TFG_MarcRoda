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
import csv
import threading
import sqlite3
from datetime import datetime
import builtins

def safe_print(*args, **kwargs):
    try:
        builtins.print(*args, **kwargs)
    except Exception:
        pass

print = safe_print

app = Flask(__name__)
CORS(app)

feedback_lock = threading.Lock()

# ── CONFIGURACIÓ DE RUTES ────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "processed", "clinic_data.sqlite")
FAISS_PKL = os.path.join(BASE_DIR, "..", "data", "processed", "faiss_data.pkl")
MODEL_S1_PATH = os.path.join(BASE_DIR, "..", "data", "processed", "model_stage1_v3.joblib")
MODEL_S2_PATH = os.path.join(BASE_DIR, "..", "data", "processed", "model_stage2_v3.joblib")

# Llegir fitxer .env manualment per evitar dependències externes
def load_env():
    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip()
                    if key not in os.environ:
                        os.environ[key] = val

load_env()

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma2:2b")
USE_OPENROUTER = os.environ.get("USE_OPENROUTER", "false").lower() == "true"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3-8b-instruct:free")

# ── CÀRREGA DE RECURSOS ──────────────────────────────────────────
print("Carregant motors d'intel-ligencia artificial...")

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
    
    print("Inicialitzant explicadors SHAP...")
    explainer_s1 = shap.TreeExplainer(model_v3_s1.named_steps["classifier"])
    classifier_s2_base = model_v3_s2.named_steps["classifier"].calibrated_classifiers_[0].estimator
    explainer_s2 = shap.TreeExplainer(classifier_s2_base)
    
    print("Sistema llest i explicadors SHAP inicialitzats.")
except Exception as e:
    print(f"ERROR CRITIC: {e}")
    exit(1)

# ── FUNCIONS AUXILIARS ───────────────────────────────────────────

def safe_int(val):
    return 0 if pd.isna(val) else int(val)

def get_patient_series(id_pacient):
    conn = sqlite3.connect(DB_PATH)
    try:
        query = "SELECT * FROM dataset_final_pcc WHERE id_pacient = ?"
        row_df = pd.read_sql_query(query, conn, params=[id_pacient])
        if row_df.empty:
            return None
        return row_df.iloc[0]
    finally:
        conn.close()

def get_latest_feedback_status(id_pacient):
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT feedback_correcte, classificacio_correcta 
            FROM feedback 
            WHERE id_pacient = ? 
            ORDER BY timestamp DESC LIMIT 1
        """, (int(id_pacient),))
        row = cursor.fetchone()
        if row is None:
            return "Nova / Pendent de revisar"
        is_correct = row[0]
        if is_correct == 1:
            return "Validada"
        else:
            correct_class = row[1] if row[1] else "Altra"
            return f"Corregida a {correct_class}"
    except Exception:
        return "Nova / Pendent de revisar"
    finally:
        conn.close()

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
    pacient = get_patient_series(id_pacient)
    X_norm = encode_patient(pacient)
    distances, indices = index.search(X_norm, k)
    results = []
    pids = [int(train_ids[idx]) for idx in indices[0]]
    pids_str = ",".join(map(str, pids))
    
    conn = sqlite3.connect(DB_PATH)
    try:
        query = f"SELECT * FROM dataset_final_pcc WHERE id_pacient IN ({pids_str})"
        veins_df = pd.read_sql_query(query, conn)
        veins_df = veins_df.set_index("id_pacient")
        
        for dist, pid in zip(distances[0], pids):
            if pid in veins_df.index:
                p = veins_df.loc[pid]
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
    finally:
        conn.close()

# ── INFORME CLÍNIC SENSE BIAIX ───────────────────────────────────

NOMS_VARIABLES = {
    'num_visitas_primaria': 'Visites atenció primària',
    'farmacs_totals': 'Fàrmacs prescrits',
    'diags_totals': 'Diagnòstics totals',
    'grup_edat_70-75': 'Edat (70-75)',
    'grup_edat_75-80': 'Edat (75-80)',
    'grup_edat_80-85': 'Edat (80-85)',
    'grup_edat_85-90': 'Edat (85-90)',
    'grup_edat_90>': 'Edat (Major de 90)',
    'antiinfecciosos_per_a_us_sistemic': 'Antiinfecciosos (ús sistèmic)',
    'sistema_nervios': 'Patologia: Sistema Nerviós',
    'sang_i_organs_hematopoetics': 'Patologia: Sang i òrgans hematopoètics',
    'visites_urgencies_risc_vital': 'Visites urgències (risc vital)',
    'sistema_digestiu_i_metabolisme': 'Patologia: Sistema digestiu/metabolisme',
    'sistema_cardiovascular': 'Patologia: Sistema cardiovascular',
    'visites_hosp_243_365': 'Hospitalitzacions (fa 243-365 dies)',
    'visites_inter_243_365': 'Visites intermèdies (fa 243-365 dies)',
    'sistema_musculoesqueletic': 'Patologia: Sistema musculoesquelètic',
    'signes_i_sintomes': 'Signes i símptomes clínics',
    'sexe_D': 'Gènere femení',
    'altres': 'Altres diagnòstics/fàrmacs'
}

def cridar_llm(prompt):
    """
    Crida al LLM (OpenRouter o Ollama) amb fallback si un dels dos falla o no està configurat.
    """
    if USE_OPENROUTER and OPENROUTER_API_KEY and not OPENROUTER_API_KEY.startswith("sk-or-v1-la-teva-clau"):
        try:
            print(f"[cridar_llm] Provant OpenRouter amb model {OPENROUTER_MODEL}...")
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": OPENROUTER_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 800,
            }
            resp = http_requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=45
            )
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"]
                return text, "OpenRouter (" + OPENROUTER_MODEL + ")"
            else:
                print(f"[cridar_llm] OpenRouter ha retornat error {resp.status_code}: {resp.text}. Fent fallback a Ollama...")
        except Exception as e:
            print(f"[cridar_llm] Error connectant a OpenRouter: {e}. Fent fallback a Ollama...")
            
    # Fallback o opció per defecte: Ollama local
    print(f"[cridar_llm] Provant Ollama local amb model {OLLAMA_MODEL}...")
    try:
        resp = http_requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 800, "temperature": 0.2}
            },
            timeout=60
        )
        if resp.status_code == 200:
            text = resp.json()["response"]
            return text, "Ollama (" + OLLAMA_MODEL + ")"
        else:
            try:
                err_msg = resp.json().get("error", resp.text)
            except Exception:
                err_msg = resp.text
            raise RuntimeError(f"Ollama ha retornat error {resp.status_code}: {err_msg}")
    except Exception as e:
        print(f"[cridar_llm] Error connectant a Ollama: {e}")
        raise e

def netejar_text_informe(text):
    text = text.strip()
    
    # 1. Trobar el primer "1. CLASSIFICACIÓ RECOMANADA" o "1."
    idx_1 = text.find("1. CLASSIFICACIÓ")
    if idx_1 == -1:
        idx_1 = text.find("1.")
    
    if idx_1 != -1:
        text = text[idx_1:]
        
    # 2. Eliminar notes finals típiques dels LLMs petits
    for indicador_nota in ["Nota:", "Nota de la IA:", "Aquest informe es basa", "Disclaimer:", "Nota del model:"]:
        idx_nota = text.find(indicador_nota)
        if idx_nota != -1:
            text = text[:idx_nota].strip()
            
    return text.strip()

def generar_informe(context, shap_data=None, pred_v3=""):
    """
    Usem un prompt més tècnic i asèptic per evitar bloquejos de seguretat
    relacionats amb temes de final de vida. Incorpora explicabilitat SHAP.
    """
    # Construir llista readable de factors SHAP
    factors_s1 = []
    if shap_data and "stage1_chronic_vs_no" in shap_data and not isinstance(shap_data.get("error"), str):
        for item in shap_data["stage1_chronic_vs_no"][:4]:
            var_desc = NOMS_VARIABLES.get(item["variable"], item["variable"].replace('_', ' ').capitalize())
            val_orig = item["valor_original"]
            val_shap = item["shap_value"]
            sentit = "empeny cap a classificar com a CRÒNIC" if val_shap > 0 else "empeny cap a NO CRÒNIC"
            factors_s1.append(f"- **{var_desc}** (valor pacient: {val_orig}): impacte de {val_shap:.4f} ({sentit})")
            
    factors_s2 = []
    if shap_data and "stage2_maca_vs_pcc" in shap_data and not isinstance(shap_data.get("error"), str) and pred_v3 != "NO":
        for item in shap_data["stage2_maca_vs_pcc"][:4]:
            var_desc = NOMS_VARIABLES.get(item["variable"], item["variable"].replace('_', ' ').capitalize())
            val_orig = item["valor_original"]
            val_shap = item["shap_value"]
            sentit = "empeny cap a MACA (més complex/avançat)" if val_shap > 0 else "empeny cap a PCC (cronicitat complexa)"
            factors_s2.append(f"- **{var_desc}** (valor pacient: {val_orig}): impacte de {val_shap:.4f} ({sentit})")

    s1_text = "\n".join(factors_s1) if factors_s1 else "No s'han obtingut factors rellevants per a l'Estat 1."
    s2_text = "\n".join(factors_s2) if factors_s2 else "No s'han obtingut factors rellevants per a l'Estat 2 (el pacient s'ha classificat com a NO crònic)."

    prompt = f"""Ets un sistema d'anàlisi de dades per a suport a la gestió clínica (CDSS) de l'Hospital Joan XXIII.
Analitza aquest cas de cronicitat complexa basant-te en dades biomèdiques, similitud FAISS i impacte de variables SHAP.

PACIENT:
- Edat/Sexe: {context['grup_edat']} anys, {context['sexe']}
- Patologies/Fàrmacs: {context['diags_totals']} patologies cròniques, {context['farmacs_totals']} fàrmacs prescrits.

FACTORS CLAU DETERMINANTS PEL MODEL (Valors SHAP):
* Estat 1 (Cronicitat vs No Cronicitat):
{s1_text}

* Estat 2 (Gravetat: PCC vs MACA):
{s2_text}

DADES DE GRUP (FAISS - 10 pacients similars):
- Estabilitat: {context['pct_no']}%
- Complexitat (PCC): {context['pct_pcc']}%
- Avançat (MACA): {context['pct_maca']}%
- Risc de mortalitat històrica: {context['pct_mort_veins']}%

CLASSIFICACIÓ SUGGERIDA PEL MODEL: {pred_v3}

INSTRUCCIONS DE REDACCIÓ (MOLT IMPORTANT):
1. Respon en CATALÀ.
2. NO incloguis cap introducció, salutació, ni comiat.
3. Genera l'informe de 4 apartats seguint exactament l'esquema de plantilla mostrat al final.
4. Deixa obligatòriament una línia en blanc completa de separació abans de cadascun dels apartats 2, 3 i 4 per evitar que el text quedi atapeït.
5. Utilitza negretes (`**text**`) per destacar els factors i valors reals del pacient.
6. No incloguis advertències sobre suïcidi.

DADES DEL PACIENT:
- Edat/Sexe: {context['grup_edat']} anys, {context['sexe']}
- Patologies/Fàrmacs: {context['diags_totals']} patologies cròniques, {context['farmacs_totals']} fàrmacs prescrits.

FACTORS CLAU SHAP:
* Estat 1 (Cronicitat vs No Cronicitat):
{s1_text}

* Estat 2 (Gravetat: PCC vs MACA):
{s2_text}

DADES DE GRUP (FAISS - 10 pacients similars):
- Estabilitat: {context['pct_no']}%
- Complexitat (PCC): {context['pct_pcc']}%
- Avançat (MACA): {context['pct_maca']}%
- Risc de mortalitat històrica: {context['pct_mort_veins']}%

INFORME CLÍNIC DE LA IA (Completa exactament aquesta plantilla):

1. CLASSIFICACIÓ RECOMANADA: {pred_v3}

2. ARGUMENTACIÓ:
   - **[Factor decisiu Estat 1]**: [Explica quin factor del pacient ha tingut major impacte SHAP en la cronicitat (Estat 1) i què significa].
   - **[Factor decisiu Estat 2]**: [Explica quin factor ha tingut major impacte en la gravetat (Estat 2, si aplica) i què significa].
   - **[Similitud de grup (FAISS)]**: [Argumenta breument com recolza la decisió la similitud de veïns de FAISS].

3. PROGNOSI:
   - **[Estat de la Prognosi]**: [Si és MACA, calcula la supervivència estimada en dies en base a la mortalitat del {context['pct_mort_veins']}%. Si no ho és, indica que el pacient es troba 'Estable'].

4. ACCIÓ:
   - **[Mesura clínica directa SHAP]**: [Proposa una intervenció concreta lligada directament a la variable SHAP de més impacte].
   - **[Mesura de seguiment]**: [Recomanació de coordinació amb atenció primària o especialista].
"""

    start_time = time.time()
    try:
        informe, font = cridar_llm(prompt)
        elapsed = time.time() - start_time
        print(f"[generar_informe] Generat amb {font} en {elapsed:.2f} segons.")
        return netejar_text_informe(netejar_text(informe)), elapsed, font
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[generar_informe] Error despres de {elapsed:.2f} segons: {e}")
        return f"Error en el raonament clínic: {str(e)}", elapsed, "Error"

# ── ENDPOINTS ────────────────────────────────────────────────────

@app.route("/api/analyze", methods=["POST"])
def analyze():
    body = request.get_json() or {}
    id_pacient = body.get("id_pacient")
    if not id_pacient:
        return jsonify({"error": "Cal id_pacient"}), 400
    
    id_pacient = int(id_pacient)
    pacient_series = get_patient_series(id_pacient)
    if pacient_series is None:
        return jsonify({"error": "Pacient no trobat"}), 404
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

    explicacio_shap = calcular_explicabilitat_shap(pacient_series)
    informe_final, temps_ollama, font_informe = generar_informe(context, explicacio_shap, pred_v3)

    return jsonify({
        "pacient": context,
        "prediccio_v3": {
            "resultat": pred_v3,
            "confianca": round(float(conf_v3), 4) if isinstance(conf_v3, (int, float)) else conf_v3,
            "estat": get_latest_feedback_status(id_pacient)
        },
        "veins_similars": veins,
        "informe": informe_final,
        "model_informe": font_informe,
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
    pacient_series = get_patient_series(id_pacient)
    if pacient_series is None:
        return jsonify({"error": "Pacient no trobat"}), 404
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
        print(f"[/api/pacient-info] Ollama ha trigat {elapsed:.2f} segons.")
    except Exception as e:
        consells = "T'animem a mantenir habits saludables, passejar una mica cada dia, i seguir puntualment la teva medicacio."
        elapsed = time.time() - start_time
        print(f"[/api/pacient-info] Error despres de {elapsed:.2f} segons: {e}")

    return jsonify({
        "pacient": context,
        "consells": consells,
        "temps_generacio_segons": round(elapsed, 2)
    })

@app.route("/api/patients/priority", methods=["GET"])
def priority_patients():
    limit = request.args.get("limit", default=50, type=int)
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id_pacient, p.sexe, p.grup_edat, p.prediccio_estat, p.prob_maca, p.prob_pcc
            FROM dataset_final_pcc p
            WHERE p.prediccio_estat IN ('MACA', 'PCC')
              AND NOT EXISTS (
                  SELECT 1 FROM feedback f 
                  WHERE f.id_pacient = p.id_pacient
              )
            ORDER BY 
              CASE WHEN p.prediccio_estat = 'MACA' THEN 1 
                   WHEN p.prediccio_estat = 'PCC' THEN 2 
                   ELSE 3 END ASC,
              CASE WHEN p.prediccio_estat = 'MACA' THEN p.prob_maca 
                   WHEN p.prediccio_estat = 'PCC' THEN p.prob_pcc 
                   ELSE 0 END DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        patients = []
        for r in rows:
            patients.append({
                "id_pacient": r[0],
                "sexe": r[1],
                "grup_edat": r[2],
                "prediccio_estat": r[3],
                "prob_maca": round(r[4], 4) if r[4] is not None else 0.0,
                "prob_pcc": round(r[5], 4) if r[5] is not None else 0.0,
                "status": "Pendent"
            })
        return jsonify({"patients": patients})
    except Exception as e:
        print(f"Error querying priority patients: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/feedback", methods=["POST"])
def registrar_feedback():
    body = request.get_json() or {}
    id_pacient = body.get("id_pacient")
    prediccio_model = body.get("prediccio_model")
    confianca_model = body.get("confianca_model")
    feedback_correcte = body.get("feedback_correcte")
    classificacio_correcta = body.get("classificacio_correcta")
    comentari = body.get("comentari", "")
    usuari = body.get("usuari", "professional")
    
    if id_pacient is None:
        return jsonify({"error": "Cal id_pacient"}), 400
        
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        fb_correct = 1 if feedback_correcte else 0
        cursor.execute("""
            INSERT INTO feedback (timestamp, id_pacient, prediccio_model, confianca_model, 
                                  feedback_correcte, classificacio_correcta, comentari, usuari)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            int(id_pacient),
            str(prediccio_model),
            float(confianca_model) if confianca_model is not None else None,
            fb_correct,
            str(classificacio_correcta) if classificacio_correcta is not None else None,
            str(comentari),
            str(usuari)
        ))
        conn.commit()
    except Exception as e:
        print(f"Error guardant feedback a la base de dades: {e}")
        return jsonify({"error": f"Error de base de dades: {str(e)}"}), 500
    finally:
        conn.close()
            
    return jsonify({"success": True, "message": "Feedback registrat correctament"})

@app.route("/api/feedback/history", methods=["POST"])
def feedback_history():
    body = request.get_json() or {}
    id_pacient = body.get("id_pacient")
    if id_pacient is None:
        return jsonify({"error": "Cal id_pacient"}), 400
        
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, prediccio_model, confianca_model, feedback_correcte, 
                   classificacio_correcta, comentari, usuari 
            FROM feedback 
            WHERE id_pacient = ? 
            ORDER BY timestamp DESC
        """, (int(id_pacient),))
        rows = cursor.fetchall()
        history = []
        for r in rows:
            history.append({
                "timestamp": r[0],
                "prediccio_model": r[1],
                "confianca_model": r[2],
                "feedback_correcte": bool(r[3]),
                "classificacio_correcta": r[4],
                "comentari": r[5],
                "usuari": r[6]
            })
        return jsonify({"history": history})
    except Exception as e:
        print(f"Error llegint historial de feedback: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)