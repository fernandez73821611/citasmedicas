#!/usr/bin/env python3
"""
Script de prueba para verificar la sincronización de fechas de vigencia
en los horarios de trabajo de los doctores
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db
from app.models.user import User
from app.models.work_schedule import WorkSchedule
from datetime import datetime, date, time

def test_date_synchronization():
    """Prueba la sincronización de fechas de vigencia"""
    
    print("🧪 Iniciando prueba de sincronización de fechas de vigencia...")
    print("=" * 70)
    
    # Buscar un doctor con múltiples horarios
    doctor = User.query.filter_by(role='doctor').first()
    
    if not doctor:
        print("❌ No se encontró ningún doctor en el sistema")
        return
    
    print(f"📋 Doctor seleccionado: {doctor.full_name}")
    
    # Obtener horarios del doctor
    schedules = WorkSchedule.query.filter_by(doctor_id=doctor.id, is_active=True).all()
    
    if len(schedules) < 2:
        print("⚠️  El doctor debe tener al menos 2 horarios para probar la sincronización")
        return
    
    print(f"📅 Horarios encontrados: {len(schedules)}")
    
    # Mostrar estado inicial
    print("\n📊 ESTADO INICIAL:")
    for i, schedule in enumerate(schedules, 1):
        print(f"   {i}. {schedule.day_name} - Vigencia: {schedule.start_date} a {schedule.end_date}")
    
    # Simular actualización de fechas en el primer horario
    first_schedule = schedules[0]
    original_start = first_schedule.start_date
    original_end = first_schedule.end_date
    
    # Nuevas fechas de prueba
    new_start_date = date(2025, 8, 1)
    new_end_date = date(2025, 12, 31)
    
    print(f"\n🔄 SIMULANDO ACTUALIZACIÓN...")
    print(f"   Horario: {first_schedule.day_name}")
    print(f"   Nueva fecha inicio: {new_start_date}")
    print(f"   Nueva fecha fin: {new_end_date}")
    
    # Aplicar lógica de sincronización (simulando la ruta edit_work_schedule)
    if (first_schedule.start_date != new_start_date or 
        first_schedule.end_date != new_end_date):
        
        # Actualizar el horario principal
        first_schedule.start_date = new_start_date
        first_schedule.end_date = new_end_date
        first_schedule.updated_at = datetime.utcnow()
        
        # Actualizar todos los otros horarios del doctor
        updated_count = 0
        for other_schedule in schedules:
            if other_schedule.id != first_schedule.id:
                other_schedule.start_date = new_start_date
                other_schedule.end_date = new_end_date
                other_schedule.updated_at = datetime.utcnow()
                updated_count += 1
        
        try:
            db.session.commit()
            print(f"✅ Se actualizaron {updated_count + 1} horarios exitosamente")
            
            # Mostrar estado final
            print("\n📊 ESTADO FINAL:")
            updated_schedules = WorkSchedule.query.filter_by(doctor_id=doctor.id, is_active=True).all()
            for i, schedule in enumerate(updated_schedules, 1):
                print(f"   {i}. {schedule.day_name} - Vigencia: {schedule.start_date} a {schedule.end_date}")
            
            # Verificar que todas las fechas son iguales
            all_same = all(s.start_date == new_start_date and s.end_date == new_end_date 
                          for s in updated_schedules)
            
            if all_same:
                print("\n✅ PRUEBA EXITOSA: Todas las fechas de vigencia están sincronizadas")
            else:
                print("\n❌ PRUEBA FALLIDA: Las fechas no están sincronizadas")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error durante la sincronización: {str(e)}")
    
    else:
        print("ℹ️  No hay cambios en las fechas de vigencia")

if __name__ == "__main__":
    # Crear aplicación Flask
    app = create_app()
    
    with app.app_context():
        test_date_synchronization()
