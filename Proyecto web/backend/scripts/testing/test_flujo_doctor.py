#!/usr/bin/env python3
"""
Script para probar las Fases 1 y 2 del Flujo del Doctor
Ejecutar desde el directorio backend/
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.patient import Patient
from app.models.medical_record import MedicalRecord
from app.models.medical_history import MedicalHistory
from app.models.user import User
from app.models.appointment import Appointment
from datetime import datetime, date

def print_section(title):
    """Imprime una sección con formato"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_success(message):
    """Imprime mensaje de éxito"""
    print(f"✅ {message}")

def print_warning(message):
    """Imprime mensaje de advertencia"""
    print(f"⚠️  {message}")

def print_error(message):
    """Imprime mensaje de error"""
    print(f"❌ {message}")

def print_info(message):
    """Imprime mensaje informativo"""
    print(f"ℹ️  {message}")

def test_fase1_models():
    """Prueba los modelos de la Fase 1"""
    print_section("FASE 1: PRUEBAS DE MODELOS")
    
    try:
        # Prueba 1: Importar modelos
        print_info("Probando importación de modelos...")
        from app.models.medical_history import MedicalHistory
        from app.models.patient import Patient
        from app.models.medical_record import MedicalRecord
        print_success("Todos los modelos se importaron correctamente")
        
        # Prueba 2: Verificar que existen pacientes
        print_info("Verificando existencia de pacientes...")
        patients = Patient.query.all()
        if patients:
            print_success(f"Se encontraron {len(patients)} pacientes en la base de datos")
            
            # Prueba 3: Probar método has_medical_history
            print_info("Probando método has_medical_history...")
            patient = patients[0]
            has_history = patient.has_medical_history()
            print_success(f"Método has_medical_history funciona: {patient.full_name} - {has_history}")
            
            # Prueba 4: Probar método get_medical_history
            print_info("Probando método get_medical_history...")
            history = patient.get_medical_history()
            if history:
                print_success(f"Historia clínica encontrada: N° {history.medical_record_number}")
                print_info(f"  - Creada: {history.created_at}")
                print_info(f"  - Antecedentes personales: {history.personal_history[:50]}..." if history.personal_history else "  - Sin antecedentes personales")
            else:
                print_warning("No hay historia clínica para este paciente")
            
            # Prueba 5: Probar método get_consultation_count
            print_info("Probando método get_consultation_count...")
            count = patient.get_consultation_count()
            print_success(f"Número de consultas: {count}")
            
            # Prueba 6: Probar métodos de MedicalRecord
            print_info("Probando métodos de MedicalRecord...")
            medical_records = MedicalRecord.query.filter_by(patient_id=patient.id).all()
            if medical_records:
                record = medical_records[0]
                print_success(f"Registro médico encontrado: {record.id}")
                print_info(f"  - Anamnesis: {record.anamnesis[:50]}..." if record.anamnesis else "  - Sin anamnesis")
                print_info(f"  - Diagnóstico: {record.diagnosis_summary[:50]}..." if record.diagnosis_summary else "  - Sin diagnóstico")
                print_info(f"  - Recomendaciones: {record.recommendations[:50]}..." if record.recommendations else "  - Sin recomendaciones")
            else:
                print_warning("No hay registros médicos para este paciente")
                
        else:
            print_warning("No hay pacientes en la base de datos")
            
    except Exception as e:
        print_error(f"Error en pruebas de Fase 1: {str(e)}")
        import traceback
        traceback.print_exc()

def test_fase2_routes():
    """Prueba las rutas de la Fase 2"""
    print_section("FASE 2: PRUEBAS DE RUTAS Y FUNCIONALIDAD")
    
    try:
        # Prueba 1: Verificar que existen doctores
        print_info("Verificando existencia de doctores...")
        doctors = User.query.filter_by(role='doctor').all()
        if doctors:
            print_success(f"Se encontraron {len(doctors)} doctores en la base de datos")
            doctor = doctors[0]
            print_info(f"  - Doctor de prueba: {doctor.full_name}")
            
            # Prueba 2: Verificar citas del doctor
            print_info("Verificando citas del doctor...")
            appointments = Appointment.query.filter_by(doctor_id=doctor.id).all()
            if appointments:
                print_success(f"Se encontraron {len(appointments)} citas para el doctor")
                appointment = appointments[0]
                print_info(f"  - Cita de prueba: {appointment.patient.full_name} - {appointment.date_time}")
                
                # Prueba 3: Verificar estado de historia clínica del paciente
                print_info("Verificando estado de historia clínica...")
                patient = appointment.patient
                has_history = patient.has_medical_history()
                if has_history:
                    print_success(f"El paciente {patient.full_name} TIENE historia clínica")
                    print_info("  - Flujo esperado: Ver Historia + Consulta")
                else:
                    print_warning(f"El paciente {patient.full_name} NO TIENE historia clínica")
                    print_info("  - Flujo esperado: Crear Historia + Consulta")
                
            else:
                print_warning("No hay citas para este doctor")
                
        else:
            print_warning("No hay doctores en la base de datos")
            
        # Prueba 4: Verificar historias clínicas existentes
        print_info("Verificando historias clínicas existentes...")
        patients_with_history = []
        all_patients = Patient.query.all()
        
        for patient in all_patients:
            if patient.has_medical_history():
                patients_with_history.append(patient)
                
        if patients_with_history:
            print_success(f"Se encontraron {len(patients_with_history)} pacientes con historia clínica")
            for patient in patients_with_history[:3]:  # Mostrar solo los primeros 3
                history = patient.get_medical_history()
                print_info(f"  - {patient.full_name}: N° {history.medical_record_number}")
        else:
            print_warning("No hay pacientes con historia clínica")
            
    except Exception as e:
        print_error(f"Error en pruebas de Fase 2: {str(e)}")
        import traceback
        traceback.print_exc()

