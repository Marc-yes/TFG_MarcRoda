#!/usr/bin/env python3
import os
import sys
import pandas as pd
import sqlite3

# Add ai directory to path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AI_DIR = os.path.join(BASE_DIR, "ai")
sys.path.insert(0, AI_DIR)

import api

print("--- Testing API with newly trained 3-branch models ---")
# 1. Obtenir un pacient de test
conn = sqlite3.connect(api.DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT id_pacient FROM dataset_final_pcc LIMIT 5;")
pids = [row[0] for row in cursor.fetchall()]
conn.close()

print(f"Testing patient IDs: {pids}")

for pid in pids:
    p_series = api.get_patient_series(pid)
    assert p_series is not None, f"Patient {pid} not found"
    
    # Test predicció V3
    pred, conf = api.fer_prediccio_v3(p_series)
    print(f"\n[Pacient {pid}] Predicció V3: {pred}, Confiança: {conf:.4f}")
    
    # Test SHAP
    shap_res = api.calcular_explicabilitat_shap(p_series)
    assert "stage1_chronic_vs_no" in shap_res, "Missing stage1 SHAP"
    assert "stage2_maca_vs_pcc" in shap_res, "Missing stage2 SHAP"
    
    s1_vars = [item["variable"] for item in shap_res["stage1_chronic_vs_no"][:3]]
    s2_vars = [item["variable"] for item in shap_res["stage2_maca_vs_pcc"][:3]]
    
    # Verify no 'counts__', 'labs__', 'cat__' prefixes remain
    for v in s1_vars + s2_vars:
        assert not v.startswith("counts__"), f"Residual prefix in {v}"
        assert not v.startswith("labs__"), f"Residual prefix in {v}"
        assert not v.startswith("cat__"), f"Residual prefix in {v}"
        assert not v.startswith("num__"), f"Residual prefix in {v}"
    
    print(f"Top 3 factors SHAP Estat 1: {s1_vars}")
    print(f"Top 3 factors SHAP Estat 2: {s2_vars}")

print("\n--- ALL VERIFICATION TESTS PASSED SUCCESSFULLY! ---")
