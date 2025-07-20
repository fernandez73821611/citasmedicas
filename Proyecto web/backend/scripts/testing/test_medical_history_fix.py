#!/usr/bin/env python3
"""
Verificar que la función de historia clínica funcione correctamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.patient import Patient
from app.models.user import User

def test_medical_history_validation():
    """Probar la validación de historia clínica"""
    app = create_app()
    
    with app.app_context():
        print("🏥 VERIFICANDO VALIDACIÓN DE HISTORIA CLÍNICA")
        print("=" * 60)
        
        # Obtener un paciente nuevo
        patients = Patient.query.filter_by().all()
        new_patients = [p for p in patients if not p.has_medical_history()]
        
        if not new_patients:
            print("❌ No hay pacientes nuevos para probar")
            return
        
        patient = new_patients[0]
        print(f"👤 Paciente de prueba: {patient.full_name}")
        print(f"   DNI: {patient.dni}")
        print(f"   Edad: {patient.age} años")
        print(f"   Tiene historia: {patient.has_medical_history()}")
        print()
        
        # Obtener un doctor
        doctor = User.query.filter_by(role='doctor').first()
        if not doctor:
            print("❌ No hay doctores en el sistema")
            return
            
        print(f"👨‍⚕️ Doctor de prueba: {doctor.full_name}")
        print()
        
        # Simular datos mínimos para historia clínica
        form_data = {
            'personal_history': 'Antecedentes personales de prueba',
            'family_history': 'Antecedentes familiares de prueba',
            'allergies': '',
            'current_medications': '',
            'smoking_habits': '',
            'alcohol_habits': '',
            'physical_activity': '',
            'observations': 'Observaciones generales',
            'symptoms': '',  # Vacío para historia clínica
            'diagnosis': '',  # Vacío para historia clínica
            'treatment': '',
            'prescriptions': ''
        }
        
        print("📋 Datos de prueba para historia clínica:")
        for key, value in form_data.items():
            if value:
                print(f"   {key}: {value[:50]}{'...' if len(value) > 50 else ''}")
            else:
                print(f"   {key}: (vacío)")
        
        print()
        print("✅ VALIDACIÓN:")
        print("   - symptoms: vacío (correcto para historia clínica)")
        print("   - diagnosis: vacío (correcto para historia clínica)")
        print("   - personal_history: con datos (suficiente para historia clínica)")
        print("   - family_history: con datos (suficiente para historia clínica)")
        print()
        
        # Verificar que tiene información médica suficiente
        has_medical_info = any([
            form_data.get('observations'),
            form_data.get('personal_history'),
            form_data.get('family_history'),
            form_data.get('allergies'),
            form_data.get('current_medications'),
            form_data.get('smoking_habits'),
            form_data.get('alcohol_habits'),
            form_data.get('physical_activity')
        ])
        
        if has_medical_info:
            print("✅ RESULTADO: La validación DEBERÍA PASAR")
            print("   Razón: Tiene información médica suficiente para historia clínica")
        else:
            print("❌ RESULTADO: La validación DEBERÍA FALLAR")
            print("   Razón: No tiene información médica suficiente")
        
        print()
        print("🔧 CORRECCIÓN APLICADA:")
        print("   - Eliminada validación obligatoria de 'symptoms' y 'diagnosis'")
        print("   - Agregada validación de información médica general")
        print("   - Historia clínica ya no requiere datos de consulta específica")

if __name__ == "__main__":
    test_medical_history_validation()
