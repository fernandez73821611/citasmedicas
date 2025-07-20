#!/usr/bin/env python3
"""
Script para verificar las rutas de enfermería
"""

import sys
import os

# Agregar el directorio backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app import create_app

def verify_nurse_routes():
    """Verificar que las rutas de enfermería están correctamente configuradas"""
    
    app = create_app()
    
    with app.app_context():
        # Obtener todas las rutas de la aplicación
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint.startswith('nurse.'):
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
                    'url': str(rule)
                })
        
        print("RUTAS DE ENFERMERÍA DISPONIBLES:")
        print("=" * 50)
        
        for route in sorted(routes, key=lambda x: x['url']):
            print(f"Endpoint: {route['endpoint']}")
            print(f"URL: {route['url']}")
            print(f"Métodos: {', '.join(route['methods'])}")
            print("-" * 30)
        
        # Verificar rutas específicas que necesitamos
        required_routes = [
            'nurse.dashboard',
            'nurse.triage_list',
            'nurse.new_triage',
            'nurse.start_triage_for_appointment',
            'nurse.view_triage'
        ]
        
        print("\nVERIFICACIÓN DE RUTAS REQUERIDAS:")
        print("=" * 50)
        
        existing_endpoints = [route['endpoint'] for route in routes]
        
        for required_route in required_routes:
            if required_route in existing_endpoints:
                print(f"✓ {required_route} - EXISTE")
            else:
                print(f"✗ {required_route} - FALTA")
        
        # Verificar específicamente la nueva ruta
        triage_appointment_route = next((r for r in routes if r['endpoint'] == 'nurse.start_triage_for_appointment'), None)
        if triage_appointment_route:
            print(f"\n✓ NUEVA RUTA AGREGADA CORRECTAMENTE:")
            print(f"  Endpoint: {triage_appointment_route['endpoint']}")
            print(f"  URL: {triage_appointment_route['url']}")
            print(f"  Métodos: {', '.join(triage_appointment_route['methods'])}")
        else:
            print(f"\n✗ LA NUEVA RUTA NO SE ENCONTRÓ")

if __name__ == "__main__":
    verify_nurse_routes()
