#!/usr/bin/env python3
"""
Script para actualizar todos los horarios de trabajo con fechas de vigencia.
Establece fecha de inicio como hoy y fecha de fin dentro de 15 días.
"""

import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio padre al path para importar la app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.work_schedule import WorkSchedule

def update_all_schedule_dates():
    """Actualizar todos los horarios con fechas de vigencia"""
    app = create_app()
    
    with app.app_context():
        try:
            # Obtener fecha actual y fecha de fin (15 días después)
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=15)
            
            print(f"Actualizando horarios de trabajo...")
            print(f"Fecha de inicio: {start_date}")
            print(f"Fecha de fin: {end_date}")
            print("-" * 50)
            
            # Obtener todos los horarios que no tienen fechas establecidas
            schedules = WorkSchedule.query.filter(
                WorkSchedule.start_date.is_(None)
            ).all()
            
            if not schedules:
                print("No se encontraron horarios sin fechas de vigencia.")
                return
            
            print(f"Se encontraron {len(schedules)} horarios para actualizar:")
            
            updated_count = 0
            
            for schedule in schedules:
                try:
                    # Obtener información del doctor
                    doctor_name = schedule.doctor.full_name if schedule.doctor else "Doctor desconocido"
                    day_name = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][schedule.day_of_week]
                    
                    print(f"  - Dr. {doctor_name} - {day_name} ({schedule.time_range})")
                    
                    # Actualizar las fechas
                    schedule.start_date = start_date
                    schedule.end_date = end_date
                    schedule.updated_at = datetime.utcnow()
                    
                    updated_count += 1
                    
                except Exception as e:
                    print(f"    ERROR al actualizar horario ID {schedule.id}: {str(e)}")
                    continue
            
            # Confirmar cambios
            db.session.commit()
            
            print("-" * 50)
            print(f"✅ Actualización completada exitosamente!")
            print(f"📅 {updated_count} horarios actualizados")
            print(f"🗓️  Vigencia: {start_date} hasta {end_date}")
            
            # Mostrar resumen por doctor
            print("\n📊 Resumen por doctor:")
            doctors_summary = {}
            for schedule in schedules:
                doctor_name = schedule.doctor.full_name if schedule.doctor else "Doctor desconocido"
                if doctor_name not in doctors_summary:
                    doctors_summary[doctor_name] = 0
                doctors_summary[doctor_name] += 1
            
            for doctor_name, count in doctors_summary.items():
                print(f"  - Dr. {doctor_name}: {count} horarios")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error durante la actualización: {str(e)}")
            return False
    
    return True

if __name__ == "__main__":
    print("🔄 Iniciando actualización de fechas de vigencia...")
    print("=" * 60)
    
    success = update_all_schedule_dates()
    
    if success:
        print("\n✅ Proceso completado exitosamente!")
    else:
        print("\n❌ El proceso falló. Revise los errores anteriores.")
