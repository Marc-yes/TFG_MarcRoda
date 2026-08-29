import requests
import json
import sys

# Força la codificació UTF-8 a la consola per evitar errors de charmap a Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("1. Provant l'endpoint /api/analyze per al pacient ID 6...")
url_analyze = "http://localhost:5001/api/analyze"
payload = {"id_pacient": 6}

try:
    resp = requests.post(url_analyze, json=payload)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print("\nOK: Resposta d'anàlisi obtinguda:")
        print(f"   Pacient ID: {data['pacient']['id_pacient']}")
        print(f"   Classificació Suggerida: {data['prediccio_v3']['resultat']}")
        print(f"   Model Usat per l'Informe: {data.get('model_informe', 'No especificat')}")
        print(f"   Temps de Generació: {data['temps_generacio_segons']}s")
        print("\n   --- INFORME DE DECISIÓ CLÍNICA (IA) AMB SHAP ---")
        print(data['informe'])
        print("   ------------------------------------------------")
    else:
        print(f"Error: {resp.text}")
except Exception as e:
    print(f"Error de connexió a Flask: {e}")
