#!/usr/bin/env python3
"""
Script para limpiar datos transaccionales antes de las pruebas
Mantiene: Usuarios, Especialidades, Comisiones, Horarios
Elimina: Pacientes, Citas, Registros Médicos, Triage, Facturas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.medical_record import MedicalRecord
from app.models.triage import Triage
from app.models.invoice import Invoice
from sqlalchemy import text

def clean_transactional_data():
    """Limpia todos los datos transaccionales manteniendo la configuración base"""
    
    print("🧹 Iniciando limpieza de datos transaccionales...")
    print("=" * 60)
    
    try:
        # Contar registros antes de eliminar
        patients_count = Patient.query.count()
        appointments_count = Appointment.query.count()
        medical_records_count = MedicalRecord.query.count()
        triage_count = Triage.query.count()
        invoices_count = Invoice.query.count()
        
        print(f"📊 DATOS ANTES DE LA LIMPIEZA:")
        print(f"   • Pacientes: {patients_count}")
        print(f"   • Citas: {appointments_count}")
        print(f"   • Registros Médicos: {medical_records_count}")
        print(f"   • Triage: {triage_count}")
        print(f"   • Facturas: {invoices_count}")
        print()
        
        # Deshabilitar restricciones de clave foránea temporalmente
        db.session.execute(text('PRAGMA foreign_keys = OFF'))
        
        # Eliminar datos transaccionales en el orden correcto
        print("🗑️  Eliminando datos transaccionales...")
        
        # 1. Eliminar facturas
        Invoice.query.delete()
        print("   ✅ Facturas eliminadas")
        
        # 2. Eliminar triage
        Triage.query.delete()
        print("   ✅ Registros de triage eliminados")
        
        # 3. Eliminar registros médicos
        MedicalRecord.query.delete()
        print("   ✅ Registros médicos eliminados")
        
        # 4. Eliminar citas
        Appointment.query.delete()
        print("   ✅ Citas eliminadas")
        
        # 5. Eliminar pacientes
        Patient.query.delete()
        print("   ✅ Pacientes eliminados")
        
        # Restablecer restricciones de clave foránea
        db.session.execute(text('PRAGMA foreign_keys = ON'))
        
        # Confirmar cambios
        db.session.commit()
        
        print()
        print("✅ LIMPIEZA COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        print("🔧 CONFIGURACIÓN MANTENIDA:")
        
        # Verificar que los datos de configuración siguen intactos
        from app.models.user import User
        from app.models.specialty import Specialty
        from app.models.work_schedule import WorkSchedule
        from app.models.salary_configuration import SalaryConfiguration
        
        users_count = User.query.count()
        specialties_count = Specialty.query.count()
        schedules_count = WorkSchedule.query.count()
        salary_configs_count = SalaryConfiguration.query.count()
        
        print(f"   • Usuarios: {users_count}")
        print(f"   • Especialidades: {specialties_count}")
        print(f"   • Horarios: {schedules_count}")
        print(f"   • Configuraciones de salario: {salary_configs_count}")
        
        print()
        print("📋 DATOS TRANSACCIONALES DESPUÉS DE LA LIMPIEZA:")
        print(f"   • Pacientes: {Patient.query.count()}")
        print(f"   • Citas: {Appointment.query.count()}")
        print(f"   • Registros Médicos: {MedicalRecord.query.count()}")
        print(f"   • Triage: {Triage.query.count()}")
        print(f"   • Facturas: {Invoice.query.count()}")
        
        print()
        print("🎯 SISTEMA LISTO PARA PRUEBAS DE LA FASE 5")
        print("   El sistema mantiene toda la configuración base")
        print("   Los datos transaccionales han sido eliminados")
        print("   Puede proceder con las pruebas del flujo del doctor")
        
    except Exception as e:
        print(f"❌ Error durante la limpieza: {str(e)}")
        db.session.rollback()
        raise
    
    finally:
        # Asegurar que las restricciones de clave foránea estén habilitadas
        db.session.execute(text('PRAGMA foreign_keys = ON'))
        db.session.commit()

def confirm_cleanup():
    """Confirma la limpieza con el usuario"""
    print("⚠️  ADVERTENCIA: Esta operación eliminará TODOS los datos transaccionales")
    print("   Se mantendrán: Usuarios, Especialidades, Comisiones, Horarios")
    print("   Se eliminarán: Pacientes, Citas, Registros Médicos, Triage, Facturas")
    print()
    
    response = input("¿Está seguro que desea continuar? (escriba 'SI' para confirmar): ").strip().upper()
    
    if response == 'SI':
        return True
    else:
        print("❌ Operación cancelada")
        return False

if __name__ == "__main__":
    # Crear aplicación Flask
    app = create_app()
    
    with app.app_context():
        if confirm_cleanup():
            clean_transactional_data()
        else:
            print("Limpieza cancelada por el usuario")
