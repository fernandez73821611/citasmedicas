#!/usr/bin/env python3
"""
Script para probar que el nuevo sistema de historia clínica incluye todas las secciones
"""

from app import create_app, db
from app.models.patient import Patient
from app.models.medical_record import MedicalRecord
from app.models.medical_history import MedicalHistory
from app.models.user import User
from datetime import datetime

def test_complete_medical_history():
    """Probar la creación de una historia clínica completa con el nuevo sistema"""
    app = create_app()
    with app.app_context():
        
        # Buscar un doctor para la prueba
        doctor = User.query.filter_by(role='doctor').first()
        if not doctor:
            print("No se encontró ningún doctor en el sistema")
            return
        
        # Buscar un paciente sin historia clínica o crear uno de prueba
        patient = Patient.query.filter(~Patient.medical_records.any()).first()
        if not patient:
            print("No se encontró un paciente sin historia clínica")
            # En producción, aquí podrías crear un paciente de prueba
            return
        
        print(f"Paciente de prueba: {patient.full_name}")
        print(f"Doctor de prueba: {doctor.full_name}")
        
        # Simular la creación de una historia clínica usando la nueva lógica
        # (simulando lo que hace la ruta new_medical_history)
        
        # Datos de ejemplo - algunos campos vacíos para probar el comportamiento
        form_data = {
            'personal_history': 'Hipertensión hace 5 años',  # Con datos
            'family_history': '',  # Vacío
            'allergies': 'Penicilina',  # Con datos
            'current_medications': '',  # Vacío
            'surgical_history': 'Apendicectomía 2020',  # Con datos
            'smoking_habits': '',  # Vacío
            'alcohol_habits': 'Ocasional',  # Con datos
            'drug_habits': '',  # Vacío
            'physical_activity': 'Camina 30 min diarios',  # Con datos
            'symptoms': 'Dolor de cabeza',
            'diagnosis': 'Cefalea tensional',
            'treatment': 'Ibuprofeno 400mg c/8h',
            'observations': 'Paciente refiere estrés laboral'
        }
        
        # Aplicar la nueva lógica mejorada
        history_info = []
        
        # SIEMPRE incluir todas las secciones (nueva lógica)
        history_info.append(f"ANTECEDENTES PERSONALES:\n{form_data['personal_history'] or 'Sin antecedentes registrados'}")
        history_info.append(f"ANTECEDENTES FAMILIARES:\n{form_data['family_history'] or 'Sin antecedentes registrados'}")
        history_info.append(f"ALERGIAS:\n{form_data['allergies'] or 'Sin alergias registradas'}")
        history_info.append(f"MEDICAMENTOS CRÓNICOS:\n{form_data['current_medications'] or 'Sin medicamentos registrados'}")
        history_info.append(f"HISTORIA QUIRÚRGICA:\n{form_data['surgical_history'] or 'Sin cirugías registradas'}")
        history_info.append(f"HÁBITOS DE TABACO:\n{form_data['smoking_habits'] or 'No fuma'}")
        history_info.append(f"HÁBITOS DE ALCOHOL:\n{form_data['alcohol_habits'] or 'No consume alcohol'}")
        history_info.append(f"USO DE DROGAS:\n{form_data['drug_habits'] or 'No consume drogas'}")
        history_info.append(f"ACTIVIDAD FÍSICA:\n{form_data['physical_activity'] or 'Sin información de actividad física'}")
        
        # Combinar con observaciones de consulta
        full_observations = "\n\n".join(history_info)
        if form_data['observations']:
            full_observations += f"\n\nOBSERVACIONES DE CONSULTA:\n{form_data['observations']}"
        
        print("\nObservaciones generadas:")
        print("=" * 60)
        print(full_observations)
        print("=" * 60)
        
        # Crear el registro médico
        medical_record = MedicalRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            symptoms=form_data['symptoms'],
            diagnosis=form_data['diagnosis'],
            treatment=form_data['treatment'],
            observations=full_observations,
            consultation_date=datetime.now()
        )
        
        # Guardar en base de datos
        db.session.add(medical_record)
        db.session.commit()
        
        print(f"\n✅ Registro médico creado con ID: {medical_record.id}")
        
        # Verificar la historia clínica generada
        history = MedicalHistory(patient)
        print(f"\n🔍 Verificación de la historia clínica:")
        print(f"- Antecedentes personales: {repr(history.personal_history)}")
        print(f"- Antecedentes familiares: {repr(history.family_history)}")
        print(f"- Alergias: {repr(history.allergies)}")
        print(f"- Medicamentos crónicos: {repr(history.chronic_medications)}")
        print(f"- Historia quirúrgica: {repr(history.surgical_history)}")
        print(f"- Hábitos de tabaco: {repr(history.smoking_habits)}")
        print(f"- Hábitos de alcohol: {repr(history.alcohol_habits)}")
        print(f"- Uso de drogas: {repr(history.drug_habits)}")
        print(f"- Actividad física: {repr(history.physical_activity)}")
        
        # Verificar que ningún campo esté vacío
        fields = [
            ('personal_history', history.personal_history),
            ('family_history', history.family_history),
            ('allergies', history.allergies),
            ('chronic_medications', history.chronic_medications),
            ('surgical_history', history.surgical_history),
            ('smoking_habits', history.smoking_habits),
            ('alcohol_habits', history.alcohol_habits),
            ('drug_habits', history.drug_habits),
            ('physical_activity', history.physical_activity),
        ]
        
        empty_fields = [name for name, value in fields if not value.strip()]
        if empty_fields:
            print(f"\n❌ CAMPOS VACÍOS DETECTADOS: {empty_fields}")
            print("Esto significa que aparecerán como 'No registrado' en el template")
        else:
            print(f"\n✅ TODOS LOS CAMPOS TIENEN CONTENIDO")
            print("No aparecerá 'No registrado' en ningún campo")
        
        # Limpiar: eliminar el registro de prueba
        db.session.delete(medical_record)
        db.session.commit()
        print(f"\n🧹 Registro de prueba eliminado")

if __name__ == "__main__":
    test_complete_medical_history()
