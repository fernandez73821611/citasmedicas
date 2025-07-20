"""
Script para generar datos de prueba del sistema de comisiones
"""
import sys
import os

# Agregar el directorio backend al path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.salary_configuration import SalaryConfiguration, CommissionRecord
from app.models.specialty import Specialty
from app.models.invoice import Invoice
from app.models.patient import Patient
from app.models.appointment import Appointment
from datetime import datetime, timedelta
import random

def create_sample_salary_configurations():
    """Crear configuraciones de salario de ejemplo"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 Creando configuraciones de salario de ejemplo...")
            
            # Obtener doctores existentes
            doctors = User.query.filter_by(role='doctor', is_active=True).all()
            
            if not doctors:
                print("❌ No se encontraron doctores en el sistema.")
                return
            
            # Porcentajes de ejemplo
            sample_percentages = [35.0, 40.0, 42.5, 45.0, 38.0, 50.0]
            
            created_count = 0
            for i, doctor in enumerate(doctors):
                # Verificar si ya tiene configuración
                existing = SalaryConfiguration.query.filter_by(doctor_id=doctor.id).first()
                
                if not existing:
                    percentage = sample_percentages[i % len(sample_percentages)]
                    
                    config = SalaryConfiguration(
                        doctor_id=doctor.id,
                        commission_percentage=percentage,
                        is_active=True,
                        effective_from=datetime.utcnow().date()
                    )
                    
                    db.session.add(config)
                    created_count += 1
                    print(f"✅ Dr. {doctor.full_name}: {percentage}% comisión")
            
            if created_count > 0:
                db.session.commit()
                print(f"✅ {created_count} configuraciones de salario creadas exitosamente.")
            else:
                print("ℹ️ Todos los doctores ya tienen configuraciones de salario.")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al crear configuraciones: {str(e)}")


def simulate_commission_generation():
    """Simular generación de comisiones para facturas existentes"""
    app = create_app()
    
    with app.app_context():
        try:
            print("💰 Simulando generación de comisiones...")
            
            # Obtener facturas pagadas sin comisiones
            paid_invoices = Invoice.query.filter_by(status='paid').all()
            
            if not paid_invoices:
                print("❌ No se encontraron facturas pagadas.")
                return
            
            generated_count = 0
            for invoice in paid_invoices:
                # Verificar si ya tiene comisión
                existing_commission = CommissionRecord.query.filter_by(invoice_id=invoice.id).first()
                
                if not existing_commission:
                    commission = CommissionRecord.generate_commission_for_invoice(invoice)
                    if commission:
                        generated_count += 1
                        print(f"✅ Comisión generada para factura {invoice.invoice_number}: S/ {commission.commission_amount}")
            
            print(f"✅ {generated_count} comisiones generadas exitosamente.")
                
        except Exception as e:
            print(f"❌ Error al generar comisiones: {str(e)}")


def show_commission_summary():
    """Mostrar resumen de comisiones"""
    app = create_app()
    
    with app.app_context():
        try:
            print("\n📊 RESUMEN DE COMISIONES")
            print("=" * 50)
            
            # Obtener estadísticas
            total_commissions = db.session.query(db.func.sum(CommissionRecord.commission_amount)).scalar() or 0
            total_records = CommissionRecord.query.count()
            unique_doctors = db.session.query(CommissionRecord.doctor_id).distinct().count()
            
            print(f"💰 Total en comisiones: S/ {total_commissions:.2f}")
            print(f"📋 Total registros: {total_records}")
            print(f"👨‍⚕️ Doctores con comisiones: {unique_doctors}")
            
            if total_records > 0:
                print(f"📈 Promedio por comisión: S/ {total_commissions/total_records:.2f}")
            
            # Mostrar top 3 doctores
            print("\n🏆 TOP 3 DOCTORES POR COMISIONES:")
            top_doctors = db.session.query(
                User.first_name,
                User.last_name,
                db.func.sum(CommissionRecord.commission_amount).label('total'),
                db.func.count(CommissionRecord.id).label('count')
            ).join(
                CommissionRecord, User.id == CommissionRecord.doctor_id
            ).group_by(
                User.id, User.first_name, User.last_name
            ).order_by(
                db.func.sum(CommissionRecord.commission_amount).desc()
            ).limit(3).all()
            
            for i, doctor in enumerate(top_doctors, 1):
                print(f"{i}. Dr. {doctor.first_name} {doctor.last_name}: S/ {doctor.total:.2f} ({doctor.count} comisiones)")
                
        except Exception as e:
            print(f"❌ Error al mostrar resumen: {str(e)}")


def main():
    """Función principal para ejecutar todas las simulaciones"""
    print("🚀 INICIANDO CONFIGURACIÓN DEL SISTEMA DE COMISIONES")
    print("=" * 60)
    
    # Crear configuraciones de salario
    create_sample_salary_configurations()
    
    print("\n" + "=" * 60)
    
    # Simular generación de comisiones
    simulate_commission_generation()
    
    print("\n" + "=" * 60)
    
    # Mostrar resumen
    show_commission_summary()
    
    print("\n✅ CONFIGURACIÓN COMPLETADA")
    print("\n💡 Ahora puede:")
    print("   1. Acceder a /admin/salary-management para configurar comisiones")
    print("   2. Acceder a /admin/commission-reports para ver reportes")
    print("   3. Las comisiones se generarán automáticamente al pagar facturas")


if __name__ == "__main__":
    main()
