#!/usr/bin/env python3
"""
Script para limpiar registros médicos vacíos creados por el bug de "Solo Guardar Historia"
"""

import sqlite3
from datetime import datetime

# Conectar a la base de datos
db_path = "instance/medical_system.db"

def clean_empty_medical_records():
    """Eliminar registros médicos que están completamente vacíos"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Buscar registros médicos que están completamente vacíos
        cursor.execute("""
            SELECT id, patient_id, doctor_id, symptoms, diagnosis, treatment, prescriptions, observations
            FROM medical_records
            WHERE (symptoms IS NULL OR symptoms = '')
            AND (diagnosis IS NULL OR diagnosis = '')
            AND (treatment IS NULL OR treatment = '')
            AND (prescriptions IS NULL OR prescriptions = '')
            AND (observations IS NULL OR observations = '')
            AND blood_pressure IS NULL
            AND heart_rate IS NULL
            AND temperature IS NULL
            AND weight IS NULL
            AND height IS NULL
            AND appointment_id IS NULL
        """)
        
        empty_records = cursor.fetchall()
        
        if empty_records:
            print(f"Encontrados {len(empty_records)} registros médicos completamente vacíos:")
            
            for record in empty_records:
                print(f"  ID: {record[0]}, Paciente: {record[1]}, Doctor: {record[2]}")
            
            # Confirmar eliminación
            confirm = input("¿Desea eliminar estos registros vacíos? (s/n): ")
            
            if confirm.lower() == 's':
                # Eliminar registros vacíos
                empty_ids = [record[0] for record in empty_records]
                placeholders = ','.join(['?' for _ in empty_ids])
                
                cursor.execute(f"DELETE FROM medical_records WHERE id IN ({placeholders})", empty_ids)
                conn.commit()
                
                print(f"Eliminados {len(empty_records)} registros médicos vacíos")
            else:
                print("Operación cancelada")
        else:
            print("No se encontraron registros médicos completamente vacíos")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    clean_empty_medical_records()
