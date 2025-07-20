#!/usr/bin/env python3
"""
Script para simular el dashboard del doctor
"""

import sqlite3
import os
from datetime import datetime, date

def main():
    # Ruta a la base de datos
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'medical_system.db')
    
    if not os.path.exists(db_path):
        print(f"Base de datos no encontrada en: {db_path}")
        return
    
    print("=== SIMULANDO DASHBOARD DEL DOCTOR ===\n")
    
    # Conectar a la base de datos
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Simular el usuario doctor (Roger Osbaldo, asumiendo ID 2)
        doctor_id = 2
        today = date.today()
        
        print(f"Dashboard para doctor ID: {doctor_id}")
        print(f"Fecha: {today}\n")
        
        # Citas de hoy
        print("=== CITAS DE HOY ===")
        cursor.execute("""
            SELECT a.id, a.status, a.date_time,
                   p.first_name || ' ' || p.last_name as patient_name,
                   CASE WHEN t.id IS NOT NULL THEN 'Sí' ELSE 'No' END as has_triage
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            LEFT JOIN triages t ON a.id = t.appointment_id
            WHERE a.doctor_id = ? AND DATE(a.date_time) = ?
            ORDER BY a.date_time
        """, (doctor_id, today))
        
        today_appointments = cursor.fetchall()
        for apt in today_appointments:
            print(f"  - {apt[3]} ({apt[1]}) - {apt[2]} - Triage: {apt[4]}")
        
        # Citas listas para consulta (con triage completado, pero no completadas)
        print("\n=== CITAS LISTAS PARA CONSULTA ===")
        cursor.execute("""
            SELECT a.id, a.status, a.date_time,
                   p.first_name || ' ' || p.last_name as patient_name
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            WHERE a.doctor_id = ? AND a.status = 'ready_for_doctor'
            ORDER BY a.date_time
        """, (doctor_id,))
        
        ready_appointments = cursor.fetchall()
        if ready_appointments:
            for apt in ready_appointments:
                print(f"  - {apt[3]} - {apt[2]}")
        else:
            print("  No hay citas listas para consulta")
        
        # Citas en triage
        print("\n=== CITAS EN TRIAGE ===")
        cursor.execute("""
            SELECT a.id, a.status, a.date_time,
                   p.first_name || ' ' || p.last_name as patient_name
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            WHERE a.doctor_id = ? AND a.status = 'in_triage'
            ORDER BY a.date_time
        """, (doctor_id,))
        
        in_triage_appointments = cursor.fetchall()
        if in_triage_appointments:
            for apt in in_triage_appointments:
                print(f"  - {apt[3]} - {apt[2]}")
        else:
            print("  No hay citas en triage")
        
        # Citas completadas
        print("\n=== CITAS COMPLETADAS ===")
        cursor.execute("""
            SELECT a.id, a.status, a.date_time,
                   p.first_name || ' ' || p.last_name as patient_name
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            WHERE a.doctor_id = ? AND a.status = 'completed'
            ORDER BY a.date_time DESC
        """, (doctor_id,))
        
        completed_appointments = cursor.fetchall()
        if completed_appointments:
            for apt in completed_appointments:
                print(f"  - {apt[3]} - {apt[2]}")
        else:
            print("  No hay citas completadas")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