def test_templates_and_forms():
    """Prueba la existencia de templates y formularios"""
    print_section("FASE 2: PRUEBAS DE TEMPLATES Y FORMULARIOS")
    
    try:
        import os
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'templates', 'doctor')
        
        # Lista de templates que deberían existir
        required_templates = [
            'medical_history_form.html',
            'consultation_form.html',
            'medical_history_view.html',
            'consultation_view.html',
            'clinical_histories.html'
        ]
        
        print_info("Verificando existencia de templates...")
        for template in required_templates:
            template_path = os.path.join(template_dir, template)
            if os.path.exists(template_path):
                print_success(f"Template encontrado: {template}")
            else:
                print_error(f"Template NO encontrado: {template}")
                
        # Verificar rutas en doctor.py
        print_info("Verificando rutas en doctor.py...")
        routes_file = os.path.join(os.path.dirname(__file__), 'app', 'routes', 'doctor.py')
        if os.path.exists(routes_file):
            with open(routes_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Verificar rutas específicas
            required_routes = [
                'def view_medical_history',
                'def new_medical_history',
                'def new_consultation',
                'def view_consultation',
                'def check_patient_history',
                'def clinical_histories'
            ]
            
            for route in required_routes:
                if route in content:
                    print_success(f"Ruta encontrada: {route}")
                else:
                    print_error(f"Ruta NO encontrada: {route}")
        else:
            print_error("Archivo doctor.py no encontrado")
            
    except Exception as e:
        print_error(f"Error en pruebas de templates: {str(e)}")
        import traceback
        traceback.print_exc()

def create_test_scenario():
    """Crea un escenario de prueba si es necesario"""
    print_section("CREACIÓN DE DATOS DE PRUEBA")
    
    try:
        # Verificar si necesitamos crear datos de prueba
        doctors = User.query.filter_by(role='doctor').all()
        patients = Patient.query.all()
        
        if not doctors or not patients:
            print_warning("Se necesitan datos de prueba para realizar las pruebas completas")
            print_info("Datos disponibles:")
            print_info(f"  - Doctores: {len(doctors)}")
            print_info(f"  - Pacientes: {len(patients)}")
            print_info("\nPara crear datos de prueba, ejecute:")
            print_info("  python scripts/setup/create_test_data.py")
        else:
            print_success("Datos suficientes para realizar pruebas")
            
    except Exception as e:
        print_error(f"Error verificando datos de prueba: {str(e)}")

def main():
    """Función principal"""
    print(f"""
{'='*60}
   PRUEBAS DEL FLUJO DEL DOCTOR - FASES 1 y 2
{'='*60}
   Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
{'='*60}
""")
    
    # Crear aplicación Flask
    app = create_app()
    
    with app.app_context():
        # Ejecutar pruebas
        test_fase1_models()
        test_fase2_routes()
        test_templates_and_forms()
        create_test_scenario()
        
        print_section("RESUMEN DE PRUEBAS")
        print_success("Pruebas de Fase 1 completadas")
        print_success("Pruebas de Fase 2 completadas")
        print_info("Revise los mensajes arriba para ver detalles específicos")
        
        print(f"\n{'='*60}")
        print("  INSTRUCCIONES PARA PROBAR EN EL NAVEGADOR")
        print(f"{'='*60}")
        print("1. Inicie la aplicación: python run.py")
        print("2. Acceda como doctor al sistema")
        print("3. Verifique el dashboard - debe mostrar:")
        print("   - Indicadores 'Tiene Historia' / 'Paciente Nuevo'")
        print("   - Botones 'Ver Historia + Consulta' / 'Crear Historia + Consulta'")
        print("4. Navegue a 'Historias Clínicas' en el menú lateral")
        print("5. Pruebe crear una nueva historia clínica")
        print("6. Pruebe crear una nueva consulta")
        print(f"{'='*60}")

if __name__ == "__main__":
    main()
