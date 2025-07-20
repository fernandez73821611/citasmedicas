#!/usr/bin/env python3
"""
Script para verificar el flujo de pago → enfermería → doctor
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.appointment import Appointment
from app.models.invoice import Invoice
from app.models.triage import Triage
from app.models.patient import Patient
from app.models.user import User
from datetime import datetime, date

def test_payment_flow():
    """Probar el flujo de pago completo"""
    app = create_app()
    with app.app_context():
        print("=== TESTING FLUJO PAGO → ENFERMERÍA → DOCTOR ===\n")
        
        # 1. Obtener una cita para probar
        appointment = Appointment.query.filter_by(status='scheduled').first()
        if not appointment:
            print("❌ No hay citas programadas para probar")
            return
            
        print(f"📋 Probando con cita ID: {appointment.id}")
        print(f"   Paciente: {appointment.patient.full_name}")
        print(f"   Doctor: Dr. {appointment.doctor.full_name}")
        print(f"   Fecha: {appointment.date_time.strftime('%d/%m/%Y %H:%M')}")
        print(f"   Estado: {appointment.status}")
        
        # 2. Verificar estado inicial de pago
        print(f"\n💰 ESTADO DE PAGO:")
        print(f"   is_paid: {appointment.is_paid}")
        print(f"   payment_status: {appointment.payment_status}")
        
        if appointment.invoice:
            print(f"   Factura: {appointment.invoice.invoice_number}")
            print(f"   Estado factura: {appointment.invoice.status}")
            print(f"   Monto: S/ {appointment.invoice.total_amount}")
        else:
            print("   ❌ No tiene factura asociada")
            
        # 3. Verificar si puede hacer triage
        print(f"\n🩺 DISPONIBILIDAD PARA TRIAGE:")
        print(f"   can_start_triage(): {appointment.can_start_triage()}")
        
        # 4. Simular consulta de enfermería
        from sqlalchemy import and_
        today = date.today()
        paid_appointments = Appointment.query.join(
            Invoice, Appointment.id == Invoice.appointment_id
        ).filter(
            and_(
                Appointment.date_time >= datetime.combine(today, datetime.min.time()),
                Appointment.date_time < datetime.combine(today, datetime.max.time()),
                Appointment.status == 'scheduled',
                Invoice.status == 'paid'
            )
        ).outerjoin(
            Triage, Appointment.id == Triage.appointment_id
        ).filter(
            Triage.id.is_(None)  # Sin triage existente
        ).all()
        
        print(f"\n👩‍⚕️ VISTA DE ENFERMERÍA:")
        print(f"   Citas pagadas disponibles para triage hoy: {len(paid_appointments)}")
        
        if appointment in paid_appointments:
            print(f"   ✅ Esta cita ESTÁ disponible para enfermería")
        else:
            print(f"   ❌ Esta cita NO está disponible para enfermería")
            
        # 5. Mostrar todas las citas pagadas de hoy
        if paid_appointments:
            print(f"\n📋 LISTA DE CITAS PAGADAS PARA TRIAGE:")
            for i, apt in enumerate(paid_appointments, 1):
                print(f"   {i}. {apt.patient.full_name} - Dr. {apt.doctor.full_name}")
                print(f"      Hora: {apt.date_time.strftime('%H:%M')} | Factura: {apt.invoice.invoice_number}")
        
        # 6. Verificar si ya tiene triage
        existing_triage = Triage.query.filter_by(appointment_id=appointment.id).first()
        if existing_triage:
            print(f"\n🔍 TRIAGE EXISTENTE:")
            print(f"   ID: {existing_triage.id}")
            print(f"   Estado: {existing_triage.status}")
            print(f"   Enfermera: {existing_triage.nurse.full_name}")
            print(f"   Prioridad: {existing_triage.priority_level}")
            
            if existing_triage.status == 'completed':
                print(f"   ✅ Triage COMPLETADO - Cita lista para doctor")
                print(f"   Estado de cita debería ser: ready_for_doctor")
                print(f"   Estado actual de cita: {appointment.status}")
            else:
                print(f"   ⏳ Triage EN PROCESO")
        else:
            print(f"\n🔍 TRIAGE: No tiene triage asociado")
            
        print(f"\n=== RESUMEN DEL FLUJO ===")
        if appointment.is_paid:
            print("✅ PASO 1: Cita PAGADA - OK")
            if appointment in paid_appointments:
                print("✅ PASO 2: VISIBLE para enfermería - OK") 
                if existing_triage and existing_triage.status == 'completed':
                    print("✅ PASO 3: Triage COMPLETADO - OK")
                    print("✅ PASO 4: Disponible para doctor - OK")
                    print("\n🎉 FLUJO COMPLETO FUNCIONANDO CORRECTAMENTE")
                elif existing_triage:
                    print("⏳ PASO 3: Triage EN PROCESO")
                    print("⏳ PASO 4: Esperando completar triage")
                else:
                    print("⏳ PASO 3: Falta realizar triage")
                    print("⏳ PASO 4: Esperando triage")
            else:
                print("❌ PASO 2: NO VISIBLE para enfermería")
        else:
            print("❌ PASO 1: Cita NO PAGADA")
            print("❌ PASO 2: NO VISIBLE para enfermería")
            print("❌ FLUJO BLOQUEADO - Necesita pago")

if __name__ == '__main__':
    test_payment_flow()
