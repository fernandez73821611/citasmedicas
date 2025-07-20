#!/usr/bin/env python3
"""
Script para verificar que las historias clínicas se muestren correctamente
Solo deben aparecer los pacientes que el doctor actual ha atendido
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.patient import Patient
from app.models.medical_record import MedicalRecord
from app.models.user import User
from app.models.appointment import Appointment

def test_clinical_histories():
    """Verificar que las historias clínicas se filtren correctamente"""
    app = create_app()
    
    with app.app_context():
        print("=== VERIFICACIÓN DE HISTORIAS CLÍNICAS ===\n")
        
        # Obtener doctores
        doctors = User.query.filter_by(role='doctor').all()
        print(f"Doctores encontrados: {len(doctors)}")
        
        for doctor in doctors:
            print(f"\n--- Doctor: {doctor.full_name} ---")
            
            # Método ANTERIOR (incorrecto): Pacientes con citas
            patients_with_appointments = Patient.query.join(Appointment).filter(
                Appointment.doctor_id == doctor.id,
                Patient.is_active == True
            ).distinct().all()
            
            print(f"Pacientes con citas: {len(patients_with_appointments)}")
            
            # Método CORRECTO: Pacientes con consultas realizadas
            patients_with_consultations = Patient.query.join(MedicalRecord).filter(
                MedicalRecord.doctor_id == doctor.id,
                Patient.is_active == True
            ).distinct().all()
            
            print(f"Pacientes con consultas realizadas: {len(patients_with_consultations)}")
            
            # Mostrar diferencia
            if patients_with_appointments:
                print("Pacientes con citas:")
                for patient in patients_with_appointments:
                    has_history = patient.has_medical_history()
                    has_my_consultations = MedicalRecord.query.filter_by(
                        patient_id=patient.id,
                        doctor_id=doctor.id
                    ).count() > 0
                    print(f"  - {patient.full_name}: Historia={has_history}, Mis consultas={has_my_consultations}")
            
            if patients_with_consultations:
                print("Pacientes con consultas del doctor:")
                for patient in patients_with_consultations:
                    my_consultations = MedicalRecord.query.filter_by(
                        patient_id=patient.id,
                        doctor_id=doctor.id
                    ).count()
                    print(f"  - {patient.full_name}: {my_consultations} consultas")
        
        print("\n=== VERIFICACIÓN COMPLETADA ===")

if __name__ == "__main__":
    test_clinical_histories()
