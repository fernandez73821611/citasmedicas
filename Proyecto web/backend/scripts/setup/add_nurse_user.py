#!/usr/bin/env python3
"""
Script para agregar usuario enfermera a la base de datos existente
Sistema de Gestión Médica - Proyecto Académico
"""

import os
from app import create_app, db
from app.models.user import User

def add_nurse_user():
    """Agregar usuario enfermera a la base de datos"""
    
    # Crear la aplicación
    app = create_app(os.getenv('FLASK_ENV') or 'default')
    
    with app.app_context():
        print("🏥 Agregando usuario enfermera al sistema...")
        
        # Verificar si ya existe una enfermera
        existing_nurse = User.query.filter_by(role='nurse').first()
        if existing_nurse:
            print(f"   ⚠️  Ya existe una enfermera: {existing_nurse.full_name}")
            return
        
        # Verificar si el username ya existe
        existing_user = User.query.filter_by(username='enf.carmen').first()
        if existing_user:
            print(f"   ⚠️  El usuario 'enf.carmen' ya existe")
            return
        
        # Crear usuario enfermera
        nurse_user = User(
            username='enf.carmen',
            email='carmen.enfermera@clinica.com',
            first_name='Carmen',
            last_name='Ruiz',
            phone='987654327',
            role='nurse',
            is_active=True
        )
        
        # Establecer contraseña
        nurse_user.set_password('enf123')
        
        # Agregar a la base de datos
        db.session.add(nurse_user)
        db.session.commit()
        
        print(f"   ✅ Usuario enfermera creado exitosamente:")
        print(f"      - Usuario: enf.carmen")
        print(f"      - Contraseña: enf123")
        print(f"      - Nombre: Carmen Ruiz")
        print(f"      - Email: carmen.enfermera@clinica.com")
        print(f"      - Rol: nurse")
        print(f"      - Estado: Activo")
        print()
        print("🔐 Credenciales de acceso:")
        print("   Usuario: enf.carmen")
        print("   Contraseña: enf123")
        print()
        print("🎯 Ahora puedes hacer login con el perfil de enfermera!")

if __name__ == '__main__':
    add_nurse_user()
