# 🚀 Scripts de Configuración Inicial

Estos scripts se ejecutan una sola vez para configurar el sistema inicial.

## 📋 Scripts Disponibles

### **seed_data.py**
- **Propósito**: Poblar la base de datos con datos iniciales
- **Uso**: `python seed_data.py`
- **Descripción**: Crea usuarios, especialidades, pacientes y datos básicos

### **add_nurse_user.py**
- **Propósito**: Agregar usuarios con rol de enfermera
- **Uso**: `python add_nurse_user.py`
- **Descripción**: Crea usuarios específicos para el rol de enfermería

### **setup_commissions.py**
- **Propósito**: Configurar el sistema de comisiones
- **Uso**: `python setup_commissions.py`
- **Descripción**: Establece configuraciones de comisiones para médicos

### **setup_work_schedules.py**
- **Propósito**: Configurar horarios de trabajo iniciales
- **Uso**: `python setup_work_schedules.py`
- **Descripción**: Establece horarios de trabajo para médicos

## ⚠️ Importante

- Estos scripts solo deben ejecutarse UNA VEZ
- Ejecutar en orden si hay dependencias
- Hacer backup de la base de datos antes de ejecutar
