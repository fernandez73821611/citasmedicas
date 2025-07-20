"""
Script para crear una nueva cita y demostrar el flujo completo paso a paso
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.user import User
from app.models.invoice import Invoice, InvoiceService
from app.models.triage import Triage
from app.models.specialty import Specialty
from datetime import datetime, date, timedelta
from decimal import Decimal

def demo_complete_flow():
    """Demostrar el flujo completo desde cero"""
    app = create_app()
    with app.app_context():
        print("=== DEMOSTRACIÓN COMPLETA DEL FLUJO DE TRABAJO ===\n")
        
        # 1. Crear nueva cita
        print("PASO 1: 📋 RECEPCIONISTA PROGRAMA NUEVA CITA")
        
        # Buscar paciente y doctor
        patient = Patient.query.filter_by(first_name='Juan').first()
        doctor = User.query.filter_by(role='doctor').first()
        specialty = Specialty.query.first()
        
        if not patient or not doctor:
            print("❌ No se encontraron paciente o doctor")
            return
        
        # Crear cita para hoy (fecha actual)
        appointment_time = datetime.combine(date.today(), datetime.min.time()) + timedelta(hours=15)  # 3 PM hoy
        
        new_appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            specialty_id=specialty.id,
            date_time=appointment_time,
            reason="Consulta general de seguimiento",
            status="scheduled"
        )
        
        db.session.add(new_appointment)
        db.session.commit()
        
        print(f"✅ Cita creada:")
        print(f"   ID: {new_appointment.id}")
        print(f"   Paciente: {new_appointment.patient.full_name}")
        print(f"   Doctor: {new_appointment.doctor.full_name}")
        print(f"   Hora: {new_appointment.date_time.strftime('%H:%M')}")
        print(f"   Estado: {new_appointment.status}")
        print(f"   Pagado: {new_appointment.is_paid}")
        
        # 2. Crear factura
        print(f"\nPASO 2: 💰 RECEPCIONISTA GENERA FACTURA")
        
        # Buscar el número de factura más alto
        last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
        next_number = 1 if not last_invoice else last_invoice.id + 1
        
        # Buscar un usuario para created_by (recepcionista)
        receptionist = User.query.filter_by(role='receptionist').first()
        if not receptionist:
            receptionist = User.query.first()  # Usar cualquier usuario si no hay recepcionista
        
        invoice = Invoice(
            patient_id=new_appointment.patient_id,
            appointment_id=new_appointment.id,
            doctor_id=new_appointment.doctor_id,
            invoice_number=f"FAC-{next_number:06d}",
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            status='pending',
            subtotal=Decimal('120.00'),
            tax_amount=Decimal('21.60'),
            total_amount=Decimal('141.60'),
            notes='Consulta médica general',
            created_by=receptionist.id
        )
        
        db.session.add(invoice)
        db.session.commit()
        
        # Crear servicio de factura
        invoice_service = InvoiceService(
            invoice_id=invoice.id,
            description="Consulta médica general",
            quantity=1,
            unit_price=Decimal('120.00'),
            notes="Consulta de seguimiento"
        )
        
        db.session.add(invoice_service)
        db.session.commit()
        
        print(f"✅ Factura creada:")
        print(f"   Número: {invoice.invoice_number}")
        print(f"   Monto: S/ {invoice.total_amount}")
        print(f"   Estado: {invoice.status}")
        print(f"   Fecha vencimiento: {invoice.due_date}")
        
        # 3. Verificar estado antes del pago
        print(f"\nPASO 3: 🔍 VERIFICACIÓN ANTES DEL PAGO")
        print(f"   Cita pagada: {new_appointment.is_paid}")
        print(f"   Estado pago: {new_appointment.payment_status}")
        print(f"   Puede iniciar triage: {new_appointment.can_start_triage()}")
        
        # Verificar visibilidad en enfermería
        today = date.today()
        paid_appointments = Appointment.query.join(
            Invoice, Appointment.id == Invoice.appointment_id
        ).filter(
            Appointment.date_time >= datetime.combine(today, datetime.min.time()),
            Appointment.date_time < datetime.combine(today, datetime.max.time()),
            Appointment.status == 'scheduled',
            Invoice.status == 'paid'
        ).outerjoin(
            Triage, Appointment.id == Triage.appointment_id
        ).filter(
            Triage.id.is_(None)
        ).all()
        
        visible_before = new_appointment.id in [apt.id for apt in paid_appointments]
        print(f"   Visible para enfermería: {visible_before}")
        
        # 4. Procesar pago
        print(f"\nPASO 4: 💳 PROCESANDO PAGO")
        
        invoice.status = 'paid'
        invoice.payment_date = date.today()
        invoice.payment_method = 'efectivo'
        
        db.session.commit()
        
        print(f"✅ Pago procesado:")
        print(f"   Estado factura: {invoice.status}")
        print(f"   Fecha pago: {invoice.payment_date}")
        print(f"   Método: {invoice.payment_method}")
        
        # 5. Verificar estado después del pago
        print(f"\nPASO 5: 🔍 VERIFICACIÓN DESPUÉS DEL PAGO")
        
        # Recargar la cita
        new_appointment = Appointment.query.get(new_appointment.id)
        
        print(f"   Cita pagada: {new_appointment.is_paid}")
        print(f"   Estado pago: {new_appointment.payment_status}")
        print(f"   Puede iniciar triage: {new_appointment.can_start_triage()}")
        
        # Verificar visibilidad en enfermería
        paid_appointments = Appointment.query.join(
            Invoice, Appointment.id == Invoice.appointment_id
        ).filter(
            Appointment.date_time >= datetime.combine(today, datetime.min.time()),
            Appointment.date_time < datetime.combine(today, datetime.max.time()),
            Appointment.status == 'scheduled',
            Invoice.status == 'paid'
        ).outerjoin(
            Triage, Appointment.id == Triage.appointment_id
        ).filter(
            Triage.id.is_(None)
        ).all()
        
        visible_after = new_appointment.id in [apt.id for apt in paid_appointments]
        print(f"   Visible para enfermería: {visible_after}")
        
        if visible_after:
            print(f"   ✅ LA CITA AHORA ES VISIBLE PARA ENFERMERÍA")
        else:
            print(f"   ❌ La cita no es visible para enfermería")
        
        # 6. Simular dashboard de enfermería
        print(f"\nPASO 6: 👩‍⚕️ DASHBOARD DE ENFERMERÍA")
        
        print(f"   Citas pagadas pendientes de triage: {len(paid_appointments)}")
        
        if paid_appointments:
            print(f"   📋 Citas disponibles para triage:")
            for apt in paid_appointments:
                marker = "👉" if apt.id == new_appointment.id else "  "
                print(f"      {marker} {apt.patient.full_name} - {apt.date_time.strftime('%H:%M')}")
                if apt.id == new_appointment.id:
                    print(f"         ⭐ NUESTRA CITA DE DEMOSTRACIÓN")
        
        # 7. Resumen final
        print(f"\n=== RESUMEN FINAL ===")
        
        steps = [
            ("Cita programada", new_appointment.status == 'scheduled'),
            ("Factura generada", invoice is not None),
            ("Pago procesado", invoice.status == 'paid'),
            ("Cita marcada como pagada", new_appointment.is_paid),
            ("Visible para enfermería", visible_after),
            ("Lista para triage", new_appointment.can_start_triage())
        ]
        
        print(f"   Estado del flujo:")
        for i, (paso, completado) in enumerate(steps, 1):
            estado = "✅" if completado else "❌"
            print(f"      {i}. {estado} {paso}")
        
        completados = sum(1 for _, completado in steps if completado)
        total = len(steps)
        
        print(f"\n   Progreso: {completados}/{total} pasos completados")
        
        if completados == total:
            print(f"\n🎉 FLUJO FUNCIONANDO PERFECTAMENTE")
            print(f"💡 La cita pagada está lista para que la enfermera haga triage")
        else:
            print(f"\n⚠️  Hay problemas en el flujo")
        
        print(f"\n✅ DEMOSTRACIÓN COMPLETA")
        print(f"📝 ID de la cita para pruebas: {new_appointment.id}")

if __name__ == '__main__':
    demo_complete_flow()
