#!/usr/bin/env python3
"""
Script para verificar el flujo creando una factura pagada
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.appointment import Appointment
from app.models.invoice import Invoice, InvoiceService
from app.models.patient import Patient
from app.models.user import User
from datetime import datetime, date
from decimal import Decimal

def test_with_paid_invoice():
    """Crear una factura pagada y probar el flujo"""
    app = create_app()
    with app.app_context():
        print("=== TESTING CON FACTURA PAGADA ===\n")
        
        # 1. Obtener una cita sin factura
        appointment = Appointment.query.filter(
            Appointment.status == 'scheduled',
            ~Appointment.id.in_(db.session.query(Invoice.appointment_id).filter(Invoice.appointment_id.isnot(None)))
        ).first()
        
        if not appointment:
            print("❌ No hay citas sin factura para probar")
            return
            
        print(f"📋 Cita seleccionada:")
        print(f"   ID: {appointment.id}")
        print(f"   Paciente: {appointment.patient.full_name}")
        print(f"   Doctor: Dr. {appointment.doctor.full_name}")
        print(f"   Fecha: {appointment.date_time.strftime('%d/%m/%Y %H:%M')}")
        
        # 2. Crear factura
        try:
            invoice = Invoice(
                patient_id=appointment.patient_id,
                appointment_id=appointment.id,
                doctor_id=appointment.doctor_id,
                invoice_number=Invoice.get_next_invoice_number(),
                issue_date=date.today(),
                due_date=date.today(),
                subtotal=Decimal('150.00'),
                discount_percentage=Decimal('0.0'),
                discount_amount=Decimal('0.0'),
                tax_percentage=Decimal('0.0'),
                tax_amount=Decimal('0.0'),
                total_amount=Decimal('150.00'),
                status='paid',  # MARCAMOS COMO PAGADA
                payment_date=date.today(),
                payment_method='efectivo',
                created_by=appointment.doctor_id,
                notes='Pago de consulta médica'
            )
            
            db.session.add(invoice)
            db.session.flush()  # Para obtener el ID
            
            # Crear servicio de factura
            service = InvoiceService(
                invoice_id=invoice.id,
                description='Consulta médica - Cardiología',
                quantity=1,
                unit_price=Decimal('150.00')
            )
            
            db.session.add(service)
            db.session.commit()
            
            print(f"\n💰 FACTURA CREADA:")
            print(f"   Número: {invoice.invoice_number}")
            print(f"   Estado: {invoice.status}")
            print(f"   Monto: S/ {invoice.total_amount}")
            print(f"   Método pago: {invoice.payment_method}")
            print(f"   Fecha pago: {invoice.payment_date}")
            
        except Exception as e:
            print(f"❌ Error creando factura: {e}")
            db.session.rollback()
            return
            
        # 3. Re-verificar el estado de la cita
        db.session.refresh(appointment)  # Refrescar para obtener la nueva factura
        
        print(f"\n🔄 ESTADO ACTUALIZADO DE LA CITA:")
        print(f"   is_paid: {appointment.is_paid}")
        print(f"   payment_status: {appointment.payment_status}")
        print(f"   can_start_triage(): {appointment.can_start_triage()}")
        
        # 4. Verificar visibilidad para enfermería
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
        ).all()
        
        print(f"\n👩‍⚕️ VISTA DE ENFERMERÍA:")
        print(f"   Citas pagadas disponibles para triage hoy: {len(paid_appointments)}")
        
        if appointment in paid_appointments:
            print(f"   ✅ Esta cita AHORA ESTÁ disponible para enfermería")
        else:
            print(f"   ❌ Esta cita AÚN NO está disponible para enfermería")
            print(f"   Razón: Puede ser que la fecha no sea de hoy")
            
        # 5. Mostrar todas las citas pagadas de hoy
        if paid_appointments:
            print(f"\n📋 LISTA DE CITAS PAGADAS PARA TRIAGE HOY:")
            for i, apt in enumerate(paid_appointments, 1):
                is_current = apt.id == appointment.id
                marker = "👉" if is_current else "  "
                print(f"   {marker} {i}. {apt.patient.full_name} - Dr. {apt.doctor.full_name}")
                print(f"      Hora: {apt.date_time.strftime('%H:%M')} | Factura: {apt.invoice.invoice_number}")
                if is_current:
                    print(f"      ⭐ ESTA ES LA CITA QUE ACABAMOS DE PAGAR")
        
        print(f"\n=== RESUMEN FINAL ===")
        if appointment.is_paid:
            print("✅ PASO 1: Cita PAGADA - OK")
            if appointment in paid_appointments:
                print("✅ PASO 2: VISIBLE para enfermería - OK") 
                print("✅ FLUJO FUNCIONANDO CORRECTAMENTE")
                print("\n🎉 LA ENFERMERA AHORA PUEDE VER ESTA CITA PARA TRIAGE")
            else:
                print("⚠️  PASO 2: No visible (posiblemente por fecha)")
                print("💡 La cita puede no ser de hoy, pero el pago funciona")
        else:
            print("❌ Error: La cita debería estar pagada")

if __name__ == '__main__':
    test_with_paid_invoice()
