#!/usr/bin/env python3
"""
Script para poblar la base de datos PostgreSQL con usuarios iniciales del sistema médico
"""

import sys
import os

# Agregar el directorio padre al path para importar la app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.user import User

def create_initial_users():
    """Crear usuarios iniciales en la base de datos"""
    
    # Lista de usuarios a crear
    users_data = [
        {
            'username': 'admin',
            'password': 'admin123',
            'email': 'admin@clinica.com',
            'first_name': 'Administrador',
            'last_name': 'Sistema',
            'role': 'admin',
            'phone': '123-456-7890'
        },
        {
            'username': 'recep.sofia',
            'password': 'recep123',
            'email': 'sofia@clinica.com',
            'first_name': 'Sofía',
            'last_name': 'Torres',
            'role': 'receptionist',
            'phone': '123-456-7891'
        },
        {
            'username': 'dr.rodriguez',
            'password': 'doc123',
            'email': 'rodriguez@clinica.com',
            'first_name': 'Miguel',
            'last_name': 'Rodríguez',
            'role': 'doctor',
            'phone': '123-456-7892'
        },
        {
            'username': 'enf.carmen',
            'password': 'enf123',
            'email': 'carmen@clinica.com',
            'first_name': 'Carmen',
            'last_name': 'Enfermera',
            'role': 'nurse',
            'phone': '123-456-7893'
        }
    ]
    
    print("🏥 Iniciando creación de usuarios del sistema médico...")
    print("=" * 60)
    
    created_count = 0
    skipped_count = 0
    
    for user_data in users_data:
        # Verificar si el usuario ya existe
        existing_user = User.query.filter_by(username=user_data['username']).first()
        
        if existing_user:
            print(f"⚠️  Usuario '{user_data['username']}' ya existe - OMITIDO")
            skipped_count += 1
            continue
        
        # Crear nuevo usuario
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            role=user_data['role'],
            phone=user_data.get('phone'),
            is_active=True
        )
        
        # Establecer contraseña encriptada
        user.set_password(user_data['password'])
        
        # Agregar a la sesión
        db.session.add(user)
        
        print(f"✅ Usuario creado: {user_data['username']} ({user_data['role']}) - {user_data['first_name']} {user_data['last_name']}")
        created_count += 1
    
    try:
        # Confirmar cambios en la base de datos
        db.session.commit()
        print("=" * 60)
        print(f"🎉 ¡Proceso completado exitosamente!")
        print(f"📊 Resumen:")
        print(f"   - Usuarios creados: {created_count}")
        print(f"   - Usuarios omitidos: {skipped_count}")
        print(f"   - Total procesados: {created_count + skipped_count}")
        
        if created_count > 0:
            print("\n🔐 Credenciales de acceso:")
            print("-" * 40)
            for user_data in users_data:
                existing_user = User.query.filter_by(username=user_data['username']).first()
                if existing_user:
                    print(f"👤 {user_data['role'].upper()}: {user_data['username']} / {user_data['password']}")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al guardar usuarios: {str(e)}")
        return False
    
    return True

def main():
    """Función principal"""
    print("🚀 Iniciando script de población de usuarios...")
    
    # Crear la aplicación Flask
    app = create_app()
    
    # Ejecutar dentro del contexto de la aplicación
    with app.app_context():
        try:
            # Verificar conexión a la base de datos
            with db.engine.connect() as conn:
                conn.execute(db.text("SELECT 1"))
            print("✅ Conexión a PostgreSQL exitosa")
            
            # Crear usuarios
            success = create_initial_users()
            
            if success:
                print("\n🏥 ¡Sistema médico listo para usar!")
                print("🌐 Puedes iniciar la aplicación con: python run.py")
            else:
                print("\n❌ Hubo errores durante la creación de usuarios")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Error de conexión a la base de datos: {str(e)}")
            print("💡 Asegúrate de que PostgreSQL esté corriendo y el archivo .env esté configurado correctamente")
            sys.exit(1)

if __name__ == "__main__":
    main()
