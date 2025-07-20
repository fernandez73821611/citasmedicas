#!/usr/bin/env python
"""
Script para crear pacientes de muestra para cada grupo etario
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, date
from app import create_app, db
from app.models.patient import Patient

def create_sample_patients():
    """Crear pacientes de muestra para cada grupo etario"""
    
    app = create_app()
    with app.app_context():
        
        # Fecha base para calcular edades
        today = date.today()
        
        # Lista de pacientes a crear
        patients_data = [
            {
                # LACTANTE (1 año)
                'first_name': 'Sofia',
                'last_name': 'Ramírez Mendoza',
                'dni': '12345001',
                'birth_date': date(today.year - 1, 3, 15),  # 1 año
                'gender': 'F',
                'phone': '987654321',
                'email': None,  # Los lactantes no tienen email
                'address': 'Av. Los Rosales 123, Bagua Grande',
                'emergency_contact_name': 'María Mendoza',
                'emergency_contact_phone': '987654322',
                'emergency_contact_relationship': 'Abuela',
                'guardian_name': 'Carlos Ramírez',
                'guardian_dni': '41234567',
                'guardian_phone': '987654323',
                'guardian_relationship': 'Padre'
            },
            {
                # PREESCOLAR (4 años)
                'first_name': 'Diego',
                'last_name': 'Torres Vásquez',
                'dni': '12345002',
                'birth_date': date(today.year - 4, 8, 20),  # 4 años
                'gender': 'M',
                'phone': '987654324',
                'email': None,
                'address': 'Jr. San Martín 456, Bagua Grande',
                'emergency_contact_name': 'Ana Vásquez',
                'emergency_contact_phone': '987654325',
                'emergency_contact_relationship': 'Madre',
                'guardian_name': 'Luis Torres',
                'guardian_dni': '42345678',
                'guardian_phone': '987654326',
                'guardian_relationship': 'Padre'
            },
            {
                # ESCOLAR (9 años)
                'first_name': 'Valeria',
                'last_name': 'Gonzales Ruiz',
                'dni': '12345003',
                'birth_date': date(today.year - 9, 12, 10),  # 9 años
                'gender': 'F',
                'phone': '987654327',
                'email': None,
                'address': 'Calle Los Pinos 789, Bagua Grande',
                'emergency_contact_name': 'Pedro Gonzales',
                'emergency_contact_phone': '987654328',
                'emergency_contact_relationship': 'Padre',
                'guardian_name': 'Elena Ruiz',
                'guardian_dni': '43456789',
                'guardian_phone': '987654329',
                'guardian_relationship': 'Madre'
            },
            {
                # ADOLESCENTE (15 años)
                'first_name': 'Mateo',
                'last_name': 'Castillo Pérez',
                'dni': '12345004',
                'birth_date': date(today.year - 15, 5, 25),  # 15 años
                'gender': 'M',
                'phone': '987654330',
                'email': 'mateo.castillo@estudiante.com',
                'address': 'Av. Grau 321, Bagua Grande',
                'emergency_contact_name': 'Rosa Pérez',
                'emergency_contact_phone': '987654331',
                'emergency_contact_relationship': 'Madre',
                'guardian_name': 'Miguel Castillo',
                'guardian_dni': '44567890',
                'guardian_phone': '987654332',
                'guardian_relationship': 'Padre'
            },
            {
                # ADOLESCENTE (17 años)
                'first_name': 'Camila',
                'last_name': 'Herrera López',
                'dni': '12345005',
                'birth_date': date(today.year - 17, 11, 5),  # 17 años
                'gender': 'F',
                'phone': '987654333',
                'email': 'camila.herrera@estudiante.com',
                'address': 'Jr. Bolívar 654, Bagua Grande',
                'emergency_contact_name': 'Jorge Herrera',
                'emergency_contact_phone': '987654334',
                'emergency_contact_relationship': 'Padre',
                'guardian_name': 'Carmen López',
                'guardian_dni': '45678901',
                'guardian_phone': '987654335',
                'guardian_relationship': 'Madre'
            },
            {
                # ADULTO (25 años)
                'first_name': 'Andrea',
                'last_name': 'Morales Silva',
                'dni': '12345006',
                'birth_date': date(today.year - 25, 2, 14),  # 25 años
                'gender': 'F',
                'phone': '987654336',
                'email': 'andrea.morales@gmail.com',
                'address': 'Calle Libertad 987, Bagua Grande',
                'emergency_contact_name': 'Roberto Morales',
                'emergency_contact_phone': '987654337',
                'emergency_contact_relationship': 'Hermano',
                'guardian_name': None,  # No necesita apoderado
                'guardian_dni': None,
                'guardian_phone': None,
                'guardian_relationship': None
            },
            {
                # ADULTO (45 años)
                'first_name': 'Fernando',
                'last_name': 'Delgado Chávez',
                'dni': '12345007',
                'birth_date': date(today.year - 45, 7, 30),  # 45 años
                'gender': 'M',
                'phone': '987654338',
                'email': 'fernando.delgado@hotmail.com',
                'address': 'Av. Amazonas 147, Bagua Grande',
                'emergency_contact_name': 'Patricia Chávez',
                'emergency_contact_phone': '987654339',
                'emergency_contact_relationship': 'Esposa',
                'guardian_name': None,  # No necesita apoderado
                'guardian_dni': None,
                'guardian_phone': None,
                'guardian_relationship': None
            },
            {
                # ADULTO MAYOR (70 años)
                'first_name': 'Rosa',
                'last_name': 'Villanueva Romero',
                'dni': '12345008',
                'birth_date': date(today.year - 70, 4, 12),  # 70 años
                'gender': 'F',
                'phone': '987654340',
                'email': None,  # Persona mayor sin email
                'address': 'Jr. Amazonas 258, Bagua Grande',
                'emergency_contact_name': 'Carlos Villanueva',
                'emergency_contact_phone': '987654341',
                'emergency_contact_relationship': 'Hijo',
                'guardian_name': None,  # No necesita apoderado
                'guardian_dni': None,
                'guardian_phone': None,
                'guardian_relationship': None
            }
        ]
        
        print("🏥 Creando pacientes de muestra para cada grupo etario...")
        print("=" * 60)
        
        created_patients = []
        
        for patient_data in patients_data:
            # Verificar si ya existe un paciente con este DNI
            existing_patient = Patient.query.filter_by(dni=patient_data['dni']).first()
            
            if existing_patient:
                print(f"⚠️  Paciente con DNI {patient_data['dni']} ya existe: {existing_patient.full_name}")
                continue
                
            # Crear nuevo paciente
            patient = Patient(
                first_name=patient_data['first_name'],
                last_name=patient_data['last_name'],
                dni=patient_data['dni'],
                birth_date=patient_data['birth_date'],
                gender=patient_data['gender'],
                phone=patient_data['phone'],
                email=patient_data['email'],
                address=patient_data['address'],
                emergency_contact_name=patient_data['emergency_contact_name'],
                emergency_contact_phone=patient_data['emergency_contact_phone'],
                emergency_contact_relationship=patient_data['emergency_contact_relationship'],
                guardian_name=patient_data['guardian_name'],
                guardian_dni=patient_data['guardian_dni'],
                guardian_phone=patient_data['guardian_phone'],
                guardian_relationship=patient_data['guardian_relationship']
            )
            
            db.session.add(patient)
            created_patients.append(patient)
            
            # Información del paciente creado
            print(f"✅ {patient.full_name} - DNI: {patient.dni}")
            print(f"   📅 Edad: {patient.age} años ({patient.age_group_label})")
            print(f"   📍 Dirección: {patient.address}")
            print(f"   📞 Teléfono: {patient.phone}")
            if patient.email:
                print(f"   ✉️  Email: {patient.email}")
            if patient.guardian_name:
                print(f"   👤 Apoderado: {patient.guardian_name} ({patient.guardian_relationship})")
            print(f"   🚨 Contacto de emergencia: {patient.emergency_contact_name} ({patient.emergency_contact_relationship})")
            print("-" * 60)
        
        # Confirmar los cambios
        db.session.commit()
        
        print(f"\n🎉 Se crearon {len(created_patients)} pacientes exitosamente!")
        print("\n📊 Resumen por grupo etario:")
        
        # Mostrar resumen por grupo etario
        age_groups = {}
        for patient in created_patients:
            group = patient.age_group_label
            if group not in age_groups:
                age_groups[group] = []
            age_groups[group].append(patient)
        
        for group, patients in age_groups.items():
            print(f"\n{group}:")
            for patient in patients:
                print(f"  - {patient.full_name} ({patient.age} años)")
        
        print(f"\n✨ ¡Pacientes de muestra creados exitosamente!")
        print("Ahora puedes probar el sistema de triage con pacientes de diferentes edades.")
        
        return created_patients

if __name__ == '__main__':
    try:
        patients = create_sample_patients()
        print(f"\n🏁 Proceso completado. {len(patients)} pacientes creados.")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
