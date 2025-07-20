# Backend - Sistema Médico

Este directorio contiene el backend del sistema médico construido con Flask.

## Estructura de Directorios

```
backend/
├── app/                    # Aplicación principal de Flask
│   ├── models/            # Modelos de datos (SQLAlchemy)
│   ├── routes/            # Rutas y controladores
│   └── utils/             # Utilidades de la aplicación
├── instance/              # Base de datos SQLite
├── migrations/            # Migraciones de Alembic
├── scripts/               # Scripts de desarrollo y mantenimiento
│   ├── maintenance/       # Scripts de mantenimiento de datos
│   ├── setup/            # Scripts de configuración inicial
│   ├── testing/          # Scripts de prueba y verificación
│   └── utils/            # Utilidades de desarrollo
├── config.py             # Configuración de la aplicación
├── requirements.txt      # Dependencias de Python
└── run.py               # Punto de entrada de la aplicación
```

## Archivos Principales

- **`run.py`**: Punto de entrada principal para ejecutar la aplicación Flask
- **`config.py`**: Configuración de la aplicación (base de datos, secretos, etc.)
- **`requirements.txt`**: Lista de dependencias de Python

## Scripts Organizados

### scripts/maintenance/
Scripts para mantenimiento y corrección de datos:
- `add_missing_sections.py` - Agregar secciones faltantes a historias clínicas
- `clean_orphaned_commissions.py` - Limpiar comisiones huérfanas
- `complete_medical_records.py` - Completar registros médicos incompletos
- `fix_drugs_section.py` - Corregir sección de drogas en historias clínicas
- `sync_miguel_dates.py` - Sincronizar fechas específicas

### scripts/setup/
Scripts para configuración inicial del sistema:
- `add_nurse_user.py` - Crear usuario enfermero
- `create_sample_patients.py` - Crear pacientes de muestra

### scripts/testing/
Scripts de prueba y verificación:
- `test_*.py` - Scripts de prueba para diferentes funcionalidades
- `create_test_appointment.py` - Crear cita de prueba

### scripts/utils/
Utilidades de desarrollo y análisis:
- `analyze_*.py` - Scripts de análisis de datos
- `check_*.py` - Scripts de verificación del sistema
- `debug_*.py` - Scripts de depuración
- `verify_*.py` - Scripts de verificación de funcionalidades
- `view_database.py` - Visualizar contenido de la base de datos

## Ejecución

Para ejecutar la aplicación:
```bash
cd backend
python run.py
```

Para ejecutar scripts:
```bash
cd backend
python scripts/testing/test_script_name.py
python scripts/maintenance/maintenance_script.py
```

## Desarrollo

- Mantener los scripts organizados en sus respectivas carpetas
- Usar la carpeta `testing/` para nuevos scripts de prueba
- Usar la carpeta `maintenance/` para scripts de corrección de datos
- Usar la carpeta `utils/` para herramientas de desarrollo
- Documentar los scripts con comentarios claros

## Base de Datos

La base de datos SQLite se encuentra en:
- `instance/medical_system.db` - Base de datos principal
- `instance/medical_system_backup.db` - Respaldo de la base de datos

Las migraciones se manejan con Alembic en el directorio `migrations/`.
