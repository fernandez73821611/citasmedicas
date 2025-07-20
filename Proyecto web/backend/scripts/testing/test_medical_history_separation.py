#!/usr/bin/env python3
"""
Script para probar la nueva lógica que separa historia clínica de consultas
"""

import sys
sys.path.append('.')

from app import create_app, db
from app.models.patient import Patient
from app.models.medical_record import MedicalRecord
from app.models.user import User
from datetime import datetime

def test_medical_history_separation():
    """Probar que la historia clínica no aparezca como consulta"""
    app = create_app()
    with app.app_context():
        
        print("🧪 Probando separación de historia clínica y consultas...")
        
        # Buscar el paciente que acabas de crear
        patient = Patient.query.filter_by(dni='56688999').first()
        if not patient:
            print("❌ No se encontró el paciente con DNI 56688999")
            return
        
        print(f"✅ Paciente encontrado: {patient.full_name}")
        
        # Obtener todos los registros médicos del paciente
        all_records = MedicalRecord.query.filter_by(
            patient_id=patient.id
        ).order_by(MedicalRecord.consultation_date.desc()).all()
        
        print(f"\n📊 Total de registros médicos: {len(all_records)}")
        
        for i, record in enumerate(all_records, 1):
            print(f"\n--- Registro {i} ---")
            print(f"ID: {record.id}")
            print(f"Fecha: {record.consultation_date}")
            print(f"Doctor: {record.doctor.full_name if record.doctor else 'N/A'}")
            print(f"Síntomas: {repr(record.symptoms)}")
            print(f"Diagnóstico: {repr(record.diagnosis)}")
            print(f"Tratamiento: {repr(record.treatment)}")
            print(f"Prescripciones: {repr(record.prescriptions)}")
            
            # Verificar si es una consulta real
            is_real_consultation = any([
                record.symptoms and record.symptoms.strip(),
                record.diagnosis and record.diagnosis.strip(),
                record.treatment and record.treatment.strip(),
                record.prescriptions and record.prescriptions.strip()
            ])
            
            if is_real_consultation:
                print("🩺 TIPO: Consulta real")
            else:
                print("📋 TIPO: Solo historia clínica")
            
            # Verificar si tiene información de historia clínica
            has_history_info = bool(record.observations and record.observations.strip())
            if has_history_info:
                print("📝 Contiene información de historia clínica")
                # Mostrar un fragmento de las observaciones
                obs_preview = record.observations[:100] + "..." if len(record.observations) > 100 else record.observations
                print(f"   Observaciones (preview): {obs_preview}")
        
        # Aplicar el filtro como lo haría la nueva lógica
        from app.routes.doctor import filter_real_consultations
        
        real_consultations = filter_real_consultations(all_records)
        
        print(f"\n🔍 RESULTADO DEL FILTRO:")
        print(f"   Total de registros: {len(all_records)}")
        print(f"   Consultas reales: {len(real_consultations)}")
        print(f"   Registros de solo historia clínica: {len(all_records) - len(real_consultations)}")
        
        if len(all_records) > len(real_consultations):
            print(f"\n✅ ÉXITO: El filtro está funcionando")
            print(f"   Los registros de solo historia clínica NO aparecerán en el historial de consultas")
        else:
            print(f"\n⚠️ ADVERTENCIA: Todos los registros se consideran consultas")
            print(f"   Verifica que el registro de historia clínica no tenga datos de consulta")

if __name__ == "__main__":
    test_medical_history_separation()
