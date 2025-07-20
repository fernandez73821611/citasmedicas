#!/usr/bin/env python3
"""
Script para probar el flujo completo de triage y consulta con prellenado
incluyendo todos los grupos etarios.
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

def create_test_appointment_with_triage():
    """Crear una cita de prueba con triage para verificar el prellenado"""
    app = create_app()
    
    with app.app_context():
        print("🏥 Creando cita de prueba con triage para verificar prellenado...")
        print("=" * 70)
        
        # 1. Obtener usuarios
        doctor = User.query.filter_by(role='doctor').first()
        nurse = User.query.filter_by(role='nurse').first()
        
        if not doctor or not nurse:
            print("❌ No hay médicos o enfermeras en el sistema")
            return False
        
        # 2. Buscar un paciente escolar (que debería tener todos los campos)
        patient = Patient.query.filter_by(age_group='escolar').first()
        
        if not patient:
            print("❌ No hay pacientes escolares en el sistema")
            return False
        
        print(f"✅ Paciente seleccionado: {patient.full_name}")
        print(f"   Edad: {patient.age} años ({patient.age_group_label})")
        print(f"   DNI: {patient.dni}")
        print()
        
        # 3. Crear una cita nueva
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_date=date.today(),
            appointment_time=datetime.now().time(),
            reason='Consulta de prueba para verificar prellenado',
            status='paid',
            created_at=datetime.now()
        )
        
        try:
            db.session.add(appointment)
            db.session.flush()  # Para obtener el ID
            
            # 4. Crear factura pagada
            invoice = Invoice(
                appointment_id=appointment.id,
                patient_id=patient.id,
                total_amount=50.00,
                status='paid',
                issue_date=date.today(),
                created_at=datetime.now()
            )
            
            db.session.add(invoice)
            db.session.flush()
            
            print(f"✅ Cita creada (ID: {appointment.id})")
            print(f"✅ Factura creada y pagada (ID: {invoice.id})")
            print()
            
            # 5. Crear triage con datos completos
            triage_data = {
                'patient_id': patient.id,
                'appointment_id': appointment.id,
                'nurse_id': nurse.id,
                'chief_complaint': 'Consulta de control - prueba de prellenado',
                'priority_level': 'media',
                
                # Signos vitales para escolar (todos los campos)
                'blood_pressure_systolic': 110,
                'blood_pressure_diastolic': 70,
                'heart_rate': 85,
                'temperature': 36.8,
                'respiratory_rate': 16,
                'weight': 35.0,
                'height': 140,
                'oxygen_saturation': 98,
                
                'status': 'completed',
                'created_at': datetime.now()
            }
            
            triage = Triage(**triage_data)
            db.session.add(triage)
            
            # 6. Cambiar estado de la cita
            appointment.status = 'ready_for_doctor'
            
            db.session.commit()
            
            print(f"✅ Triage creado (ID: {triage.id})")
            print("✅ Cita marcada como 'ready_for_doctor'")
            print()
            
            # 7. Mostrar datos que deberían prellenarse
            print("📋 DATOS PARA PRELLENADO EN CONSULTA MÉDICA:")
            print("-" * 50)
            print(f"🩺 Presión arterial: {triage.blood_pressure_systolic}/{triage.blood_pressure_diastolic} mmHg")
            print(f"💓 Frecuencia cardíaca: {triage.heart_rate} bpm")
            print(f"🌡️  Temperatura: {triage.temperature}°C")
            print(f"🫁 Frecuencia respiratoria: {triage.respiratory_rate} rpm")
            print(f"⚖️  Peso: {triage.weight} kg")
            print(f"📏 Altura: {triage.height} cm")
            print(f"🫀 Saturación de oxígeno: {triage.oxygen_saturation}%")
            print()
            
            # 8. URLs para probar
            print("🔗 URLS PARA PROBAR:")
            print("-" * 30)
            print(f"Triage (enfermería): /nurse/triage/appointment/{appointment.id}")
            print(f"Consulta (doctor): /doctor/consultation/{patient.id}/new?appointment_id={appointment.id}")
            print()
            
            # 9. Verificar grupos etarios
            print("👥 VERIFICANDO TODOS LOS GRUPOS ETARIOS:")
            print("-" * 40)
            verify_all_age_groups()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")
            return False

def verify_all_age_groups():
    """Verificar que todos los grupos etarios estén funcionando"""
    app = create_app()
    
    with app.app_context():
        # Contar pacientes por grupo etario
        age_groups = {}
        patients = Patient.query.all()
        
        for patient in patients:
            group = patient.age_group
            if group not in age_groups:
                age_groups[group] = []
            age_groups[group].append(patient)
        
        # Mostrar estadísticas
        for group in ['lactante', 'preescolar', 'escolar', 'adolescente', 'adulto', 'adulto_mayor']:
            count = len(age_groups.get(group, []))
            if count > 0:
                example = age_groups[group][0]
                restrictions = get_group_restrictions(group, example.age)
                print(f"✅ {group.upper()}: {count} pacientes")
                print(f"   Ejemplo: {example.full_name} ({example.age} años)")
                print(f"   Restricciones: {restrictions}")
            else:
                print(f"⚠️  {group.upper()}: 0 pacientes")
            print()

def get_group_restrictions(group, age):
    """Obtener restricciones por grupo etario"""
    if group == 'lactante':
        return "❌ Presión arterial, ❌ FR específica, ✅ FC, temperatura, peso, altura"
    elif group == 'preescolar':
        if age < 3:
            return "❌ Presión arterial, ✅ FC, temperatura, peso, altura, FR"
        else:
            return "✅ Todos los signos vitales disponibles"
    elif group in ['escolar', 'adolescente']:
        return "✅ Todos los signos vitales disponibles"
    elif group == 'adulto_mayor':
        return "✅ Todos disponibles con tolerancias especiales"
    else:  # adulto
        return "✅ Evaluación estándar completa"

if __name__ == '__main__':
    create_test_appointment_with_triage()
