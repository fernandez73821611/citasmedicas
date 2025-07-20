#!/usr/bin/env python3
"""
Script para probar la interfaz web del Flujo del Doctor
Genera URLs específicas para probar en el navegador
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.patient import Patient
from app.models.user import User
from app.models.appointment import Appointment
from datetime import datetime

def print_section(title):
    """Imprime una sección con formato"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def generate_test_urls():
    """Genera URLs para probar en el navegador"""
    print_section("URLS PARA PROBAR EN EL NAVEGADOR")
    
    app = create_app()
    with app.app_context():
        # Obtener datos de prueba
        doctors = User.query.filter_by(role='doctor').all()
        patients = Patient.query.all()
        appointments = Appointment.query.all()
        
        if not doctors:
            print("❌ No hay doctores en la base de datos")
            return
            
        if not patients:
            print("❌ No hay pacientes en la base de datos")
            return
            
        doctor = doctors[0]
        patient = patients[0]
        
        print(f"🔍 Datos de prueba:")
        print(f"   Doctor: {doctor.full_name} (ID: {doctor.id})")
        print(f"   Paciente: {patient.full_name} (ID: {patient.id})")
        print(f"   Tiene historia: {'SÍ' if patient.has_medical_history() else 'NO'}")
        
        base_url = "http://localhost:5000"
        
        print(f"\n📋 URLs PRINCIPALES:")
        print(f"1. Dashboard del Doctor:")
        print(f"   {base_url}/doctor/dashboard")
        
        print(f"\n2. Lista de Pacientes:")
        print(f"   {base_url}/doctor/patients")
        
        print(f"\n3. Historias Clínicas:")
        print(f"   {base_url}/doctor/clinical-histories")
        
        print(f"\n4. Citas del Doctor:")
        print(f"   {base_url}/doctor/appointments")
        
        print(f"\n📋 URLs ESPECÍFICAS PARA PACIENTE DE PRUEBA:")
        print(f"5. Ver Historia Clínica (si existe):")
        print(f"   {base_url}/doctor/medical-history/{patient.id}")
        
        print(f"\n6. Crear Historia Clínica (si no existe):")
        print(f"   {base_url}/doctor/medical-history/{patient.id}/new")
        
        print(f"\n7. Nueva Consulta (si ya tiene historia):")
        print(f"   {base_url}/doctor/consultation/{patient.id}/new")
        
        print(f"\n8. Verificar Estado del Paciente:")
        print(f"   {base_url}/doctor/patient/{patient.id}/check-history")
        
        print(f"\n9. Historial Completo del Paciente:")
        print(f"   {base_url}/doctor/patient/{patient.id}/history")
        
        # URLs con citas si existen
        doctor_appointments = Appointment.query.filter_by(doctor_id=doctor.id).all()
        if doctor_appointments:
            appointment = doctor_appointments[0]
            print(f"\n📋 URLs CON CITA DE PRUEBA:")
            print(f"10. Consultar desde Cita:")
            print(f"    {base_url}/doctor/appointment/{appointment.id}/consult")
            
            print(f"\n11. Verificar Historia desde Cita:")
            print(f"    {base_url}/doctor/patient/{appointment.patient_id}/check-history?appointment_id={appointment.id}")

def print_test_checklist():
    """Imprime lista de verificación para pruebas"""
    print_section("LISTA DE VERIFICACIÓN - FASE 1 y 2")
    
    print("✅ FASE 1 - MODELOS:")
    print("   □ Los pacientes pueden tener historias clínicas")
    print("   □ Método has_medical_history() funciona")
    print("   □ Método get_medical_history() funciona")
    print("   □ Método get_consultation_count() funciona")
    print("   □ MedicalRecord tiene propiedades lógicas")
    print("   □ No hay errores en la base de datos")
    
    print("\n✅ FASE 2 - FORMULARIOS Y TEMPLATES:")
    print("   □ Dashboard muestra estado de historia clínica")
    print("   □ Botones diferenciados en dashboard")
    print("   □ Lista de pacientes muestra estado")
    print("   □ Formulario de historia clínica funciona")
    print("   □ Formulario de consulta funciona")
    print("   □ Visualización de historia clínica funciona")
    print("   □ Visualización de consulta funciona")
    print("   □ Menú 'Historias Clínicas' aparece")
    print("   □ Navegación entre formularios funciona")
    
    print("\n✅ FLUJO COMPLETO:")
    print("   □ Paciente nuevo → Crear Historia + Consulta")
    print("   □ Paciente con historia → Ver Historia + Consulta")
    print("   □ Redirección automática según estado")
    print("   □ Formularios guardan datos correctamente")
    print("   □ Visualización muestra datos correctos")

def print_startup_instructions():
    """Imprime instrucciones para iniciar la aplicación"""
    print_section("INSTRUCCIONES PARA INICIAR LA APLICACIÓN")
    
    print("1. 🚀 INICIAR LA APLICACIÓN:")
    print("   cd backend")
    print("   python run.py")
    print("   (La aplicación debería iniciarse en http://localhost:5000)")
    
    print("\n2. 🔐 ACCEDER AL SISTEMA:")
    print("   - Navegar a http://localhost:5000")
    print("   - Iniciar sesión como doctor")
    print("   - Si no hay usuario doctor, crear uno desde admin")
    
    print("\n3. 🧪 PROBAR FUNCIONALIDADES:")
    print("   - Verificar dashboard con indicadores")
    print("   - Probar crear historia clínica")
    print("   - Probar crear consulta")
    print("   - Verificar navegación entre páginas")
    
    print("\n4. 🐛 SI HAY ERRORES:")
    print("   - Verificar la consola del navegador (F12)")
    print("   - Verificar logs de Flask en la terminal")
    print("   - Verificar que la base de datos esté actualizada")

def main():
    """Función principal"""
    print(f"""
{'='*60}
   GUÍA DE PRUEBAS WEB - FLUJO DEL DOCTOR
{'='*60}
   Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
{'='*60}
""")
    
    print_startup_instructions()
    generate_test_urls()
    print_test_checklist()
    
    print_section("PRÓXIMOS PASOS")
    print("1. Ejecutar: python test_flujo_doctor.py")
    print("2. Iniciar aplicación: python run.py")
    print("3. Probar URLs generadas arriba")
    print("4. Verificar lista de verificación")
    print("5. Reportar cualquier problema encontrado")

if __name__ == "__main__":
    main()
