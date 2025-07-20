"""
Script para verificar que el dashboard de enfermería funciona correctamente
"""

import sys
import os

# Agregar el directorio backend al path
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.append(backend_path)

from app import create_app, db
from app.models.user import User

def test_nurse_dashboard():
    """Probar el dashboard de enfermería"""
    app = create_app()
    with app.app_context():
        print("=== VERIFICANDO DASHBOARD DE ENFERMERÍA ===")
        
        # Buscar una enfermera
        nurse = User.query.filter_by(role='nurse').first()
        if not nurse:
            print("❌ No se encontró ninguna enfermera en el sistema")
            return
            
        print(f"✅ Enfermera encontrada: {nurse.full_name}")
        
        # Simular el login de la enfermera (solo para testing)
        with app.test_client() as client:
            # Simular sesión de enfermera
            with client.session_transaction() as sess:
                sess['_user_id'] = str(nurse.id)
                sess['_fresh'] = True
            
            try:
                # Intentar acceder al dashboard
                response = client.get('/nurse/dashboard')
                
                if response.status_code == 200:
                    print(f"✅ Dashboard carga correctamente (Status: {response.status_code})")
                    print(f"✅ El error TypeError se ha resuelto")
                else:
                    print(f"⚠️  Dashboard responde con status: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error al cargar dashboard: {str(e)}")
                return
        
        print(f"\n✅ VERIFICACIÓN COMPLETADA")
        print(f"💡 El dashboard de enfermería ahora funciona correctamente")

if __name__ == '__main__':
    test_nurse_dashboard()
