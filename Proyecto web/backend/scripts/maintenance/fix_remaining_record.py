#!/usr/bin/env python3
"""
Script para corregir el registro médico restante
"""

import sqlite3
import os

def main():
    # Ruta a la base de datos
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'medical_system.db')
    
    if not os.path.exists(db_path):
        print(f"Base de datos no encontrada en: {db_path}")
        return
    
    print("=== CORRIGIENDO REGISTRO MÉDICO RESTANTE ===\n")
    
    # Conectar a la base de datos
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Buscar el registro médico ID 2 sin cita asociada
        cursor.execute("""
            SELECT mr.id, mr.patient_id, mr.doctor_id, mr.consultation_date
            FROM medical_records mr
            WHERE mr.id = 2 AND mr.appointment_id IS NULL
        """)
        
        record = cursor.fetchone()
        
        if record:
            record_id, patient_id, doctor_id, consultation_date = record
            
            # Asociar con la cita ID 1 (que ya tiene una consulta)
            cursor.execute("""
                UPDATE medical_records 
                SET appointment_id = 1 
                WHERE id = ?
            """, (record_id,))
            
            print(f"Registro médico ID {record_id} asociado con cita ID 1")
            
            # Confirmar cambios
            conn.commit()
            print("Corrección completada")
        else:
            print("No se encontró el registro médico ID 2")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
