#!/usr/bin/env python3
"""
Script para probar el prellenado de signos vitales desde triage 
en el formulario de consulta médica.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, date
from app import create_app, db
from app.models.patient import Patient
from app.models.user import User
from app.models.appointment import Appointment
from app.models.triage import Triage
from app.models.invoice import Invoice

def test_vital_signs_prefill():
    """Probar prellenado de signos vitales"""
    app = create_app()
    
    with app.app_context():
        print("🔍 Probando prellenado de signos vitales...")
        print("=" * 50)
        
        # Buscar doctor y enfermera
        doctor = User.query.filter_by(role='doctor').first()
        nurse = User.query.filter_by(role='nurse').first()
        
        if not doctor or not nurse:
            print("❌ No hay doctor o enfermera en el sistema")
            return False
        
        # Buscar especialidad del doctor
        from app.models.specialty import Specialty
        specialty = doctor.specialty if hasattr(doctor, 'specialty') and doctor.specialty else Specialty.query.first()
        if not specialty:
            print("❌ No hay especialidades en el sistema")
            return False
        
        # Buscar paciente adulto mayor
        elderly_patient = Patient.query.filter_by(first_name='Carlos', last_name='Mendoza').first()
        if not elderly_patient:
            print("❌ No se encontró paciente de prueba")
            return False
        
        print(f"👤 Paciente: {elderly_patient.full_name} ({elderly_patient.age_group_label})")
        print(f"👨‍⚕️ Doctor: {doctor.full_name}")
        print(f"👩‍⚕️ Enfermera: {nurse.full_name}")
        print()
        
        # Crear cita de prueba
        today = date.today()
        appointment_time = datetime.combine(today, datetime.min.time().replace(hour=10))
        
        appointment = Appointment(
            patient_id=elderly_patient.id,
            doctor_id=doctor.id,
            specialty_id=specialty.id,
            date_time=appointment_time,
            status='scheduled',
            reason='Consulta de control'
        )
        
        db.session.add(appointment)
        db.session.flush()  # Para obtener el ID
        
        # Crear factura pagada
        invoice = Invoice(
            appointment_id=appointment.id,
            patient_id=elderly_patient.id,
            doctor_id=doctor.id,
            invoice_number=f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            issue_date=today,
            due_date=today,
            subtotal=100.00,
            total_amount=100.00,
            status='paid',
            payment_method='efectivo',
            payment_date=today,
            created_by=doctor.id
        )
        
        db.session.add(invoice)
        db.session.flush()
        
        print(f"📅 Cita creada: ID {appointment.id}")
        print(f"💰 Factura pagada: ID {invoice.id}")
        print()
        
        # Crear triage con signos vitales específicos
        triage_data = {
            'patient_id': elderly_patient.id,
            'appointment_id': appointment.id,
            'nurse_id': nurse.id,
            'chief_complaint': 'Control de rutina',
            'priority_level': 'media',
            
            # Signos vitales específicos para adulto mayor
            'blood_pressure_systolic': 135,
            'blood_pressure_diastolic': 85,
            'heart_rate': 65,
            'temperature': 36.2,
            'respiratory_rate': 16,
            'oxygen_saturation': 92,
            'weight': 68.5,
            'height': 165,
            
            # Campos específicos de adulto mayor
            'mobility_status': 'walker',
            'cognitive_status': 'alert',
            'fall_risk': 'moderate',
            'functional_status': 'partial_assistance',
            'chronic_conditions': 'Hipertensión arterial, diabetes tipo 2',
            'medication_polypharmacy': 'Enalapril 10mg 2 veces/día, Metformina 850mg 3 veces/día',
            
            'status': 'completed',
            'completed_at': datetime.now()
        }
        
        triage = Triage(**triage_data)
        db.session.add(triage)
        
        # Actualizar cita
        appointment.status = 'ready_for_doctor'
        
        try:
            db.session.commit()
            print("✅ Triage creado exitosamente")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")
            return False
        
        print()
        print("📋 DATOS DEL TRIAGE PARA PRELLENADO:")
        print("-" * 40)
        print(f"Presión Arterial: {triage.blood_pressure_systolic}/{triage.blood_pressure_diastolic} mmHg")
        print(f"Frecuencia Cardíaca: {triage.heart_rate} bpm")
        print(f"Temperatura: {triage.temperature}°C")
        print(f"Frecuencia Respiratoria: {triage.respiratory_rate} rpm")
        print(f"Peso: {triage.weight} kg")
        print(f"Altura: {triage.height} cm")
        print()
        
        print("🔗 ENLACES PARA PROBAR:")
        print("-" * 25)
        print(f"Triage: http://localhost:5000/nurse/triage/{triage.id}")
        print(f"Consulta: http://localhost:5000/doctor/consultation/{elderly_patient.id}/new?appointment_id={appointment.id}")
        print()
        
        print("✅ Datos de prueba creados. El doctor puede ahora:")
        print("   1. Ver el triage completado")
        print("   2. Iniciar consulta médica") 
        print("   3. Verificar que los signos vitales se prellenen automáticamente")
        print("   4. Comprobar las restricciones por grupo etario (adulto mayor)")
        
        return True

if __name__ == '__main__':
    test_vital_signs_prefill()
