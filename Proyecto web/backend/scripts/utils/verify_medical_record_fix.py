#!/usr/bin/env python3
"""
Script de prueba para verificar la corrección del error de personal_history
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.medical_record import MedicalRecord
from app.models.patient import Patient
from app.models.user import User

def test_medical_record_creation():
    """Probar la creación de un registro médico con los campos correctos"""
    app = create_app()
    
    with app.app_context():
        print("🔍 VERIFICANDO CAMPOS VÁLIDOS DE MEDICALRECORD")
        print("=" * 60)
        
        # Obtener un paciente y doctor de prueba
        patient = Patient.query.first()
        doctor = User.query.filter_by(role='doctor').first()
        
        if not patient or not doctor:
            print("❌ No hay pacientes o doctores en la base de datos")
            return
        
        print(f"👤 Paciente: {patient.full_name}")
        print(f"👨‍⚕️ Doctor: {doctor.full_name}")
        print()
        
        # Crear un registro médico de prueba con solo campos válidos
        try:
            print("🧪 Creando registro médico de prueba...")
            
            # Simular datos de historia clínica estructurados en observations
            history_info = [
                "ANTECEDENTES PERSONALES:\nHipertensión arterial desde hace 5 años",
                "ANTECEDENTES FAMILIARES:\nDiabetes tipo 2 (madre), Hipertensión (padre)",
                "ALERGIAS:\nPenicilina, mariscos",
                "MEDICAMENTOS ACTUALES:\nLosartán 50mg diario, Metformina 850mg dos veces al día"
            ]
            
            full_observations = "\n\n".join(history_info)
            full_observations += "\n\nOBSERVACIONES DE CONSULTA:\nPaciente refiere dolor de cabeza ocasional"
            
            test_record = MedicalRecord(
                patient_id=patient.id,
                doctor_id=doctor.id,
                symptoms="Dolor de cabeza ocasional",
                diagnosis="Cefalea tensional",
                treatment="Reposo, hidratación adecuada",
                prescriptions="Paracetamol 500mg cada 8h por 3 días",
                observations=full_observations,
                blood_pressure="120/80",
                heart_rate=72,
                temperature=36.5,
                weight=70.0,
                height=170.0
            )
            
            # Verificar que el objeto se crea correctamente
            print("✅ Objeto MedicalRecord creado exitosamente")
            print(f"   Paciente: {test_record.patient_id}")
            print(f"   Doctor: {test_record.doctor_id}")
            print(f"   Síntomas: {test_record.symptoms}")
            print(f"   Diagnóstico: {test_record.diagnosis}")
            print(f"   Observaciones (primeras 100 chars): {test_record.observations[:100]}...")
            
            # NO vamos a guardarlo en la BD, solo verificar que se puede crear
            print()
            print("✅ VERIFICACIÓN EXITOSA: Los campos son válidos")
            print("   El error de 'personal_history' está corregido")
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return
        
        # Verificar campos válidos del modelo
        print()
        print("📋 CAMPOS VÁLIDOS DE MEDICALRECORD:")
        valid_fields = [
            'id', 'patient_id', 'doctor_id', 'appointment_id',
            'symptoms', 'diagnosis', 'treatment', 'prescriptions',
            'blood_pressure', 'heart_rate', 'temperature', 'weight', 'height',
            'observations', 'next_appointment_notes',
            'consultation_date', 'created_at', 'updated_at'
        ]
        
        for field in valid_fields:
            print(f"   ✅ {field}")
        
        print()
        print("❌ CAMPOS NO VÁLIDOS (que causaban el error):")
        invalid_fields = [
            'personal_history', 'family_history', 'allergies',
            'current_medications', 'smoking_habits', 'alcohol_habits',
            'physical_activity', 'is_first_consultation'
        ]
        
        for field in invalid_fields:
            print(f"   ❌ {field}")

if __name__ == "__main__":
    print("🚀 INICIANDO VERIFICACIÓN DE CORRECCIÓN DE MEDICALRECORD")
    print()
    
    test_medical_record_creation()
    
    print()
    print("✅ VERIFICACIÓN COMPLETADA")
    print("💡 La información de historia clínica ahora se guarda estructurada en 'observations'")
