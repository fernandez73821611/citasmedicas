#!/usr/bin/env python3
"""
Script simple para listar todas las rutas disponibles
"""

import sys
import os

# Agregar el directorio backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

try:
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        print("TODAS LAS RUTAS DISPONIBLES:")
        print("=" * 60)
        
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
                'url': str(rule)
            })
        
        # Filtrar solo rutas de nurse
        nurse_routes = [r for r in routes if r['endpoint'].startswith('nurse.')]
        
        print("RUTAS DE ENFERMERÍA:")
        print("-" * 30)
        for route in sorted(nurse_routes, key=lambda x: x['url']):
            print(f"{route['url']} -> {route['endpoint']} [{', '.join(route['methods'])}]")
        
        # Buscar específicamente la ruta que necesitamos
        triage_route = next((r for r in nurse_routes if '/triage/<int:appointment_id>' in r['url']), None)
        
        print("\n" + "=" * 60)
        if triage_route:
            print("✓ LA RUTA /nurse/triage/<int:appointment_id> ESTÁ DISPONIBLE")
            print(f"  Endpoint: {triage_route['endpoint']}")
            print(f"  Métodos: {triage_route['methods']}")
        else:
            print("✗ LA RUTA /nurse/triage/<int:appointment_id> NO SE ENCONTRÓ")
            
        print(f"\nTotal de rutas de enfermería: {len(nurse_routes)}")
        
except Exception as e:
    print(f"Error al cargar la aplicación: {e}")
    import traceback
    traceback.print_exc()
