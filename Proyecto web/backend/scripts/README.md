# 🔧 Scripts del Sistema Médico

Esta carpeta contiene todos los scripts de utilidad, configuración y mantenimiento del sistema médico.

## 📁 Estructura

### **setup/** - Scripts de Configuración Inicial
Scripts que se ejecutan una sola vez para configurar el sistema inicial.

### **maintenance/** - Scripts de Mantenimiento
Scripts para actualizar, limpiar y mantener los datos del sistema.

### **utils/** - Scripts de Utilidades
Scripts para verificar, visualizar y diagnosticar el estado del sistema.

## 📋 Instrucciones de Uso

1. **Activar el entorno virtual**:
   ```bash
   cd backend
   venv\Scripts\activate
   ```

2. **Ejecutar un script**:
   ```bash
   python scripts/setup/seed_data.py
   ```

## ⚠️ Advertencias

- Los scripts de **setup** solo deben ejecutarse una vez
- Los scripts de **maintenance** pueden afectar datos existentes
- Siempre hacer backup antes de ejecutar scripts de mantenimiento
- Los scripts de **utils** son seguros para ejecutar en cualquier momento
