#!/usr/bin/env python3
"""
Script para probar el sistema completo con todos los grupos etarios,
incluyendo el nuevo grupo de adulto mayor.
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

def test_all_age_groups():
    """Probar todos los grupos etarios incluyendo adulto mayor"""
    app = create_app()
    
    with app.app_context():
        print("🔍 Verificando todos los grupos etarios...")
        print("=" * 60)
        
        # 1. Verificar que hay médicos y enfermeras
        doctor = User.query.filter_by(role='doctor').first()
        nurse = User.query.filter_by(role='nurse').first()
        
        if not doctor or not nurse:
            print("❌ No hay médicos o enfermeras en el sistema")
            return False
            
        print(f"✅ Doctor: {doctor.full_name}")
        print(f"✅ Enfermera: {nurse.full_name}")
        print()
        
        # 2. Revisar todos los grupos etarios
        age_groups = {
            'lactante': (0, 2),
            'preescolar': (2, 6), 
            'escolar': (6, 12),
            'adolescente': (12, 18),
            'adulto': (18, 65),
            'adulto_mayor': (65, 90)
        }
        
        print("📊 Grupos etarios definidos:")
        for group, (min_age, max_age) in age_groups.items():
            print(f"  • {group}: {min_age}-{max_age} años")
        print()
        
        # 3. Verificar pacientes existentes por grupo
        print("👥 Pacientes existentes por grupo:")
        for group_name in age_groups.keys():
            patients = Patient.query.filter_by(age_group=group_name).all()
            count = len(patients)
            print(f"  • {group_name}: {count} pacientes")
            
            if patients:
                for patient in patients[:3]:  # Mostrar máximo 3
                    print(f"    - {patient.full_name} ({patient.age} años)")
                if count > 3:
                    print(f"    ... y {count - 3} más")
        print()
        
        # 4. Crear pacientes de prueba si faltan grupos
        print("🛠️  Creando pacientes de prueba para grupos faltantes...")
        test_patients_created = 0
        
        for group_name, (min_age, max_age) in age_groups.items():
            existing = Patient.query.filter_by(age_group=group_name).first()
            if not existing:
                # Calcular fecha de nacimiento para tener la edad correcta
                target_age = min_age + 1  # Un año más que el mínimo
                birth_year = date.today().year - target_age
                birth_date = date(birth_year, 6, 15)  # 15 de junio
                
                # Crear paciente de prueba
                patient = Patient(
                    first_name=f"Test {group_name.title()}",
                    last_name="Grupo Etario",
                    dni=f"TEST{group_name.upper()[:4]}{target_age:02d}",
                    birth_date=birth_date,
                    gender='M' if target_age % 2 == 0 else 'F',
                    phone=f"999{target_age:06d}",
                    address=f"Dirección de prueba para {group_name}"
                )
                
                try:
                    db.session.add(patient)
                    db.session.commit()
                    print(f"  ✅ Creado: {patient.full_name} ({patient.age} años, {patient.age_group})")
                    test_patients_created += 1
                except Exception as e:
                    print(f"  ❌ Error creando paciente para {group_name}: {e}")
                    db.session.rollback()
        
        if test_patients_created == 0:
            print("  ℹ️  No se necesitaron crear pacientes de prueba")
        print()
        
        # 5. Verificar funcionalidad del grupo etario
        print("🔬 Verificando funcionalidad por grupo etario:")
        
        for group_name in age_groups.keys():
            patient = Patient.query.filter_by(age_group=group_name).first()
            if patient:
                print(f"  📋 {group_name.upper()} - {patient.full_name}:")
                print(f"    - Edad: {patient.age} años")
                print(f"    - Grupo detectado: {patient.age_group}")
                print(f"    - Etiqueta: {patient.age_group_label}")
                print(f"    - Es menor: {patient.is_minor}")
                
                # Verificar restricciones específicas
                restrictions = get_age_specific_restrictions(group_name, patient.age)
                if restrictions['blocked']:
                    print(f"    - Campos bloqueados: {', '.join(restrictions['blocked'])}")
                if restrictions['critical']:
                    print(f"    - Campos críticos: {', '.join(restrictions['critical'])}")
                print()
        
        # 6. Resumen de configuración
        print("📋 CONFIGURACIÓN COMPLETA POR GRUPO ETARIO:")
        print_detailed_age_configuration()
        
        return True

def get_age_specific_restrictions(age_group, age):
    """Obtener restricciones específicas por grupo etario"""
    
    if age_group == 'lactante':
        return {
            'blocked': ['Presión arterial', 'Frecuencia respiratoria específica'],
            'critical': ['Frecuencia cardíaca', 'Temperatura', 'Peso', 'Altura'],
            'special_fields': ['Alimentación', 'Sueño', 'Irritabilidad', 'Fontanela'],
            'note': 'Sin presión arterial. Peso y temperatura críticos.'
        }
    elif age_group == 'preescolar':
        if age < 3:
            return {
                'blocked': ['Presión arterial'],
                'critical': ['Frecuencia cardíaca', 'Temperatura', 'Peso', 'Altura'],
                'special_fields': ['Desarrollo psicomotor', 'Comportamiento social'],
                'note': 'Sin presión arterial hasta los 3 años.'
            }
        else:
            return {
                'blocked': [],
                'critical': ['Presión arterial', 'Frecuencia cardíaca', 'Temperatura', 'Peso', 'Altura'],
                'special_fields': ['Desarrollo psicomotor', 'Estado vacunal'],
                'note': 'Evaluación completa disponible.'
            }
    elif age_group == 'escolar':
        return {
            'blocked': [],
            'critical': ['Presión arterial', 'Frecuencia cardíaca', 'Temperatura', 'Peso', 'Altura'],
            'special_fields': ['Rendimiento escolar', 'Actividad física'],
            'note': 'Evaluación completa. Comunicación directa posible.'
        }
    elif age_group == 'adolescente':
        return {
            'blocked': [],
            'critical': ['Presión arterial', 'Frecuencia cardíaca', 'Temperatura'],
            'special_fields': ['Privacidad', 'Desarrollo puberal', 'Conductas de riesgo'],
            'note': 'Similar a adulto. Considerar privacidad y autonomía.'
        }
    elif age_group == 'adulto_mayor':
        return {
            'blocked': [],
            'critical': ['Presión arterial (tolerancia especial)', 'Frecuencia cardíaca (rango amplio)', 'Temperatura', 'Peso'],
            'special_fields': ['Movilidad', 'Estado cognitivo', 'Riesgo caídas', 'Polifarmacia'],
            'note': 'Tolerancias especiales. Vigilar comorbilidades y polifarmacia.'
        }
    else:  # adulto
        return {
            'blocked': [],
            'critical': ['Presión arterial', 'Frecuencia cardíaca', 'Temperatura', 'Peso', 'Altura'],
            'special_fields': [],
            'note': 'Evaluación estándar completa.'
        }

def print_detailed_age_configuration():
    """Imprimir configuración detallada por grupo etario"""
    
    configurations = {
        'LACTANTE (0-2 años)': {
            'vital_signs': {
                'blocked': ['Presión arterial', 'Frecuencia respiratoria'],
                'critical': ['FC: 100-160 bpm', 'Temp: 36.5-37.8°C', 'Peso', 'Altura']
            },
            'special_evaluation': ['Alimentación', 'Patrón de sueño', 'Irritabilidad', 'Fontanela'],
            'pain_scale': 'Conductual (observación)',
            'guardian': 'Obligatorio'
        },
        'PREESCOLAR < 3 años': {
            'vital_signs': {
                'blocked': ['Presión arterial'],
                'critical': ['FC: 90-130 bpm', 'Temp: 36.0-37.5°C', 'Peso', 'Altura']
            },
            'special_evaluation': ['Desarrollo psicomotor', 'Comportamiento'],
            'pain_scale': 'Conductual',
            'guardian': 'Obligatorio'
        },
        'PREESCOLAR ≥ 3 años': {
            'vital_signs': {
                'blocked': [],
                'critical': ['PA: 85-110/55-75 mmHg', 'FC: 90-130 bpm', 'Temp: 36.0-37.5°C', 'Peso', 'Altura']
            },
            'special_evaluation': ['Desarrollo psicomotor', 'Estado vacunal'],
            'pain_scale': 'Caritas',
            'guardian': 'Obligatorio'
        },
        'ESCOLAR (6-12 años)': {
            'vital_signs': {
                'blocked': [],
                'critical': ['PA: 90-120/60-80 mmHg', 'FC: 70-110 bpm', 'Temp: 36.0-37.5°C', 'Peso', 'Altura']
            },
            'special_evaluation': ['Rendimiento escolar', 'Actividad física'],
            'pain_scale': 'Numérica (0-10)',
            'guardian': 'Obligatorio'
        },
        'ADOLESCENTE (12-18 años)': {
            'vital_signs': {
                'blocked': [],
                'critical': ['PA: 90-130/60-85 mmHg', 'FC: 60-100 bpm', 'Temp: 36.0-37.5°C']
            },
            'special_evaluation': ['Privacidad', 'Desarrollo puberal', 'Conductas de riesgo'],
            'pain_scale': 'Numérica (0-10)',
            'guardian': 'Obligatorio (puede requerir privacidad)'
        },
        'ADULTO (18-65 años)': {
            'vital_signs': {
                'blocked': [],
                'critical': ['PA: 90-140/60-90 mmHg', 'FC: 60-100 bpm', 'Temp: 36.0-37.5°C']
            },
            'special_evaluation': [],
            'pain_scale': 'Numérica (0-10)',
            'guardian': 'No requerido'
        },
        'ADULTO MAYOR (65+ años)': {
            'vital_signs': {
                'blocked': [],
                'critical': ['PA: 90-140/60-90 mmHg (tolerancia hasta 140/90)', 'FC: 50-90 bpm', 'Temp: 35.5-37.0°C', 'Peso']
            },
            'special_evaluation': ['Movilidad', 'Estado cognitivo', 'Riesgo de caídas', 'Estado funcional', 'Polifarmacia'],
            'pain_scale': 'Numérica (0-10)',
            'guardian': 'No requerido (puede necesitar acompañante)'
        }
    }
    
    for group, config in configurations.items():
        print(f"\n🔹 {group}:")
        print(f"  📊 Signos vitales:")
        if config['vital_signs']['blocked']:
            print(f"    ❌ Bloqueados: {', '.join(config['vital_signs']['blocked'])}")
        print(f"    ✅ Críticos: {', '.join(config['vital_signs']['critical'])}")
        
        if config['special_evaluation']:
            print(f"  🔍 Evaluación especial: {', '.join(config['special_evaluation'])}")
        
        print(f"  😷 Escala dolor: {config['pain_scale']}")
        print(f"  👥 Tutor: {config['guardian']}")

if __name__ == '__main__':
    test_all_age_groups()
