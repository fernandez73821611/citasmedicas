#!/usr/bin/env python3
"""
Script para crear una cita de hoy con factura pagada y probar el flujo completo
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.appointment import Appointment
from app.models.invoice import Invoice, InvoiceService
from app.models.patient import Patient
from app.models.user import User
from app.models.specialty import Specialty
from app.models.triage import Triage
from datetime import datetime, date, timedelta
from decimal import Decimal

def test_complete_flow():
    """Crear una cita de hoy con factura pagada y probar el flujo completo"""
    app = create_app()
    with app.app_context():
        print("=== TESTING FLUJO COMPLETO HOY ===\n")
        
        # 1. Obtener datos necesarios
        patient = Patient.query.first()
        doctor = User.query.filter_by(role='doctor').first()
        specialty = Specialty.query.first()
        
        if not all([patient, doctor, specialty]):
            print("❌ Faltan datos básicos (paciente, doctor o especialidad)")
            return
            
        # 2. Crear cita para hoy
        today = date.today()
        appointment_time = datetime.combine(today, datetime.strptime("14:30", "%H:%M").time())
        
        try:
            # Verificar si ya existe una cita similar
            existing = Appointment.query.filter_by(
                patient_id=patient.id,
                doctor_id=doctor.id,
                date_time=appointment_time
            ).first()
            
            if existing:
                appointment = existing
                print(f"📋 Usando cita existente:")
            else:
                appointment = Appointment(
                    patient_id=patient.id,
                    doctor_id=doctor.id,
                    specialty_id=specialty.id,
                    date_time=appointment_time,
                    reason="Consulta de control",
                    status='scheduled'
                )
                db.session.add(appointment)
                db.session.flush()
                print(f"📋 Cita NUEVA creada:")
            
            print(f"   ID: {appointment.id}")
            print(f"   Paciente: {appointment.patient.full_name}")
            print(f"   Doctor: Dr. {appointment.doctor.full_name}")
            print(f"   Especialidad: {appointment.specialty.name}")
            print(f"   Fecha: {appointment.date_time.strftime('%d/%m/%Y %H:%M')}")
            print(f"   Estado: {appointment.status}")
            
        except Exception as e:
            print(f"❌ Error creando cita: {e}")
            db.session.rollback()
            return
            
        # 3. Crear factura PAGADA
        try:
            # Verificar si ya tiene factura
            existing_invoice = Invoice.query.filter_by(appointment_id=appointment.id).first()
            if existing_invoice:
                invoice = existing_invoice
                if invoice.status != 'paid':
                    invoice.status = 'paid'
                    invoice.payment_date = today
                    invoice.payment_method = 'efectivo'
                    db.session.commit()
                print(f"💰 Usando factura existente (marcada como pagada):")
            else:
                invoice = Invoice(
                    patient_id=appointment.patient_id,
                    appointment_id=appointment.id,
                    doctor_id=appointment.doctor_id,
                    invoice_number=Invoice.get_next_invoice_number(),
                    issue_date=today,
                    due_date=today,
                    subtotal=Decimal('150.00'),
                    discount_percentage=Decimal('0.0'),
                    discount_amount=Decimal('0.0'),
                    tax_percentage=Decimal('0.0'),
                    tax_amount=Decimal('0.0'),
                    total_amount=Decimal('150.00'),
                    status='paid',  # PAGADA
                    payment_date=today,
                    payment_method='efectivo',
                    created_by=appointment.doctor_id,
                    notes='Consulta médica'
                )
                
                db.session.add(invoice)
                db.session.flush()
                
                # Crear servicio
                service = InvoiceService(
                    invoice_id=invoice.id,
                    description=f'Consulta médica - {appointment.specialty.name}',
                    quantity=1,
                    unit_price=Decimal('150.00')
                )
                
                db.session.add(service)
                db.session.commit()
                print(f"💰 Factura NUEVA creada y PAGADA:")
            
            print(f"   Número: {invoice.invoice_number}")
            print(f"   Estado: {invoice.status}")
            print(f"   Monto: S/ {invoice.total_amount}")
            print(f"   Fecha pago: {invoice.payment_date}")
            
        except Exception as e:
            print(f"❌ Error creando factura: {e}")
            db.session.rollback()
            return
            
        # 4. Verificar estado de la cita
        print(f"\n🔍 VERIFICACIÓN DE ESTADO:")
        print(f"   appointment.is_paid: {appointment.is_paid}")
        print(f"   appointment.payment_status: {appointment.payment_status}")
        print(f"   appointment.can_start_triage(): {appointment.can_start_triage()}")
        
        # 5. Simular vista de enfermería
        from sqlalchemy import and_
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
        
        print(f"\n👩‍⚕️ VISTA DE ENFERMERÍA (CITAS PAGADAS HOY):")
        print(f"   Total citas pagadas disponibles: {len(paid_appointments)}")
        
        if appointment in paid_appointments:
            print(f"   ✅ ESTA CITA ESTÁ VISIBLE para enfermería")
        else:
            print(f"   ❌ Esta cita NO está visible")
            # Investigar por qué
            has_triage = Triage.query.filter_by(appointment_id=appointment.id).first()
            if has_triage:
                print(f"   Razón: Ya tiene triage (ID: {has_triage.id})")
            else:
                print(f"   Investigando razones...")
                
        # 6. Listar todas las citas pagadas de hoy
        if paid_appointments:
            print(f"\n📋 LISTA COMPLETA DE CITAS PAGADAS PARA TRIAGE HOY:")
            for i, apt in enumerate(paid_appointments, 1):
                is_current = apt.id == appointment.id
                marker = "👉" if is_current else "  "
                print(f"   {marker} {i}. {apt.patient.full_name} - Dr. {apt.doctor.full_name}")
                print(f"      {apt.date_time.strftime('%H:%M')} | {apt.specialty.name}")
                # Buscar factura asociada
                apt_invoice = Invoice.query.filter_by(appointment_id=apt.id).first()
                print(f"      Factura: {apt_invoice.invoice_number} ({apt_invoice.status})")
                if is_current:
                    print(f"      ⭐ ESTA ES NUESTRA CITA DE PRUEBA")
        else:
            print(f"\n⚠️  NO HAY CITAS PAGADAS DISPONIBLES PARA TRIAGE HOY")
            
        # 7. Verificar si tiene triage
        existing_triage = Triage.query.filter_by(appointment_id=appointment.id).first()
        if existing_triage:
            print(f"\n🩺 TRIAGE EXISTENTE:")
            print(f"   ID: {existing_triage.id}")
            print(f"   Estado: {existing_triage.status}")
            print(f"   Enfermera: {existing_triage.nurse.full_name}")
            if existing_triage.status == 'completed':
                print(f"   ✅ Triage COMPLETADO - Listo para doctor")
            else:
                print(f"   ⏳ Triage EN PROCESO")
        else:
            print(f"\n🩺 Sin triage - Disponible para enfermería")
            
        print(f"\n=== RESUMEN FINAL ===")
        step1 = appointment.is_paid
        step2 = appointment in paid_appointments
        step3 = existing_triage and existing_triage.status == 'completed'
        
        print(f"✅ PASO 1: Cita PAGADA - {'OK' if step1 else 'FALLO'}")
        print(f"{'✅' if step2 else '❌'} PASO 2: VISIBLE para enfermería - {'OK' if step2 else 'FALLO'}")
        
        if step2:
            if existing_triage:
                if step3:
                    print(f"✅ PASO 3: Triage COMPLETADO - OK")
                    print(f"✅ PASO 4: Lista para doctor - OK")
                    print(f"\n🎉 FLUJO COMPLETO FUNCIONANDO")
                else:
                    print(f"⏳ PASO 3: Triage en proceso")
            else:
                print(f"⏳ PASO 3: Pendiente de triage")
        
        if step1 and step2:
            print(f"\n✅ FLUJO PRINCIPAL FUNCIONANDO CORRECTAMENTE")
            print(f"💡 La enfermera puede ver y hacer triage a esta cita")
        elif step1:
            print(f"\n⚠️  Cita pagada pero no visible para enfermería")
        else:
            print(f"\n❌ Flujo bloqueado - verificar pago")

if __name__ == '__main__':
    test_complete_flow()
