"""
Configuración para scripts de prueba
"""

import sys
import os

# Agregar el directorio padre al path para importar la app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuraciones de prueba
TEST_DATABASE_URL = 'sqlite:///test.db'
TESTING = True
SECRET_KEY = 'test-secret-key'

# Configuración de logging para pruebas
LOGGING_LEVEL = 'INFO'

# Configuración de datos de prueba
TEST_PATIENT_DATA = {
    'first_name': 'Juan',
    'last_name': 'Pérez',
    'email': 'juan.perez@test.com'
}

TEST_DOCTOR_DATA = {
    'first_name': 'Ana',
    'last_name': 'García',
    'role': 'doctor'
}

TEST_NURSE_DATA = {
    'first_name': 'Carmen',
    'last_name': 'Ruiz',
    'role': 'nurse'
}

# Configuración de servicios de prueba
TEST_SERVICE_PRICE = 120.00
TEST_TAX_RATE = 0.18
