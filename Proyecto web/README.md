# Sistema de Gestión Médica

Este proyecto es un sistema web para gestión de consultorios y clínicas médicas desarrollado con Flask.

## 🏗️ Estructura del Proyecto

```
sistema-gestion-medica/
├── backend/                    # Lógica del servidor
│   ├── app/                   # Aplicación Flask
│   │   ├── models/            # Modelos de base de datos
│   │   ├── routes/            # Rutas y controladores
│   │   └── utils/             # Utilidades
│   ├── config.py              # Configuraciones
│   ├── requirements.txt       # Dependencias Python
│   └── run.py                 # Punto de entrada
├── frontend/                  # Interface de usuario
│   ├── templates/             # Plantillas HTML
│   └── static/                # CSS, JS, imágenes
├── docs/                      # Documentación del proyecto
│   ├── sprints/               # Documentos de mejoras por sprint
│   └── README.md              # Índice de documentación
├── tests/                     # Archivos de prueba y demos
│   └── README.md              # Guía de pruebas
└── venv/                      # Entorno virtual Python
```

## 🚀 Instalación y Configuración

### Prerrequisitos
- Python 3.8+
- pip (gestor de paquetes de Python)

### Pasos de instalación

1. **Clonar el repositorio**
   ```bash
   git clone <url-del-repositorio>
   cd sistema-gestion-medica
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # En Windows
   # source venv/bin/activate  # En Linux/Mac
   ```

3. **Instalar dependencias**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```

5. **Inicializar base de datos**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Ejecutar la aplicación**
   ```bash
   python run.py
   ```

## 📚 Documentación

Para información detallada sobre el sistema, consulta los siguientes documentos:

- **[docs/README.md](docs/README.md)** - Índice completo de documentación
- **[docs/CRONOGRAMA_MEJORAS.md](docs/CRONOGRAMA_MEJORAS.md)** - Plan de desarrollo y mejoras
- **[docs/FLUJO_TRABAJO_DETALLADO.md](docs/FLUJO_TRABAJO_DETALLADO.md)** - Flujos de trabajo por rol
- **[docs/ROLE_DEFINITION.md](docs/ROLE_DEFINITION.md)** - Definición de roles y permisos

## 🧪 Pruebas

Los archivos de prueba están organizados en la carpeta `tests/`. Para más información:

- **[tests/README.md](tests/README.md)** - Guía de pruebas y scripts disponibles

## 👥 Roles de Usuario

- **Administrador**: Gestión completa del sistema
- **Médico**: Atención de pacientes y gestión de historiales
- **Enfermera**: Triage y evaluación inicial de pacientes
- **Recepcionista**: Programación de citas y facturación

## 🛠️ Tecnologías Utilizadas

- **Backend**: Flask, SQLAlchemy, Flask-Login
- **Frontend**: Bootstrap 5, Jinja2
- **Base de datos**: SQLite
- **Autenticación**: Flask-Login + Werkzeug

## 📝 Licencia

Este proyecto es para fines académicos.
