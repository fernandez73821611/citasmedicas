#!/usr/bin/env python3
"""
Script para verificar que los botones de consulta aparezcan solo cuando hay citas pendientes.
"""

import sqlite3
from datetime import datetime

def verify_consultation_buttons():
    """Verificar qué pacientes deberían tener botones de consulta disponibles"""
    
    # Conectar a la base de datos
    conn = sqlite3.connect('instance/medical_system.db')
    cursor = conn.cursor()
    
    print("=== VERIFICACIÓN DE BOTONES DE CONSULTA ===")
    print(f"Fecha actual: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Obtener todos los pacientes que han tenido citas con doctores
    cursor.execute("""
        SELECT DISTINCT 
            p.id, p.first_name, p.last_name, p.dni,
            u.id as doctor_id, u.first_name as doctor_name, u.last_name as doctor_last_name
        FROM patients p
        JOIN appointments a ON p.id = a.patient_id
        JOIN users u ON a.doctor_id = u.id
        WHERE p.is_active = 1
        ORDER BY p.first_name, p.last_name
    """)
    
    patient_doctors = cursor.fetchall()
    
    for patient_id, patient_first, patient_last, patient_dni, doctor_id, doctor_first, doctor_last in patient_doctors:
        print(f"\n📋 PACIENTE: {patient_first} {patient_last} (DNI: {patient_dni})")
        print(f"👨‍⚕️ DOCTOR: {doctor_first} {doctor_last} (ID: {doctor_id})")
        
        # Verificar si tiene historia clínica
        cursor.execute("""
            SELECT COUNT(*) FROM medical_histories 
            WHERE patient_id = ?
        """, (patient_id,))
        has_history = cursor.fetchone()[0] > 0
        
        print(f"📄 Historia clínica: {'✅ Sí' if has_history else '❌ No'}")
        
        # Verificar citas pendientes para consulta (ready_for_doctor sin consulta)
        cursor.execute("""
            SELECT a.id, a.date_time, a.status
            FROM appointments a
            LEFT JOIN medical_records mr ON a.id = mr.appointment_id
            WHERE a.patient_id = ? AND a.doctor_id = ? AND a.status = 'ready_for_doctor'
            AND mr.id IS NULL
        """, (patient_id, doctor_id))
        
        pending_appointments = cursor.fetchall()
        
        if pending_appointments:
            print(f"🔄 Citas pendientes para consulta: {len(pending_appointments)}")
            for app_id, app_date, app_status in pending_appointments:
                print(f"   - Cita ID {app_id}: {app_date} (Estado: {app_status})")
        else:
            print("✅ No hay citas pendientes para consulta")
        
        # Verificar consultas completadas
        cursor.execute("""
            SELECT COUNT(*) FROM medical_records 
            WHERE patient_id = ? AND doctor_id = ?
        """, (patient_id, doctor_id))
        consultations_count = cursor.fetchone()[0]
        
        print(f"📊 Consultas completadas: {consultations_count}")
        
        # Determinar si debería aparecer el botón de consulta
        should_show_button = has_history and len(pending_appointments) > 0
        print(f"🔘 Botón de consulta: {'✅ Mostrar' if should_show_button else '❌ Ocultar'}")
        
        if should_show_button:
            print(f"   → Razón: Tiene historia clínica y {len(pending_appointments)} cita(s) pendiente(s)")
        else:
            if not has_history:
                print("   → Razón: No tiene historia clínica")
            elif len(pending_appointments) == 0:
                print("   → Razón: No tiene citas pendientes para consulta")
        
        print("-" * 80)
    
    # Resumen final
    print("\n=== RESUMEN ===")
    cursor.execute("""
        SELECT COUNT(DISTINCT p.id) FROM patients p
        JOIN appointments a ON p.id = a.patient_id
        WHERE p.is_active = 1
    """)
    total_patients = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(DISTINCT p.id) FROM patients p
        JOIN appointments a ON p.id = a.patient_id
        JOIN medical_histories mh ON p.id = mh.patient_id
        LEFT JOIN medical_records mr ON a.id = mr.appointment_id
        WHERE p.is_active = 1 AND a.status = 'ready_for_doctor' AND mr.id IS NULL
    """)
    patients_with_pending_consultations = cursor.fetchone()[0]
    
    print(f"📊 Total de pacientes: {total_patients}")
    print(f"🔘 Pacientes que deberían tener botón de consulta: {patients_with_pending_consultations}")
    
    conn.close()

if __name__ == "__main__":
    verify_consultation_buttons()
