#!/usr/bin/env python3
"""
Script para crear una cita y pago de prueba para triage
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.user import User
from app.models.specialty import Specialty
from app.models.invoice import Invoice, InvoiceService
from app import db
from datetime import datetime, date, time
from decimal import Decimal

def main():
    app = create_app()
    with app.app_context():
        print("=== CREANDO CITA Y PAGO DE PRUEBA PARA TRIAGE ===\n")
        
        # Buscar paciente (debe existir)
        patient = Patient.query.filter_by(dni='72114437').first()  # Jhon Daniel - Adulto
        if not patient:
            print("❌ No se encontró el paciente con DNI 72114437")
            return
        
        print(f"✅ Paciente: {patient.full_name}")
        print(f"   Edad: {patient.age} años")
        print(f"   Grupo etario: {patient.age_group_label}")
        
        # Buscar doctor y especialidad
        doctor = User.query.filter_by(role='doctor', is_active=True).first()
        specialty = Specialty.query.filter_by(name='Cardiología').first()
        
        if not doctor or not specialty:
            print("❌ No se encontró doctor o especialidad")
            return
        
        print(f"✅ Doctor: Dr. {doctor.full_name}")
        print(f"✅ Especialidad: {specialty.name} (S/ {specialty.base_price})")
        
        # Crear cita para HOY
        today = date.today()
        appointment_time = datetime.combine(today, time(9, 30))  # 9:30 AM hoy
        
        # Verificar si ya existe una cita
        existing_appointment = Appointment.query.filter(
            Appointment.patient_id == patient.id,
            Appointment.date_time >= datetime.combine(today, datetime.min.time()),
            Appointment.date_time < datetime.combine(today, datetime.max.time())
        ).first()
        
        if existing_appointment:
            print(f"✅ Ya existe cita para hoy: {existing_appointment.date_time}")
            appointment = existing_appointment
        else:
            # Crear nueva cita
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                specialty_id=specialty.id,
                date_time=appointment_time,
                reason="Consulta de control cardiológico",
                status='scheduled',
                notes="Cita de prueba para triage"
            )
            db.session.add(appointment)
            db.session.flush()
            print(f"✅ Cita creada: {appointment.date_time}")
        
        # Verificar si ya existe pago
        existing_invoice = Invoice.query.filter_by(appointment_id=appointment.id).first()
        
        if existing_invoice:
            print(f"✅ Ya existe pago: {existing_invoice.invoice_number} - {existing_invoice.status}")
        else:
            # Crear pago/factura
            invoice = Invoice(
                patient_id=patient.id,
                appointment_id=appointment.id,
                doctor_id=doctor.id,
                invoice_number=Invoice.get_next_invoice_number(),
                issue_date=today,
                due_date=today,
                subtotal=Decimal('0.00'),
                total_amount=Decimal('0.00'),
                discount_percentage=0.0,
                tax_percentage=0.0,
                status='paid',
                payment_date=today,
                payment_method='efectivo',
                notes=f"Consulta {specialty.name} - Dr. {doctor.full_name}",
                created_by=doctor.id  # Usar el doctor como creador por simplicidad
            )
            
            db.session.add(invoice)
            db.session.flush()
            
            # Crear servicio
            service = InvoiceService(
                invoice_id=invoice.id,
                description=f"Consulta médica - {specialty.name}",
                quantity=1,
                unit_price=specialty.base_price,
                notes=appointment.notes
            )
            
            db.session.add(service)
            
            # Recalcular totales
            invoice.calculate_totals()
            
            db.session.commit()
            
            print(f"✅ Pago creado: {invoice.invoice_number} - S/ {invoice.total_amount}")
        
        print(f"\n✅ LISTO PARA TRIAGE:")
        print(f"   - Paciente: {patient.full_name} ({patient.age_group_label})")
        print(f"   - Cita: Hoy {appointment.date_time.strftime('%H:%M')}")
        print(f"   - Estado: Pagado ✓")
        print(f"   - Doctor destino: Dr. {doctor.full_name}")

if __name__ == "__main__":
    main()
