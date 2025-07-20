#!/usr/bin/env python3
"""
Script para verificar que las citas se marcan como completadas correctamente
"""
from app import create_app
from app.models import db, Appointment, MedicalRecord, Patient, User
from datetime import datetime

def test_appointment_completion():
    """Verificar el estado de las citas y sus consultas asociadas"""
    app = create_app()
    with app.app_context():
        print("=== VERIFICACIÓN DE CITAS COMPLETADAS ===")
        
        # Buscar citas de hoy
        today = datetime.now().date()
        today_appointments = Appointment.query.filter(
            Appointment.date_time >= datetime.combine(today, datetime.min.time()),
            Appointment.date_time < datetime.combine(today, datetime.max.time())
        ).all()
        
        print(f"\nCitas de hoy: {len(today_appointments)}")
        
        for appointment in today_appointments:
            print(f"\nCita ID: {appointment.id}")
            print(f"Paciente: {appointment.patient.full_name}")
            print(f"Doctor: {appointment.doctor.full_name}")
            print(f"Estado: {appointment.status}")
            print(f"Fecha: {appointment.date_time}")
            
            # Verificar si tiene consulta médica asociada
            medical_record = MedicalRecord.query.filter_by(
                appointment_id=appointment.id
            ).first()
            
            if medical_record:
                print(f"✓ Tiene consulta médica asociada (ID: {medical_record.id})")
                print(f"  Fecha consulta: {medical_record.consultation_date}")
                print(f"  Diagnóstico: {medical_record.diagnosis[:50]}...")
            else:
                print("✗ No tiene consulta médica asociada")
            
            # Verificar si tiene triage
            if appointment.triage:
                print(f"✓ Tiene triage completado")
                print(f"  Fecha triage: {appointment.triage.created_at}")
            else:
                print("✗ No tiene triage")
            
            print("-" * 50)
        
        # Verificar citas con estado 'ready_for_doctor'
        print("\n=== CITAS LISTAS PARA DOCTOR ===")
        ready_appointments = Appointment.query.filter_by(
            status='ready_for_doctor'
        ).all()
        
        print(f"\nCitas con estado 'ready_for_doctor': {len(ready_appointments)}")
        
        for appointment in ready_appointments:
            print(f"\nCita ID: {appointment.id}")
            print(f"Paciente: {appointment.patient.full_name}")
            print(f"Doctor: {appointment.doctor.full_name}")
            print(f"Fecha: {appointment.date_time}")
            
            # Verificar si tiene consulta médica asociada
            medical_record = MedicalRecord.query.filter_by(
                appointment_id=appointment.id
            ).first()
            
            if medical_record:
                print(f"⚠️  PROBLEMA: Tiene consulta médica pero estado no es 'completed'")
                print(f"  Consulta ID: {medical_record.id}")
                print(f"  Fecha consulta: {medical_record.consultation_date}")
                
                # Intentar corregir el estado
                print(f"  Corrigiendo estado de cita a 'completed'...")
                appointment.status = 'completed'
                db.session.commit()
                print(f"  ✓ Estado corregido")
            else:
                print("✓ No tiene consulta médica (correcto)")
        
        print("\n=== VERIFICACIÓN COMPLETADA ===")

if __name__ == "__main__":
    test_appointment_completion()
