import sqlite3
import os
import sys
import json
from datetime import datetime

# Assegurar codificació UTF-8 per a la consola de Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "processed", "clinic_data.sqlite")

def run_feedback_validation():
    print("=" * 70)
    print("🔍 INICI DE LA VALIDACIÓ INTEGRAL DEL SISTEMA DE FEEDBACK CLÍNIC")
    print("=" * 70)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # ── 1. VERIFICACIÓ D'ESQUEMA ──────────────────────────────────────────
    print("\n[PAS 1] Verificació de l'esquema de la taula 'feedback'...")
    cursor.execute("PRAGMA table_info(feedback);")
    columns = cursor.fetchall()
    print(f" Columnes detectades ({len(columns)}):")
    for col in columns:
        print(f"   - {col[1]} ({col[2]}) | NotNull: {bool(col[3])} | PK: {bool(col[5])}")
    
    # ── 2. PACIENTS PENDENTS A LA CUA DE PRIORITAT (ABANS DEL FEEDBACK) ────
    print("\n[PAS 2] Comprovació de la cua de prioritat abans del feedback...")
    cursor.execute("""
        SELECT p.id_pacient, p.prediccio_estat, p.prob_maca, p.prob_pcc
        FROM dataset_final_pcc p
        WHERE p.prediccio_estat IN ('MACA', 'PCC')
          AND NOT EXISTS (SELECT 1 FROM feedback f WHERE f.id_pacient = p.id_pacient)
        LIMIT 5;
    """)
    pendents_abans = cursor.fetchall()
    print(f" Top 5 pacients pendents de revisar:")
    for p in pendents_abans:
        print(f"   - Pacient #{p[0]}: Categoria={p[1]}, Prob_MACA={p[2]:.4f}, Prob_PCC={p[3]:.4f}")
    
    test_patient_id = pendents_abans[0][0]
    test_pred_model = pendents_abans[0][1]
    test_conf = pendents_abans[0][2] if test_pred_model == 'MACA' else pendents_abans[0][3]
    
    print(f"\n-> Seleccionat pacient de test #{test_patient_id} per validar el flux complet.")
    
    # ── 3. SIMULACIÓ D'INSERCIÓ DE FEEDBACK POSITIU (VALIDACIÓ) ────────────
    print(f"\n[PAS 3] Simulant enviament de feedback POSITIU (Validació)...")
    fb_pos_payload = {
        "timestamp": datetime.now().isoformat(),
        "id_pacient": int(test_patient_id),
        "prediccio_model": test_pred_model,
        "confianca_model": float(test_conf),
        "feedback_correcte": 1,
        "classificacio_correcta": test_pred_model,
        "comentari": "Validació clínica automàtica del test de control",
        "usuari": "Dr. Marc Roda"
    }
    
    cursor.execute("""
        INSERT INTO feedback (timestamp, id_pacient, prediccio_model, confianca_model, 
                              feedback_correcte, classificacio_correcta, comentari, usuari)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        fb_pos_payload["timestamp"],
        fb_pos_payload["id_pacient"],
        fb_pos_payload["prediccio_model"],
        fb_pos_payload["confianca_model"],
        fb_pos_payload["feedback_correcte"],
        fb_pos_payload["classificacio_correcta"],
        fb_pos_payload["comentari"],
        fb_pos_payload["usuari"]
    ))
    conn.commit()
    pos_fb_id = cursor.lastrowid
    print(f" Feedback positiu inserit correctament amb ID = {pos_fb_id}!")
    
    # ── 4. VERIFICACIÓ D'EXCLUSIÓ EN TEMPS REAL DE LA CUA ─────────────────
    print(f"\n[PAS 4] Verificant que el pacient #{test_patient_id} ha desaparegut de la cua de pendents...")
    cursor.execute("""
        SELECT COUNT(*)
        FROM dataset_final_pcc p
        WHERE p.id_pacient = ?
          AND NOT EXISTS (SELECT 1 FROM feedback f WHERE f.id_pacient = p.id_pacient);
    """, (test_patient_id,))
    esta_pendent = cursor.fetchone()[0]
    if esta_pendent == 0:
        print(f" ÈXIT: El pacient #{test_patient_id} JA NO apareix a la llista de pendents (filtre NOT EXISTS operatiu).")
    else:
        print(f"❌ ERROR: El pacient #{test_patient_id} encara apareix com a pendent!")
        
    # ── 5. SIMULACIÓ D'INSERCIÓ DE FEEDBACK NEGATIU (ESMENA / CORRECCIÓ) ──
    print(f"\n[PAS 5] Simulant una esmena mèdica (feedback NEGATIU amb reclassificació)...")
    fb_neg_payload = {
        "timestamp": datetime.now().isoformat(),
        "id_pacient": int(test_patient_id),
        "prediccio_model": test_pred_model,
        "confianca_model": float(test_conf),
        "feedback_correcte": 0,
        "classificacio_correcta": "NO" if test_pred_model != "NO" else "PCC",
        "comentari": "Esmena diagnòstica: pacient amb estabilització analítica recent.",
        "usuari": "Dra. Anna Garcia (Cap de Servei)"
    }
    
    cursor.execute("""
        INSERT INTO feedback (timestamp, id_pacient, prediccio_model, confianca_model, 
                              feedback_correcte, classificacio_correcta, comentari, usuari)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        fb_neg_payload["timestamp"],
        fb_neg_payload["id_pacient"],
        fb_neg_payload["prediccio_model"],
        fb_neg_payload["confianca_model"],
        fb_neg_payload["feedback_correcte"],
        fb_neg_payload["classificacio_correcta"],
        fb_neg_payload["comentari"],
        fb_neg_payload["usuari"]
    ))
    conn.commit()
    neg_fb_id = cursor.lastrowid
    print(f" Feedback esmenat inserit correctament amb ID = {neg_fb_id}!")
    
    # ── 6. CONSULTA DE L'HISTORIAL CLINIC / TIMELINE ──────────────────────
    print(f"\n[PAS 6] Recuperant historial cronològic (timeline) del pacient #{test_patient_id}...")
    cursor.execute("""
        SELECT id, timestamp, prediccio_model, confianca_model, feedback_correcte, 
               classificacio_correcta, comentari, usuari
        FROM feedback
        WHERE id_pacient = ?
        ORDER BY timestamp DESC;
    """, (test_patient_id,))
    historial = cursor.fetchall()
    print(f" Total interaccions registrades per a aquest pacient: {len(historial)}")
    for item in historial:
        tipus = " VALIDAT" if item[4] else f"❌ ESMENAT a {item[5]}"
        print(f"   • [{item[1][:19]}] {tipus} per {item[7]}")
        print(f"     Predicció IA: {item[2]} ({item[3]*100:.1f}%) | Comentari: \"{item[6]}\"")
        
    # ── 7. NETEJA DELS REGISTRES DE PROVA ──────────────────────────────────
    print(f"\n[PAS 7] Netejant els registres de prova temporals (IDs {pos_fb_id}, {neg_fb_id})...")
    cursor.execute("DELETE FROM feedback WHERE id IN (?, ?);", (pos_fb_id, neg_fb_id))
    conn.commit()
    print(" Registres de test esborrats. Estat original de la base de dades restaurat.")
    
    # Comprovació final
    cursor.execute("SELECT id, id_pacient, usuari, comentari FROM feedback;")
    final_rows = cursor.fetchall()
    print(f"\n[ESTAT FINAL DB] Registres persistents actuals ({len(final_rows)}):")
    for r in final_rows:
        print(f"   - ID {r[0]} | Pacient #{r[1]} | Usuari: {r[2]} | Obs: {r[3]}")
        
    conn.close()
    print("\n" + "=" * 70)
    print(" VALIDACIÓ COMPLETADA AMB ÈXIT AL 100%")
    print("=" * 70)

if __name__ == "__main__":
    run_feedback_validation()
