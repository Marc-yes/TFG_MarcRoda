import requests
import json
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "processed", "clinic_data.sqlite")

print("1. Provant l'endpoint /api/analyze per al pacient ID 6...")
url_analyze = "http://localhost:5001/api/analyze"
payload = {"id_pacient": 6}

try:
    resp = requests.post(url_analyze, json=payload)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print("OK: Prediccio obtinguda:")
        print(f"   Pacient ID: {data['pacient']['id_pacient']}")
        print(f"   Prediccio: {data['prediccio_v3']['resultat']}")
        print(f"   Estat Prediccio: {data['prediccio_v3'].get('estat')}")
    else:
        print(f"Error: {resp.text}")
except Exception as e:
    print(f"Error de connexio a Flask: {e}")

print("\n2. Provant l'endpoint /api/feedback/history per al pacient ID 6...")
url_history = "http://localhost:5001/api/feedback/history"

try:
    resp_hist = requests.post(url_history, json={"id_pacient": 6})
    print(f"Status Code: {resp_hist.status_code}")
    if resp_hist.status_code == 200:
        hist_data = resp_hist.json()
        history = hist_data.get("history", [])
        print(f"OK: Trobades {len(history)} files d'historial per al pacient 6:")
        for idx, h in enumerate(history):
            print(f"   Revisio {idx + 1}:")
            print(f"      Data: {h['timestamp']}")
            print(f"      Model: {h['prediccio_model']} (Conf: {h['confianca_model']})")
            print(f"      Validat correcte?: {h['feedback_correcte']}")
            print(f"      Classe correctiva: {h['classificacio_correcta']}")
            print(f"      Usuari: {h['usuari']}")
            print(f"      Comentari: '{h['comentari']}'")
    else:
        print(f"Error historial: {resp_hist.text}")
except Exception as e:
    print(f"Error connexio historial: {e}")
