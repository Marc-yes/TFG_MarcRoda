#!/usr/bin/env python3
import os
import sqlite3
import pandas as pd

# Directori de treball de l'script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "processed", "clinic_data.sqlite")
EXCEL_ANALITIC = os.path.join(BASE_DIR, "processed", "dataset_analitico.xlsx")
CSV_PROCESSAT = os.path.join(BASE_DIR, "processed", "dataset_final_pcc.csv")

def main():
    print("Iniciant la migracio de dades a SQLite...")
    
    # Comprovar si els fitxers d'origen existeixen
    if not os.path.exists(EXCEL_ANALITIC):
        print(f"ERROR: No s'ha trobat el fitxer analitic a: {EXCEL_ANALITIC}")
        return
    if not os.path.exists(CSV_PROCESSAT):
        print(f"ERROR: No s'ha trobat el fitxer processat a: {CSV_PROCESSAT}")
        return

    # Connexio a SQLite
    print(f"Creant base de dades SQLite a: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Carregar i migrar dataset_analitico.xlsx
        print("Carregant dades en brut (dataset_analitico.xlsx)...")
        df_analitic = pd.read_excel(EXCEL_ANALITIC)
        
        # Assegurar columna situacio
        if "situacio" not in df_analitic.columns:
            df_analitic["situacio"] = "A"
            
        print(f"Escrivint taula 'dataset_analitico' ({df_analitic.shape[0]} pacients)...")
        df_analitic.to_sql("dataset_analitico", conn, if_exists="replace", index=False)

        # 2. Carregar i migrar dataset_final_pcc.csv
        print("Carregant dades preprocessades (dataset_final_pcc.csv)...")
        df_processat = pd.read_csv(CSV_PROCESSAT)
        
        # Assegurar columna situacio
        if "situacio" not in df_processat.columns:
            df_processat["situacio"] = "A"
            
        print(f"Escrivint taula 'dataset_final_pcc' ({df_processat.shape[0]} pacients)...")
        df_processat.to_sql("dataset_final_pcc", conn, if_exists="replace", index=False)

        # 3. Crear indexs de cerca rapida per a id_pacient
        print("Creant indexs de cerca rapida per a 'id_pacient'...")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_analitic_id_pacient ON dataset_analitico (id_pacient);")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_processat_id_pacient ON dataset_final_pcc (id_pacient);")

        # 4. Crear la taula de feedback si no existeix (mai s'esborra si ja existeix)
        print("Creant taula 'feedback' per a les decisions del professional sanitari...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            id_pacient INTEGER,
            prediccio_model TEXT,
            confianca_model REAL,
            feedback_correcte INTEGER,
            classificacio_correcta TEXT,
            comentari TEXT,
            usuari TEXT
        );
        """)

        conn.commit()
        print("Base de dades inicialitzada i migrada correctament!")

    except Exception as e:
        print(f"ERROR durant la migracio: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
