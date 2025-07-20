#!/usr/bin/env python3
"""
Script para analizar los registros médicos existentes
"""

import sqlite3
from datetime import datetime

# Conectar a la base de datos
db_path = "instance/medical_system.db"

def analyze_medical_records():
    """Analizar registros médicos existentes"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Obtener todos los registros médicos
        cursor.execute("""
            SELECT 
                mr.id,
                mr.patient_id,
                p.first_name || ' ' || p.last_name as patient_name,
                mr.doctor_id,
                u.first_name || ' ' || u.last_name as doctor_name,
                mr.symptoms,
                mr.diagnosis,
                mr.treatment,
                mr.prescriptions,
                mr.observations,
                mr.appointment_id,
                mr.consultation_date
            FROM medical_records mr
            JOIN patients p ON mr.patient_id = p.id
            JOIN users u ON mr.doctor_id = u.id
            ORDER BY mr.consultation_date DESC
        """)
        
        records = cursor.fetchall()
        
        print(f"TOTAL DE REGISTROS MÉDICOS: {len(records)}")
        print("="*80)
        
        for record in records:
            mr_id, patient_id, patient_name, doctor_id, doctor_name, symptoms, diagnosis, treatment, prescriptions, observations, appointment_id, consultation_date = record
            
            # Verificar si es sustancial
            has_substantial_info = any([
                symptoms and symptoms.strip(),
                diagnosis and diagnosis.strip(),
                treatment and treatment.strip(),
                prescriptions and prescriptions.strip(),
                observations and observations.strip(),
            ])
            
            status = "✓ SUSTANCIAL" if has_substantial_info else "✗ VACÍO/MÍNIMO"
            
            print(f"ID: {mr_id} | Paciente: {patient_name} | Doctor: {doctor_name}")
            print(f"  Estado: {status}")
            print(f"  Cita ID: {appointment_id or 'No asociada'}")
            print(f"  Fecha: {consultation_date}")
            print(f"  Síntomas: {symptoms[:50] + '...' if symptoms and len(symptoms) > 50 else symptoms or 'VACÍO'}")
            print(f"  Diagnóstico: {diagnosis[:50] + '...' if diagnosis and len(diagnosis) > 50 else diagnosis or 'VACÍO'}")
            print(f"  Observaciones: {observations[:50] + '...' if observations and len(observations) > 50 else observations or 'VACÍO'}")
            print("-" * 80)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    analyze_medical_records()
