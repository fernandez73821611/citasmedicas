#!/usr/bin/env python3
"""
Script para verificar rutas directamente con Flask
"""

import sys
import os

# Agregar el directorio backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app import create_app

def test_flask_routes():
    """Probar las rutas directamente con Flask"""
    
    app = create_app()
    
    with app.test_client() as client:
        print("Probando ruta: /nurse/triage/2")
        print("=" * 40)
        
        # Probar la ruta específica
        response = client.get('/nurse/triage/2')
        
        print(f"Código de estado: {response.status_code}")
        
        if response.status_code == 302:
            # Redirección (probablemente por autenticación)
            location = response.headers.get('Location', 'No location')
            print(f"Redirección a: {location}")
            if '/auth/login' in location:
                print("✓ La ruta existe pero requiere autenticación")
            else:
                print("? Redirección inesperada")
        elif response.status_code == 404:
            print("✗ Error 404 - La ruta no se encontró")
            print("Contenido de la respuesta:")
            print(response.get_data(as_text=True)[:500])
        elif response.status_code == 500:
            print("✗ Error 500 - Error interno del servidor")
            print("Contenido de la respuesta:")
            print(response.get_data(as_text=True)[:500])
        else:
            print(f"Código de estado: {response.status_code}")
            print("Contenido de la respuesta:")
            print(response.get_data(as_text=True)[:500])

if __name__ == "__main__":
    test_flask_routes()
