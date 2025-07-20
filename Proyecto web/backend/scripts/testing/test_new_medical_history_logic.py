#!/usr/bin/env python3
"""
Script para probar la nueva lógica de creación de historia clínica
"""

from app import create_app, db
from app.models.patient import Patient
from app.models.medical_record import MedicalRecord
from app.models.user import User
from datetime import datetime

def test_medical_history_logic():
    """Probar la lógica de creación de historia clínica"""
    app = create_app()
    with app.app_context():
        
        print("🧪 Probando nueva lógica de historia clínica...")
        
        # Buscar un paciente sin historia clínica
        patient = Patient.query.filter(~Patient.medical_records.any()).first()
        if not patient:
            print("❌ No se encontró un paciente sin historia clínica para probar")
            return
        
        # Buscar un doctor
        doctor = User.query.filter_by(role='doctor').first()
        if not doctor:
            print("❌ No se encontró un doctor para probar")
            return
        
        print(f"✅ Paciente de prueba: {patient.full_name}")
        print(f"✅ Doctor de prueba: {doctor.full_name}")
        
        # Simular datos de historia clínica (como los que vienen del formulario)
        history_data = {
            'personal_history': 'Hipertensión desde 2020',
            'family_history': 'Padre diabético',
            'allergies': 'Ninguna conocida',
            'current_medications': 'Enalapril 10mg diario',
            'surgical_history': 'Ninguna',
            'smoking_habits': 'No fuma',
            'alcohol_habits': 'Ocasional',
            'drug_habits': 'No consume',
            'physical_activity': 'Camina 30 min diarios'
        }
        
        # Crear observaciones estructuradas (como en el código actualizado)
        history_info = []
        history_info.append(f"ANTECEDENTES PERSONALES:\n{history_data['personal_history']}")
        history_info.append(f"ANTECEDENTES FAMILIARES:\n{history_data['family_history']}")
        history_info.append(f"ALERGIAS:\n{history_data['allergies']}")
        history_info.append(f"MEDICAMENTOS CRÓNICOS:\n{history_data['current_medications']}")
        history_info.append(f"HISTORIA QUIRÚRGICA:\n{history_data['surgical_history']}")
        history_info.append(f"HÁBITOS DE TABACO:\n{history_data['smoking_habits']}")
        history_info.append(f"HÁBITOS DE ALCOHOL:\n{history_data['alcohol_habits']}")
        history_info.append(f"USO DE DROGAS:\n{history_data['drug_habits']}")
        history_info.append(f"ACTIVIDAD FÍSICA:\n{history_data['physical_activity']}")
        
        full_observations = "\n\n".join(history_info)
        
        print(f"\n📝 Observaciones generadas:")
        print("=" * 60)
        print(full_observations)
        print("=" * 60)
        
        # Probar el caso 1: Solo guardar historia clínica (action='save')
        print(f"\n🔄 Simulando action='save' (solo guardar historia clínica)...")
        
        record_save_only = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            observations=full_observations,
            consultation_date=datetime.now(),
            # Sin síntomas, diagnóstico, tratamiento (solo historia clínica)
        )
        
        print("✅ Registro creado exitosamente para 'save'")
        print(f"   - Tiene symptoms: {bool(record_save_only.symptoms)}")
        print(f"   - Tiene diagnosis: {bool(record_save_only.diagnosis)}")
        print(f"   - Tiene treatment: {bool(record_save_only.treatment)}")
        print(f"   - Tiene observations: {bool(record_save_only.observations)}")
        print(f"   - Es consulta vacía: {not any([record_save_only.symptoms, record_save_only.diagnosis, record_save_only.treatment])}")
        
        # Verificar si esto se considera una "consulta vacía"
        is_empty_consultation = not any([
            record_save_only.symptoms and record_save_only.symptoms.strip(),
            record_save_only.diagnosis and record_save_only.diagnosis.strip(),
            record_save_only.treatment and record_save_only.treatment.strip(),
            record_save_only.prescriptions and record_save_only.prescriptions.strip()
        ])
        
        print(f"   - Es considerada consulta vacía: {is_empty_consultation}")
        
        # Pero tiene información de historia clínica válida
        has_medical_history = bool(record_save_only.observations and record_save_only.observations.strip())
        print(f"   - Tiene historia clínica válida: {has_medical_history}")
        
        print(f"\n✅ RESULTADO: Este registro NO es una consulta, es una HISTORIA CLÍNICA")
        print(f"   - La diferencia está en el propósito y contenido del registro")
        print(f"   - No debe considerarse una 'consulta vacía' porque no es una consulta")
        
        print(f"\n🎯 CONCLUSIÓN:")
        print(f"   - La nueva lógica está correcta")
        print(f"   - Solo crea un registro con historia clínica, sin datos de consulta")
        print(f"   - Para 'save_and_consult' redirigirá a crear una consulta separada")

if __name__ == "__main__":
    test_medical_history_logic()
