#!/usr/bin/env python3
"""
Script para verificar las fechas de vigencia de los horarios de trabajo.
"""

import sys
import os
from datetime import datetime

# Agregar el directorio padre al path para importar la app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.work_schedule import WorkSchedule

def verify_schedule_dates():
    """Verificar las fechas de vigencia de los horarios"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 Verificando fechas de vigencia de horarios...")
            print("=" * 60)
            
            # Obtener todos los horarios
            schedules = WorkSchedule.query.order_by(
                WorkSchedule.doctor_id,
                WorkSchedule.day_of_week
            ).all()
            
            if not schedules:
                print("❌ No se encontraron horarios.")
                return
            
            print(f"📋 Total de horarios encontrados: {len(schedules)}")
            print("-" * 60)
            
            # Agrupar por doctor
            doctors_data = {}
            for schedule in schedules:
                doctor_name = schedule.doctor.full_name if schedule.doctor else "Doctor desconocido"
                if doctor_name not in doctors_data:
                    doctors_data[doctor_name] = []
                doctors_data[doctor_name].append(schedule)
            
            # Mostrar información por doctor
            for doctor_name, doctor_schedules in doctors_data.items():
                print(f"👨‍⚕️ Dr. {doctor_name}")
                print(f"   Horarios: {len(doctor_schedules)}")
                
                for schedule in doctor_schedules:
                    day_name = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][schedule.day_of_week]
                    
                    # Mostrar información del horario
                    print(f"   📅 {day_name}: {schedule.time_range}")
                    
                    # Verificar fechas de vigencia
                    if schedule.start_date and schedule.end_date:
                        print(f"      ✅ Vigencia: {schedule.start_date} hasta {schedule.end_date}")
                        
                        # Verificar si está activo para hoy
                        today = datetime.now().date()
                        if schedule.is_valid_for_date(today):
                            print(f"      🟢 ACTIVO para hoy ({today})")
                        else:
                            print(f"      🔴 INACTIVO para hoy ({today})")
                    else:
                        print(f"      ⚠️  Sin fechas de vigencia establecidas")
                    
                    # Mostrar rango de fechas usando la propiedad del modelo
                    if hasattr(schedule, 'date_range'):
                        print(f"      📊 Rango: {schedule.date_range}")
                
                print("-" * 40)
            
            # Resumen general
            with_dates = sum(1 for s in schedules if s.start_date and s.end_date)
            without_dates = len(schedules) - with_dates
            active_today = sum(1 for s in schedules if s.is_valid_for_date(datetime.now().date()))
            
            print("📊 RESUMEN GENERAL:")
            print(f"   Total de horarios: {len(schedules)}")
            print(f"   Con fechas de vigencia: {with_dates}")
            print(f"   Sin fechas de vigencia: {without_dates}")
            print(f"   Activos para hoy: {active_today}")
            print(f"   Inactivos para hoy: {len(schedules) - active_today}")
            
        except Exception as e:
            print(f"❌ Error durante la verificación: {str(e)}")
            return False
    
    return True

if __name__ == "__main__":
    print("🔍 Iniciando verificación de fechas de vigencia...")
    print("=" * 60)
    
    success = verify_schedule_dates()
    
    if success:
        print("\n✅ Verificación completada exitosamente!")
    else:
        print("\n❌ La verificación falló. Revise los errores anteriores.")
