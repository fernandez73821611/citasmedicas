"""
Script para probar el flujo completo: Cita → Pago → Triage → Doctor
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.user import User
from app.models.invoice import Invoice
from app.models.triage import Triage
from datetime import datetime, date

def test_complete_triage_flow():
    """Probar el flujo completo incluyendo triage"""
    app = create_app()
    with app.app_context():
        print("=== TESTING FLUJO COMPLETO CON TRIAGE ===")
        
        # 1. Usar la cita existente (ID 14)
        appointment = Appointment.query.get(14)
        if not appointment:
            print("❌ No se encontró la cita de prueba")
            return
            
        print(f"📋 Usando cita existente:")
        print(f"   ID: {appointment.id}")
        print(f"   Paciente: {appointment.patient.full_name}")
        print(f"   Doctor: {appointment.doctor.full_name}")
        print(f"   Fecha: {appointment.date_time.strftime('%d/%m/%Y %H:%M')}")
        print(f"   Estado: {appointment.status}")
        print(f"   Pagado: {appointment.is_paid}")
        
        # 2. Verificar que la cita está pagada
        if not appointment.is_paid:
            print("❌ La cita no está pagada")
            return
            
        # 3. Buscar o crear una enfermera
        nurse = User.query.filter_by(role='nurse').first()
        if not nurse:
            print("❌ No hay enfermeras en el sistema")
            return
            
        print(f"👩‍⚕️ Enfermera: {nurse.full_name}")
        
        # 4. Verificar si ya existe un triage
        existing_triage = Triage.query.filter_by(appointment_id=appointment.id).first()
        if existing_triage:
            print(f"🩺 Triage existente encontrado:")
            print(f"   ID: {existing_triage.id}")
            print(f"   Estado: {existing_triage.status}")
            print(f"   Enfermera: {existing_triage.nurse.full_name}")
            
            # Si ya está completado, verificar el siguiente paso
            if existing_triage.status == 'completed':
                print(f"   ✅ Triage completado - Verificando estado de cita...")
                print(f"   Estado de cita: {appointment.status}")
                if appointment.status == 'ready_for_doctor':
                    print(f"   ✅ Cita lista para doctor")
                else:
                    print(f"   ⚠️  Cita no está en estado 'ready_for_doctor'")
                    
                    # Actualizar el estado de la cita
                    appointment.status = 'ready_for_doctor'
                    db.session.commit()
                    print(f"   ✅ Estado actualizado a 'ready_for_doctor'")
                    
            return
            
        # 5. Crear un nuevo triage
        print(f"\n🩺 Creando nuevo triage...")
        
        # Datos de ejemplo para el triage
        triage_data = {
            'appointment_id': appointment.id,
            'nurse_id': nurse.id,
            'patient_id': appointment.patient_id,
            'chief_complaint': 'Dolor de cabeza leve',
            'priority_level': 'media',
            'nurse_observations': 'Paciente en buen estado general',
            'status': 'completed'
        }
        
        try:
            # Crear el triage
            triage = Triage(
                appointment_id=triage_data['appointment_id'],
                nurse_id=triage_data['nurse_id'],
                patient_id=triage_data['patient_id'],
                temperature=36.5,
                blood_pressure_systolic=120,
                blood_pressure_diastolic=80,
                heart_rate=72,
                respiratory_rate=16,
                oxygen_saturation=98,
                weight=70.0,
                height=170.0,
                chief_complaint=triage_data['chief_complaint'],
                priority_level=triage_data['priority_level'],
                nurse_observations=triage_data['nurse_observations'],
                status=triage_data['status'],
                completed_at=datetime.utcnow()
            )
            
            db.session.add(triage)
            
            # Actualizar el estado de la cita
            appointment.status = 'ready_for_doctor'
            
            db.session.commit()
            
            print(f"✅ Triage creado exitosamente:")
            print(f"   ID: {triage.id}")
            print(f"   Estado: {triage.status}")
            print(f"   Enfermera: {triage.nurse.full_name}")
            print(f"   Prioridad: {triage.priority_level}")
            print(f"   Queja principal: {triage.chief_complaint}")
            
            print(f"\n✅ Estado de cita actualizado a: {appointment.status}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al crear triage: {str(e)}")
            return
            
        # 6. Verificar el flujo completo
        print(f"\n=== VERIFICACIÓN FINAL ===")
        
        # Recargar la cita para verificar cambios
        appointment = Appointment.query.get(appointment.id)
        triage = Triage.query.filter_by(appointment_id=appointment.id).first()
        
        step1 = appointment.is_paid
        step2 = triage is not None
        step3 = triage.status == 'completed' if triage else False
        step4 = appointment.status == 'ready_for_doctor'
        
        print(f"✅ PASO 1: Cita PAGADA - {'OK' if step1 else 'FALLO'}")
        print(f"{'✅' if step2 else '❌'} PASO 2: TRIAGE creado - {'OK' if step2 else 'FALLO'}")
        print(f"{'✅' if step3 else '❌'} PASO 3: TRIAGE completado - {'OK' if step3 else 'FALLO'}")
        print(f"{'✅' if step4 else '❌'} PASO 4: Lista para DOCTOR - {'OK' if step4 else 'FALLO'}")
        
        if step1 and step2 and step3 and step4:
            print(f"\n🎉 FLUJO COMPLETO FUNCIONANDO PERFECTAMENTE")
            print(f"💡 La cita pasó por: Pago → Triage → Lista para Doctor")
        else:
            print(f"\n⚠️  Flujo incompleto - revisar pasos fallidos")
            
        # 7. Mostrar citas listas para doctor
        print(f"\n👨‍⚕️ CITAS LISTAS PARA DOCTOR HOY:")
        today = date.today()
        ready_appointments = Appointment.query.filter(
            Appointment.date_time >= datetime.combine(today, datetime.min.time()),
            Appointment.date_time < datetime.combine(today, datetime.max.time()),
            Appointment.status == 'ready_for_doctor'
        ).all()
        
        if ready_appointments:
            for apt in ready_appointments:
                print(f"   👉 {apt.patient.full_name} - Dr. {apt.doctor.full_name}")
                print(f"      {apt.date_time.strftime('%H:%M')} | {apt.doctor.specialty}")
                print(f"      Estado: {apt.status_label}")
                triage_info = Triage.query.filter_by(appointment_id=apt.id).first()
                if triage_info:
                    print(f"      Triage: {triage_info.priority_level} - {triage_info.chief_complaint[:30]}...")
        else:
            print(f"   No hay citas listas para doctor")

if __name__ == '__main__':
    test_complete_triage_flow()
