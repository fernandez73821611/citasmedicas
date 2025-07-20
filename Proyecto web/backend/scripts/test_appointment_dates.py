#!/usr/bin/env python3
"""
Script para probar que las fechas de las citas se muestran correctamente
en la facturación después de la corrección.

Ejecutar desde la raíz del proyecto:
python backend/scripts/test_appointment_dates.py
"""

import sys
import os

# Añadir el directorio backend al path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from datetime import datetime, timedelta
from app import create_app, db
from app.models import *
from config import Config

def test_appointment_dates():
    """Prueba las fechas de las citas en el sistema."""
    
    # Crear la aplicación
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 Probando fechas de citas...")
            
            # Buscar una cita programada para hoy
            today = datetime.now().date()
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())
            
            appointment = Appointment.query.filter(
                Appointment.date_time >= today_start,
                Appointment.date_time <= today_end
            ).first()
            
            if appointment:
                print(f"✅ Cita encontrada:")
                print(f"   ID: {appointment.id}")
                print(f"   Paciente: {appointment.patient.full_name}")
                print(f"   Doctor: {appointment.doctor.full_name}")
                print(f"   Fecha/Hora original: {appointment.date_time}")
                print(f"   Fecha/Hora formateada: {appointment.date_time.strftime('%d/%m/%Y %H:%M')}")
                print(f"   Fecha ISO: {appointment.date_time.strftime('%Y-%m-%dT%H:%M:00')}")
                
                # Simular la API response
                api_response = {
                    'id': appointment.id,
                    'date': appointment.date_time.strftime('%Y-%m-%dT%H:%M:00'),
                    'date_formatted': appointment.date_time.strftime('%d/%m/%Y %H:%M'),
                    'doctor': f"Dr. {appointment.doctor.first_name} {appointment.doctor.last_name}",
                    'specialty': appointment.specialty.name if appointment.specialty else "No especificado",
                    'status': appointment.status
                }
                
                print(f"\n📊 Respuesta de API simulada:")
                print(f"   date: '{api_response['date']}'")
                print(f"   date_formatted: '{api_response['date_formatted']}'")
                
                # Probar interpretación de JavaScript (simulada)
                try:
                    # Simular lo que haría JavaScript
                    import datetime as dt
                    js_date = dt.datetime.fromisoformat(api_response['date'].replace('T', ' '))
                    print(f"\n🐍 Interpretación Python (similar a JS):")
                    print(f"   Fecha interpretada: {js_date}")
                    print(f"   ¿Coincide con original? {js_date == appointment.date_time}")
                    
                except Exception as e:
                    print(f"❌ Error en interpretación: {e}")
                
                print(f"\n✅ La fecha formateada '{api_response['date_formatted']}' debe mostrarse correctamente en el frontend")
                
            else:
                print("⚠️  No se encontraron citas para hoy. Creando una de prueba...")
                
                # Buscar un paciente y doctor
                patient = Patient.query.first()
                doctor = User.query.filter_by(role='doctor').first()
                specialty = Specialty.query.first()
                
                if not patient:
                    print("❌ No hay pacientes en el sistema")
                    return
                    
                if not doctor:
                    print("❌ No hay doctores en el sistema")
                    return
                
                # Crear cita de prueba
                test_appointment = Appointment(
                    patient_id=patient.id,
                    doctor_id=doctor.id,
                    specialty_id=specialty.id if specialty else None,
                    date_time=datetime.now().replace(hour=14, minute=30, second=0, microsecond=0),
                    reason="Prueba de fechas",
                    status='scheduled'
                )
                
                db.session.add(test_appointment)
                db.session.commit()
                
                print(f"✅ Cita de prueba creada:")
                print(f"   ID: {test_appointment.id}")
                print(f"   Fecha/Hora: {test_appointment.date_time}")
                print(f"   Formateada: {test_appointment.date_time.strftime('%d/%m/%Y %H:%M')}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_appointment_dates()
