#!/usr/bin/env python3
"""
Script para corregir los registros médicos sin cita asociada
"""

import sqlite3
import os

def main():
    # Ruta a la base de datos
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'medical_system.db')
    
    if not os.path.exists(db_path):
        print(f"Base de datos no encontrada en: {db_path}")
        return
    
    print("=== CORRIGIENDO REGISTROS MÉDICOS ===\n")
    
    # Conectar a la base de datos
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Buscar registros médicos sin cita asociada
        cursor.execute("""
            SELECT mr.id, mr.patient_id, mr.doctor_id, mr.consultation_date
            FROM medical_records mr
            WHERE mr.appointment_id IS NULL
        """)
        
        records = cursor.fetchall()
        
        for record in records:
            record_id, patient_id, doctor_id, consultation_date = record
            
            # Buscar la cita correspondiente (mismo paciente y doctor, estado ready_for_doctor)
            cursor.execute("""
                SELECT a.id 
                FROM appointments a
                WHERE a.patient_id = ? AND a.doctor_id = ? AND a.status = 'ready_for_doctor'
                ORDER BY a.date_time DESC
                LIMIT 1
            """, (patient_id, doctor_id))
            
            appointment = cursor.fetchone()
            
            if appointment:
                appointment_id = appointment[0]
                
                # Actualizar el registro médico
                cursor.execute("""
                    UPDATE medical_records 
                    SET appointment_id = ? 
                    WHERE id = ?
                """, (appointment_id, record_id))
                
                print(f"Registro médico ID {record_id} asociado con cita ID {appointment_id}")
                
                # Marcar la cita como completada
                cursor.execute("""
                    UPDATE appointments 
                    SET status = 'completed' 
                    WHERE id = ?
                """, (appointment_id,))
                
                print(f"Cita ID {appointment_id} marcada como completada")
        
        # Confirmar cambios
        conn.commit()
        print(f"\nSe procesaron {len(records)} registros médicos")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
