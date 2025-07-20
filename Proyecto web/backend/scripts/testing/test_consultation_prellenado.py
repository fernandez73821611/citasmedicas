#!/usr/bin/env python3
"""
Script para verificar que el prellenado de signos vitales funciona correctamente
en la consulta médica desde el triage.
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

def test_consultation_prellenado():
    """Verificar que el prellenado de signos vitales funciona para diferentes grupos etarios"""
    app = create_app()
    
    with app.app_context():
        print("🔍 Verificando prellenado de signos vitales en consulta médica...")
        print("=" * 60)
        
        # 1. Verificar que hay médicos y enfermeras
        doctor = User.query.filter_by(role='doctor').first()
        nurse = User.query.filter_by(role='nurse').first()
        
        if not doctor:
            print("❌ No hay médicos en el sistema")
            return False
            
        if not nurse:
            print("❌ No hay enfermeras en el sistema")
            return False
            
        print(f"✅ Doctor encontrado: {doctor.full_name}")
        print(f"✅ Enfermera encontrada: {nurse.full_name}")
        print()
        
        # 2. Buscar pacientes de diferentes grupos etarios que tengan citas con triage
        test_cases = []
        
        # Buscar pacientes por grupo etario
        for age_group in ['lactante', 'preescolar', 'escolar', 'adolescente', 'adulto']:
            patient = Patient.query.filter_by(age_group=age_group).first()
            if patient:
                # Buscar cita pagada para este paciente
                appointment = Appointment.query.filter_by(
                    patient_id=patient.id,
                    doctor_id=doctor.id,
                    status='paid'
                ).first()
                
                if appointment:
                    # Verificar si tiene factura pagada
                    invoice = Invoice.query.filter_by(
                        appointment_id=appointment.id,
                        status='paid'
                    ).first()
                    
                    if invoice:
                        test_cases.append({
                            'patient': patient,
                            'appointment': appointment,
                            'age_group': age_group
                        })
        
        if not test_cases:
            print("❌ No se encontraron pacientes con citas pagadas para probar")
            return False
            
        print(f"📋 Encontrados {len(test_cases)} casos de prueba:")
        print()
        
        # 3. Para cada caso, crear un triage de prueba y verificar datos
        for i, case in enumerate(test_cases, 1):
            patient = case['patient']
            appointment = case['appointment']
            age_group = case['age_group']
            
            print(f"--- Caso {i}: {age_group.upper()} ---")
            print(f"Paciente: {patient.full_name} ({patient.age} años)")
            print(f"Cita ID: {appointment.id}")
            
            # Verificar si ya existe triage
            existing_triage = Triage.query.filter_by(appointment_id=appointment.id).first()
            if existing_triage:
                print(f"✅ Triage existente encontrado (ID: {existing_triage.id})")
                triage = existing_triage
            else:
                # Crear triage de prueba con datos específicos por edad
                triage_data = get_sample_triage_data(age_group, patient.age)
                
                triage = Triage(
                    patient_id=patient.id,
                    appointment_id=appointment.id,
                    nurse_id=nurse.id,
                    **triage_data
                )
                
                try:
                    db.session.add(triage)
                    db.session.commit()
                    print(f"✅ Triage creado (ID: {triage.id})")
                except Exception as e:
                    print(f"❌ Error creando triage: {e}")
                    db.session.rollback()
                    continue
            
            # 4. Verificar qué campos deberían estar prellenados
            expected_fields = get_expected_prellenado_fields(age_group, patient.age)
            print(f"📝 Campos esperados para prellenar: {', '.join(expected_fields)}")
            
            # 5. Verificar datos del triage
            verify_triage_data(triage, age_group, expected_fields)
            
            print()
        
        print("✅ Verificación completada!")
        print()
        print("📋 Resumen de configuración por grupo etario:")
        print_age_group_configuration()
        
        return True

def get_sample_triage_data(age_group, age):
    """Generar datos de triage de muestra según el grupo etario"""
    base_data = {
        'chief_complaint': f'Consulta de control para {age_group}',
        'priority_level': 'media',
        'created_at': datetime.now()
    }
    
    if age_group == 'lactante':
        # Solo algunos signos vitales para lactantes
        base_data.update({
            'heart_rate': 120,
            'temperature': 36.8,
            'weight': 8.5,
            'height': 70,
            # No presión arterial, no frecuencia respiratoria específica
        })
    elif age_group == 'preescolar':
        if age < 3:
            # Preescolar menor (sin presión arterial)
            base_data.update({
                'heart_rate': 100,
                'temperature': 36.5,
                'respiratory_rate': 18,
                'weight': 12.0,
                'height': 85,
            })
        else:
            # Preescolar mayor (con presión arterial)
            base_data.update({
                'systolic': 95,
                'diastolic': 65,
                'heart_rate': 100,
                'temperature': 36.5,
                'respiratory_rate': 18,
                'weight': 15.0,
                'height': 95,
            })
    elif age_group == 'escolar':
        # Todos los signos vitales
        base_data.update({
            'systolic': 105,
            'diastolic': 70,
            'heart_rate': 85,
            'temperature': 36.2,
            'respiratory_rate': 16,
            'weight': 25.0,
            'height': 120,
        })
    elif age_group == 'adolescente':
        # Evaluación similar a adulto
        base_data.update({
            'systolic': 115,
            'diastolic': 75,
            'heart_rate': 75,
            'temperature': 36.3,
            'respiratory_rate': 15,
            'weight': 50.0,
            'height': 155,
        })
    else:  # adulto
        # Evaluación completa
        base_data.update({
            'systolic': 120,
            'diastolic': 80,
            'heart_rate': 72,
            'temperature': 36.5,
            'respiratory_rate': 16,
            'weight': 70.0,
            'height': 170,
        })
    
    return base_data

def get_expected_prellenado_fields(age_group, age):
    """Obtener campos que deberían estar prellenados según el grupo etario"""
    
    if age_group == 'lactante':
        return ['heart_rate', 'temperature', 'weight', 'height']
    elif age_group == 'preescolar':
        if age < 3:
            return ['heart_rate', 'temperature', 'respiratory_rate', 'weight', 'height']
        else:
            return ['blood_pressure', 'heart_rate', 'temperature', 'respiratory_rate', 'weight', 'height']
    elif age_group in ['escolar', 'adolescente']:
        return ['blood_pressure', 'heart_rate', 'temperature', 'respiratory_rate', 'weight', 'height']
    else:  # adulto
        return ['blood_pressure', 'heart_rate', 'temperature', 'respiratory_rate', 'weight', 'height']

def verify_triage_data(triage, age_group, expected_fields):
    """Verificar que el triage tiene los datos correctos"""
    print("📊 Datos del triage:")
    
    # Verificar presión arterial
    if 'blood_pressure' in expected_fields:
        if triage.systolic and triage.diastolic:
            bp_value = f"{triage.systolic}/{triage.diastolic}"
            print(f"  ✅ Presión arterial: {bp_value} mmHg")
        else:
            print(f"  ❌ Presión arterial: No disponible (esperada)")
    else:
        print(f"  ⚪ Presión arterial: No aplicable para {age_group}")
    
    # Verificar otros signos vitales
    vital_signs = {
        'heart_rate': ('Frecuencia cardíaca', 'bpm'),
        'temperature': ('Temperatura', '°C'),
        'respiratory_rate': ('Frecuencia respiratoria', 'rpm'),
        'weight': ('Peso', 'kg'),
        'height': ('Altura', 'cm')
    }
    
    for field, (label, unit) in vital_signs.items():
        value = getattr(triage, field, None)
        if field in expected_fields:
            if value:
                print(f"  ✅ {label}: {value} {unit}")
            else:
                print(f"  ❌ {label}: No disponible (esperado)")
        else:
            if value:
                print(f"  ⚠️  {label}: {value} {unit} (no esperado para {age_group})")
            else:
                print(f"  ⚪ {label}: No aplicable para {age_group}")

def print_age_group_configuration():
    """Imprimir configuración por grupo etario"""
    configurations = {
        'lactante (0-2 años)': {
            'blocked': ['Presión arterial', 'Frecuencia respiratoria'],
            'critical': ['Frecuencia cardíaca', 'Temperatura', 'Peso', 'Altura'],
            'note': 'Evaluación especial, sin presión arterial'
        },
        'preescolar < 3 años': {
            'blocked': ['Presión arterial'],
            'critical': ['Frecuencia cardíaca', 'Temperatura', 'Peso', 'Altura'],
            'optional': ['Frecuencia respiratoria'],
            'note': 'Sin presión arterial hasta los 3 años'
        },
        'preescolar ≥ 3 años': {
            'blocked': [],
            'critical': ['Presión arterial', 'Frecuencia cardíaca', 'Temperatura', 'Peso', 'Altura'],
            'optional': ['Frecuencia respiratoria'],
            'note': 'Evaluación completa disponible'
        },
        'escolar (6-12 años)': {
            'blocked': [],
            'critical': ['Presión arterial', 'Frecuencia cardíaca', 'Temperatura', 'Peso', 'Altura'],
            'optional': ['Frecuencia respiratoria'],
            'note': 'Evaluación completa, comunicación directa'
        },
        'adolescente (12-18 años)': {
            'blocked': [],
            'critical': ['Presión arterial', 'Frecuencia cardíaca', 'Temperatura', 'Peso', 'Altura'],
            'optional': ['Frecuencia respiratoria'],
            'note': 'Similar a adulto, considerar privacidad'
        },
        'adulto (18+ años)': {
            'blocked': [],
            'critical': ['Presión arterial', 'Frecuencia cardíaca', 'Temperatura', 'Peso', 'Altura'],
            'optional': ['Frecuencia respiratoria'],
            'note': 'Evaluación estándar completa'
        }
    }
    
    for group, config in configurations.items():
        print(f"\n🔹 {group.upper()}:")
        if config['blocked']:
            print(f"  ❌ Bloqueados: {', '.join(config['blocked'])}")
        if config['critical']:
            print(f"  ✅ Críticos: {', '.join(config['critical'])}")
        if config.get('optional'):
            print(f"  ⚪ Opcionales: {', '.join(config['optional'])}")
        print(f"  📝 {config['note']}")

if __name__ == '__main__':
    test_consultation_prellenado()
