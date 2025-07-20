#!/usr/bin/env python3
"""
Script para establecer fechas de vigencia por defecto a todos los horarios existentes
Establece un rango de fechas de 15 días a partir de hoy
"""

import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.work_schedule import WorkSchedule

def main():
    """Función principal"""
    app = create_app()
    
    with app.app_context():
        # Calcular fechas de vigencia (15 días desde hoy)
        today = datetime.now().date()
        start_date = today
        end_date = today + timedelta(days=15)
        
        print(f"🗓️  Estableciendo fechas de vigencia para todos los horarios:")
        print(f"   Fecha de inicio: {start_date.strftime('%d/%m/%Y')}")
        print(f"   Fecha de fin: {end_date.strftime('%d/%m/%Y')}")
        print("-" * 50)
        
        # Obtener todos los horarios que no tienen fechas de vigencia
        schedules = WorkSchedule.query.filter(
            (WorkSchedule.start_date == None) | (WorkSchedule.end_date == None)
        ).all()
        
        if not schedules:
            print("❌ No se encontraron horarios sin fechas de vigencia")
            return
        
        # Actualizar fechas de vigencia para cada horario
        updated_count = 0
        for schedule in schedules:
            try:
                doctor_name = schedule.doctor.full_name if schedule.doctor else "Doctor desconocido"
                day_name = schedule.day_name
                
                schedule.start_date = start_date
                schedule.end_date = end_date
                db.session.add(schedule)
                updated_count += 1
                
                print(f"✅ Dr. {doctor_name} - {day_name} - Fechas de vigencia actualizadas")
                
            except Exception as e:
                print(f"❌ Error actualizando horario ID {schedule.id}: {str(e)}")
        
        # Guardar cambios
        try:
            db.session.commit()
            print("-" * 50)
            print(f"🎉 ¡Proceso completado exitosamente!")
            print(f"   Horarios actualizados: {updated_count}")
            print(f"   Periodo de vigencia: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al guardar cambios: {str(e)}")

if __name__ == '__main__':
    main()
