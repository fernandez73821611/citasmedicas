#!/usr/bin/env python3
"""
Script para verificar que la corrección funciona correctamente
"""

import sqlite3

# Conectar a la base de datos
db_path = "instance/medical_system.db"

def test_medical_history_logic():
    """Probar la lógica de historia clínica"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Obtener información del paciente
        cursor.execute("""
            SELECT 
                p.id,
                p.first_name || ' ' || p.last_name as patient_name,
                COUNT(mr.id) as total_records,
                COUNT(CASE WHEN mr.symptoms IS NOT NULL AND mr.symptoms != '' THEN 1 END) as records_with_symptoms,
                COUNT(CASE WHEN mr.diagnosis IS NOT NULL AND mr.diagnosis != '' THEN 1 END) as records_with_diagnosis,
                COUNT(CASE WHEN mr.observations IS NOT NULL AND mr.observations != '' THEN 1 END) as records_with_observations
            FROM patients p
            LEFT JOIN medical_records mr ON p.id = mr.patient_id
            GROUP BY p.id, p.first_name, p.last_name
        """)
        
        patients = cursor.fetchall()
        
        print("ANÁLISIS DE PACIENTES Y SU ESTADO DE HISTORIA CLÍNICA:")
        print("="*70)
        
        for patient in patients:
            pid, name, total_records, records_with_symptoms, records_with_diagnosis, records_with_observations = patient
            
            print(f"\nPACIENTE: {name} (ID: {pid})")
            print(f"  Total de registros médicos: {total_records}")
            print(f"  Registros con síntomas: {records_with_symptoms}")
            print(f"  Registros con diagnóstico: {records_with_diagnosis}")
            print(f"  Registros con observaciones: {records_with_observations}")
            
            # Evaluar si debería tener historia clínica
            if total_records > 0:
                # Verificar si tiene información sustancial
                cursor.execute("""
                    SELECT id, symptoms, diagnosis, observations
                    FROM medical_records
                    WHERE patient_id = ?
                """, (pid,))
                
                records = cursor.fetchall()
                has_substantial_info = False
                
                for record in records:
                    rid, symptoms, diagnosis, observations = record
                    
                    # Aplicar la misma lógica que en get_for_patient
                    has_substantial_observations = False
                    if observations and observations.strip():
                        obs_upper = observations.upper()
                        has_substantial_observations = any([
                            'ANTECEDENTES PERSONALES' in obs_upper,
                            'ANTECEDENTES FAMILIARES' in obs_upper,
                            'ALERGIAS' in obs_upper,
                            'MEDICAMENTOS ACTUALES' in obs_upper,
                            'HÁBITOS' in obs_upper,
                            len(observations.strip()) > 50
                        ])
                    
                    record_has_substantial_info = any([
                        symptoms and symptoms.strip(),
                        diagnosis and diagnosis.strip(),
                        has_substantial_observations,
                    ])
                    
                    print(f"    Registro {rid}: {'✓ SUSTANCIAL' if record_has_substantial_info else '✗ VACÍO'}")
                    
                    if record_has_substantial_info:
                        has_substantial_info = True
                
                print(f"  -> Debería tener historia clínica: {'SÍ' if has_substantial_info else 'NO'}")
            else:
                print(f"  -> Paciente nuevo (sin registros)")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_medical_history_logic()
