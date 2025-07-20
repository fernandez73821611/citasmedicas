#!/usr/bin/env python3
"""
Script de Verificación del Flujo de Historias Clínicas
Verifica que la lógica del flujo médico funcione correctamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.patient import Patient
from app.models.medical_record import MedicalRecord
from app.models.medical_history import MedicalHistory
from app.models.appointment import Appointment
from app.models.user import User
from datetime import datetime, date

def test_patient_flow():
    """Probar el flujo completo de un paciente"""
    app = create_app()
    
    with app.app_context():
        print("🔍 VERIFICANDO FLUJO DE HISTORIAS CLÍNICAS")
        print("=" * 60)
        
        # Obtener algunos pacientes de prueba
        patients = Patient.query.limit(3).all()
        if not patients:
            print("❌ No hay pacientes en la base de datos")
            return
        
        print(f"📋 Verificando {len(patients)} pacientes...")
        print()
        
        for i, patient in enumerate(patients, 1):
            print(f"👤 PACIENTE {i}: {patient.full_name}")
            print(f"   DNI: {patient.dni}")
            print(f"   Edad: {patient.age} años")
            print(f"   Grupo etario: {patient.age_group}")
            print()
            
            # Verificar estado actual
            print("🔍 ESTADO ACTUAL:")
            
            # Método has_medical_history (problemático)
            has_history_old = patient.has_medical_history()
            print(f"   has_medical_history(): {has_history_old}")
            
            # Contar registros médicos
            records_count = patient.medical_records.count()
            print(f"   Registros médicos: {records_count}")
            
            # Verificar si puede obtener historia clínica
            medical_history = patient.get_medical_history()
            print(f"   get_medical_history(): {medical_history is not None}")
            
            if medical_history:
                print(f"   Número de historia: {medical_history.medical_history_number}")
                print(f"   Fecha apertura: {medical_history.opening_date}")
            
            # Verificar estado para doctor
            patient_status = patient.get_patient_status_for_doctor()
            print(f"   Estado para doctor: {patient_status['expected_action']}")
            print(f"   Es paciente nuevo: {patient_status['is_new_patient']}")
            
            # Verificar citas
            appointments = Appointment.query.filter_by(patient_id=patient.id).all()
            print(f"   Citas totales: {len(appointments)}")
            
            if appointments:
                print("   Citas por doctor:")
                doctors_count = {}
                for apt in appointments:
                    doctor_name = apt.doctor.full_name if apt.doctor else "Doctor desconocido"
                    doctors_count[doctor_name] = doctors_count.get(doctor_name, 0) + 1
                
                for doctor_name, count in doctors_count.items():
                    print(f"     - {doctor_name}: {count} citas")
            
            print()
            
            # VERIFICAR LÓGICA DE FLUJO
            print("🎯 VERIFICACIÓN DE FLUJO:")
            
            if records_count == 0:
                print("   ✅ PACIENTE NUEVO - Debe crear historia clínica")
                expected_action = "create_medical_history"
            else:
                print("   ✅ PACIENTE EXISTENTE - Debe crear nueva consulta")
                expected_action = "new_consultation"
            
            actual_action = patient_status['expected_action']
            if actual_action == expected_action:
                print(f"   ✅ Lógica CORRECTA: {actual_action}")
            else:
                print(f"   ❌ Lógica INCORRECTA: esperado '{expected_action}', actual '{actual_action}'")
            
            print()
            print("-" * 60)
        
        # Verificar doctores
        print()
        print("👨‍⚕️ VERIFICANDO DOCTORES:")
        doctors = User.query.filter_by(role='doctor').all()
        
        for doctor in doctors:
            print(f"   Dr. {doctor.full_name}")
            
            # Verificar historias clínicas que puede ver
            patients_with_history = Patient.query.join(Appointment).filter(
                Appointment.doctor_id == doctor.id
            ).distinct().all()
            
            print(f"   Pacientes atendidos: {len(patients_with_history)}")
            
            # Verificar cuántos tienen historia clínica
            with_history = 0
            for patient in patients_with_history:
                if patient.has_medical_history():
                    with_history += 1
            
            print(f"   Con historia clínica: {with_history}")
            print()

def test_clinical_histories_view():
    """Probar la vista de historias clínicas"""
    app = create_app()
    
    with app.app_context():
        print("🏥 VERIFICANDO VISTA DE HISTORIAS CLÍNICAS")
        print("=" * 60)
        
        doctors = User.query.filter_by(role='doctor').all()
        
        for doctor in doctors:
            print(f"👨‍⚕️ Dr. {doctor.full_name}")
            
            # Simular la consulta de clinical_histories
            patients_with_citas = Patient.query.join(Appointment).filter(
                Appointment.doctor_id == doctor.id
            ).distinct().all()
            
            print(f"   Pacientes con citas: {len(patients_with_citas)}")
            
            # Filtrar solo los que tienen historia clínica
            patients_with_history = []
            for patient in patients_with_citas:
                medical_history = patient.get_medical_history()
                if medical_history:
                    patients_with_history.append({
                        'patient': patient,
                        'medical_history': medical_history
                    })
            
            print(f"   Pacientes con historia clínica: {len(patients_with_history)}")
            
            if patients_with_history:
                print("   Historias clínicas:")
                for data in patients_with_history:
                    patient = data['patient']
                    history = data['medical_history']
                    print(f"     - {patient.full_name} (N° {history.medical_history_number})")
            else:
                print("   ✅ No hay historias clínicas (correcto para pacientes nuevos)")
            
            print()

if __name__ == "__main__":
    print("🚀 INICIANDO VERIFICACIÓN DEL FLUJO DE HISTORIAS CLÍNICAS")
    print()
    
    test_patient_flow()
    test_clinical_histories_view()
    
    print("✅ VERIFICACIÓN COMPLETADA")
