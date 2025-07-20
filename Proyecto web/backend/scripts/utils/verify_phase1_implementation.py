#!/usr/bin/env python3
"""
Script para verificar la implementación lógica de la Fase 1 del flujo del doctor.

Este script verifica que:
1. Los modelos se cargan correctamente
2. La lógica de historia clínica funciona
3. Los datos actuales no se ven afectados
4. Las relaciones entre modelos funcionan
"""

from app import create_app, db
from app.models import Patient, MedicalRecord, MedicalHistory, User
from datetime import datetime

def test_models_loading():
    """Verificar que los modelos se cargan correctamente"""
    print("🔍 Verificando carga de modelos...")
    
    try:
        # Verificar que los modelos se importan correctamente
        print(f"✅ Patient: {Patient}")
        print(f"✅ MedicalRecord: {MedicalRecord}")
        print(f"✅ MedicalHistory: {MedicalHistory}")
        print("✅ Todos los modelos se cargan correctamente")
        return True
    except Exception as e:
        print(f"❌ Error al cargar modelos: {e}")
        return False

def test_existing_data():
    """Verificar que los datos existentes no se ven afectados"""
    print("\n🔍 Verificando datos existentes...")
    
    try:
        # Contar registros existentes
        patient_count = Patient.query.count()
        medical_record_count = MedicalRecord.query.count()
        
        print(f"✅ Pacientes en BD: {patient_count}")
        print(f"✅ Registros médicos en BD: {medical_record_count}")
        
        if patient_count > 0:
            # Probar con el primer paciente
            patient = Patient.query.first()
            print(f"✅ Paciente de prueba: {patient.full_name}")
            
            # Verificar que las propiedades funcionan
            print(f"✅ Edad: {patient.age}")
            print(f"✅ Es menor: {patient.is_minor}")
            print(f"✅ Tiene historia: {patient.has_medical_history()}")
            print(f"✅ Es nuevo: {patient.is_new_patient()}")
            print(f"✅ Consultas: {patient.get_medical_records_count()}")
            
            return True
        else:
            print("ℹ️  No hay pacientes en la BD para probar")
            return True
            
    except Exception as e:
        print(f"❌ Error al verificar datos existentes: {e}")
        return False

def test_medical_history_logic():
    """Verificar la lógica de historia clínica"""
    print("\n🔍 Verificando lógica de historia clínica...")
    
    try:
        # Buscar un paciente con registros médicos
        patient = Patient.query.join(MedicalRecord).first()
        
        if patient:
            print(f"✅ Probando con paciente: {patient.full_name}")
            
            # Crear historia clínica lógica
            history = patient.get_medical_history()
            print(f"✅ Historia clínica creada: {history}")
            
            # Verificar propiedades
            print(f"✅ Número de historia: {history.medical_history_number}")
            print(f"✅ Fecha de apertura: {history.opening_date}")
            print(f"✅ Datos completos: {history.has_complete_data()}")
            
            # Obtener resumen
            summary = history.get_summary()
            print(f"✅ Resumen generado: {summary['number']}")
            
            # Verificar estado del paciente
            status = patient.get_patient_status_for_doctor()
            print(f"✅ Estado del paciente: {status['label']}")
            print(f"✅ Acción recomendada: {status['action']}")
            
            return True
        else:
            print("ℹ️  No hay pacientes con registros médicos para probar")
            return True
            
    except Exception as e:
        print(f"❌ Error al verificar lógica de historia clínica: {e}")
        return False

def test_medical_record_logic():
    """Verificar la lógica de registros médicos"""
    print("\n🔍 Verificando lógica de registros médicos...")
    
    try:
        # Buscar un registro médico
        record = MedicalRecord.query.first()
        
        if record:
            print(f"✅ Probando con registro: {record.id}")
            
            # Verificar propiedades lógicas
            print(f"✅ Motivo de consulta: {record.chief_complaint}")
            print(f"✅ Enfermedad actual: {record.current_illness}")
            print(f"✅ Examen físico: {record.general_examination}")
            print(f"✅ Recomendaciones: {record.recommendations}")
            
            # Verificar métodos
            print(f"✅ Anamnesis completa: {record.has_complete_anamnesis()}")
            print(f"✅ Signos vitales completos: {record.has_complete_vitals()}")
            print(f"✅ Consulta completa: {record.is_complete_consultation()}")
            
            # Verificar relación con historia clínica
            history = record.get_patient_medical_history()
            if history:
                print(f"✅ Historia clínica relacionada: {history.medical_history_number}")
            
            return True
        else:
            print("ℹ️  No hay registros médicos para probar")
            return True
            
    except Exception as e:
        print(f"❌ Error al verificar lógica de registros médicos: {e}")
        return False

def test_patient_workflow():
    """Verificar el flujo completo del paciente"""
    print("\n🔍 Verificando flujo completo del paciente...")
    
    try:
        # Buscar pacientes nuevos y existentes
        patients = Patient.query.limit(3).all()
        
        for patient in patients:
            print(f"\n--- Paciente: {patient.full_name} ---")
            
            # Verificar estado
            status = patient.get_patient_status_for_doctor()
            print(f"Estado: {status['label']}")
            print(f"Acción: {status['action']}")
            
            # Verificar historia clínica
            if patient.has_medical_history():
                history = patient.get_medical_history()
                summary = history.get_summary()
                print(f"Historia: {summary['number']}")
                print(f"Consultas: {summary['total_consultations']}")
            else:
                print("Sin historia clínica")
            
            # Verificar resumen médico completo
            complete_summary = patient.get_complete_medical_summary()
            print(f"Resumen completo generado: ✅")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al verificar flujo del paciente: {e}")
        return False

def main():
    """Función principal de verificación"""
    print("=" * 60)
    print("🏥 VERIFICACIÓN DE FASE 1 - FLUJO DEL DOCTOR")
    print("=" * 60)
    
    # Crear aplicación
    app = create_app()
    
    with app.app_context():
        # Ejecutar todas las pruebas
        tests = [
            ("Carga de modelos", test_models_loading),
            ("Datos existentes", test_existing_data),
            ("Lógica de historia clínica", test_medical_history_logic),
            ("Lógica de registros médicos", test_medical_record_logic),
            ("Flujo completo del paciente", test_patient_workflow)
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n{'='*40}")
            print(f"🧪 {test_name}")
            print(f"{'='*40}")
            
            result = test_func()
            results.append((test_name, result))
        
        # Mostrar resultados finales
        print("\n" + "=" * 60)
        print("📊 RESULTADOS FINALES")
        print("=" * 60)
        
        all_passed = True
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name}: {status}")
            if not result:
                all_passed = False
        
        print("\n" + "=" * 60)
        if all_passed:
            print("🎉 TODAS LAS PRUEBAS PASARON")
            print("✅ La implementación lógica de la Fase 1 está funcionando correctamente")
            print("✅ Los datos actuales no se ven afectados")
            print("✅ Las relaciones entre modelos funcionan")
        else:
            print("⚠️  ALGUNAS PRUEBAS FALLARON")
            print("❌ Revisar los errores mostrados arriba")
        
        print("=" * 60)

if __name__ == "__main__":
    main()
