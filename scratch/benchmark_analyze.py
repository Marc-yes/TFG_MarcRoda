import os
import sys
import time
import sqlite3
import numpy as np
import pandas as pd

ai_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ai'))
sys.path.insert(0, ai_dir)
os.chdir(ai_dir)
import api

# Utilitzar Ollama local directament per evitar retards de xarxa/OpenRouter
api.USE_OPENROUTER = False

def run_benchmark(n_samples=50, test_llm_samples=5):
    print(f"=== INICIANT BENCHMARK EXPERIMENTAL DE /api/analyze ({n_samples} pacients) ===", flush=True)
    
    # 1. Obtenir IDs de pacients representatius de les 3 classes (NO, PCC, MACA)
    conn = sqlite3.connect(api.DB_PATH)
    query = """
        SELECT id_pacient, target FROM dataset_final_pcc 
        WHERE id_pacient IN (
            SELECT id_pacient FROM dataset_final_pcc WHERE target = 0 LIMIT 20
        )
        UNION ALL
        SELECT id_pacient, target FROM dataset_final_pcc 
        WHERE id_pacient IN (
            SELECT id_pacient FROM dataset_final_pcc WHERE target = 1 LIMIT 20
        )
        UNION ALL
        SELECT id_pacient, target FROM dataset_final_pcc 
        WHERE id_pacient IN (
            SELECT id_pacient FROM dataset_final_pcc WHERE target = 2 LIMIT 20
        )
    """
    df_sample = pd.read_sql_query(query, conn)
    conn.close()
    
    patient_ids = df_sample['id_pacient'].tolist()[:n_samples]
    print(f"Seleccionats {len(patient_ids)} pacients de la base de dades (classes NO, PCC i MACA).", flush=True)
    
    times_sqlite = []
    times_v3 = []
    times_faiss = []
    times_shap = []
    times_total_no_llm_with_shap = []
    times_total_no_llm_no_shap = []
    
    times_llm_local = []
    times_total_with_llm_shap = []
    times_total_with_llm_no_shap = []
    
    # Warmup
    print("Executant fase de warm-up...", flush=True)
    p_warm = api.get_patient_series(patient_ids[0])
    api.fer_prediccio_v3(p_warm)
    api.buscar_similars(patient_ids[0], k=10)
    api.calcular_explicabilitat_shap(p_warm)
    print("Warm-up completat.\n", flush=True)
    
    # Execució de les mesures per component
    for i, pid in enumerate(patient_ids):
        # A. SQLite retrieval
        t0 = time.perf_counter()
        p_series = api.get_patient_series(pid)
        t1 = time.perf_counter()
        times_sqlite.append((t1 - t0) * 1000)
        
        # B. Inferència Model V3
        t0 = time.perf_counter()
        pred_v3, conf_v3 = api.fer_prediccio_v3(p_series)
        t1 = time.perf_counter()
        times_v3.append((t1 - t0) * 1000)
        
        # C. Cerca FAISS
        t0 = time.perf_counter()
        veins = api.buscar_similars(pid, k=10)
        t1 = time.perf_counter()
        times_faiss.append((t1 - t0) * 1000)
        
        # D. Càlcul SHAP
        t0 = time.perf_counter()
        shap_res = api.calcular_explicabilitat_shap(p_series)
        t1 = time.perf_counter()
        times_shap.append((t1 - t0) * 1000)
        
        # Context
        cronics_veins = [v["cronic"] for v in veins]
        context = {
            "id_pacient": pid,
            "grup_edat": str(p_series["grup_edat"]),
            "sexe": str(p_series["sexe"]),
            "cronic_actual": str(p_series["cronic"]),
            "diags_totals": api.safe_int(p_series.get("diags_totals", 0)),
            "farmacs_totals": api.safe_int(p_series.get("farmacs_totals", 0)),
            "n_veins": len(veins),
            "pct_pcc": round(cronics_veins.count("PCC") / len(veins) * 100),
            "pct_maca": round(cronics_veins.count("MACA") / len(veins) * 100),
            "pct_no": round(cronics_veins.count("NO") / len(veins) * 100),
            "pct_mort_veins": round(sum(1 for v in veins if v["situacio"] == "D") / len(veins) * 100)
        }
        
        # Temps total sense LLM amb SHAP
        t_no_llm_shap = times_sqlite[-1] + times_v3[-1] + times_faiss[-1] + times_shap[-1]
        times_total_no_llm_with_shap.append(t_no_llm_shap)
        
        # Temps total sense LLM sense SHAP
        t_no_llm_no_shap = times_sqlite[-1] + times_v3[-1] + times_faiss[-1]
        times_total_no_llm_no_shap.append(t_no_llm_no_shap)
        
        # E. LLM benchmark (per als primers test_llm_samples pacients)
        if i < test_llm_samples:
            print(f"Mesurant LLM local per al pacient {i+1}/{test_llm_samples} (ID: {pid})...", flush=True)
            t0 = time.perf_counter()
            informe, t_ollama, font = api.generar_informe(context, shap_res, pred_v3)
            t1 = time.perf_counter()
            llm_time_ms = (t1 - t0) * 1000
            times_llm_local.append(llm_time_ms)
            times_total_with_llm_shap.append(t_no_llm_shap + llm_time_ms)
            times_total_with_llm_no_shap.append(t_no_llm_no_shap + llm_time_ms)
            print(f"  -> Generat en {llm_time_ms:.1f} ms ({font})", flush=True)
            
        if (i + 1) % 10 == 0:
            print(f"Processats {i + 1}/{len(patient_ids)} pacients...", flush=True)
            
    print("\n" + "="*70, flush=True)
    print("                   RESULTATS DEL BENCHMARK", flush=True)
    print("="*70, flush=True)
    
    def stats(arr):
        return {
            "mean": np.mean(arr),
            "std": np.std(arr),
            "median": np.median(arr),
            "min": np.min(arr),
            "max": np.max(arr)
        }
    
    res = {
        "Recuperació del pacient des de SQLite": stats(times_sqlite),
        "Inferència del model V3": stats(times_v3),
        "Cerca de similitud FAISS": stats(times_faiss),
        "Càlcul SHAP (Estat 1 + Estat 2)": stats(times_shap),
        "Temps Backend IA (Sense LLM - Amb SHAP)": stats(times_total_no_llm_with_shap),
        "Temps Backend IA (Sense LLM - Sense SHAP)": stats(times_total_no_llm_no_shap),
    }
    
    if times_llm_local:
        res["Generació amb LLM (Ollama Local)"] = stats(times_llm_local)
        res["Temps total /api/analyze (Amb SHAP)"] = stats(times_total_with_llm_shap)
        res["Temps total /api/analyze (Sense SHAP)"] = stats(times_total_with_llm_no_shap)
        
    for k, v in res.items():
        print(f"\n* {k}:", flush=True)
        print(f"  - Mitjana (Mean): {v['mean']:.2f} ms ({v['mean']/1000:.4f} s)", flush=True)
        print(f"  - Mediana (Median): {v['median']:.2f} ms", flush=True)
        print(f"  - Desv. Estàndard (Std): {v['std']:.2f} ms", flush=True)
        print(f"  - Rang (Min - Max): {v['min']:.2f} ms - {v['max']:.2f} ms", flush=True)
        
    print("\n" + "="*70, flush=True)
    print("Taula de resultats experimentals per al TFG:\n", flush=True)
    print("| Component | Mitjana (ms) | Mediana (ms) | Desv. Est. (ms) | Rang [Min - Max] |", flush=True)
    print("| :--- | :---: | :---: | :---: | :---: |", flush=True)
    for k, v in res.items():
        print(f"| {k} | {v['mean']:.2f} ms | {v['median']:.2f} ms | ± {v['std']:.2f} ms | [{v['min']:.2f} - {v['max']:.2f}] ms |", flush=True)
    print("="*70, flush=True)

if __name__ == '__main__':
    run_benchmark(n_samples=50, test_llm_samples=5)
