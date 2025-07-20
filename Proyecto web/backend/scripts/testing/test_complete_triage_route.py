#!/usr/bin/env python3
"""
Script para verificar que la ruta complete_triage esté disponible
"""

import sys
sys.path.append('.')

from app import create_app
from app.routes.nurse import bp

def test_complete_triage_route():
    """Verificar que la ruta complete_triage esté registrada"""
    app = create_app()
    
    with app.app_context():
        # Verificar que el blueprint nurse esté registrado
        if 'nurse' in app.blueprints:
            print("✅ Blueprint 'nurse' registrado correctamente")
        else:
            print("❌ Blueprint 'nurse' no está registrado")
            return
        
        # Verificar las rutas disponibles en el blueprint nurse
        nurse_routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint and rule.endpoint.startswith('nurse.'):
                nurse_routes.append(rule.endpoint)
        
        print(f"\n📋 Rutas disponibles en nurse:")
        for route in sorted(nurse_routes):
            print(f"   - {route}")
        
        # Verificar específicamente si complete_triage existe
        if 'nurse.complete_triage' in nurse_routes:
            print(f"\n✅ Ruta 'nurse.complete_triage' encontrada")
        else:
            print(f"\n❌ Ruta 'nurse.complete_triage' NO encontrada")
            print("   Rutas de triage disponibles:")
            triage_routes = [r for r in nurse_routes if 'triage' in r]
            for route in triage_routes:
                print(f"   - {route}")
        
        # Buscar información específica sobre complete_triage
        for rule in app.url_map.iter_rules():
            if rule.endpoint == 'nurse.complete_triage':
                print(f"\n🔍 Detalles de complete_triage:")
                print(f"   - Patrón URL: {rule.rule}")
                print(f"   - Métodos: {rule.methods}")
                break

if __name__ == "__main__":
    test_complete_triage_route()
