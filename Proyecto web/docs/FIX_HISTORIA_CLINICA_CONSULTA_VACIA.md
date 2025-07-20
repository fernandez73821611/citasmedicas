# CORRECCIÓN DE BUG: Historia Clínica Crea Consulta Vacía

## Problema Identificado

Cuando un paciente nuevo no tenía historia clínica y se usaba el formulario "Nueva Historia Clínica", había dos opciones:

1. **"Solo Guardar Historia"** - Debería crear solo la historia clínica sin consulta
2. **"Guardar Historia + Consulta"** - Debería crear historia clínica Y consulta médica

**BUG**: Al seleccionar "Solo Guardar Historia", el sistema creaba automáticamente una consulta médica vacía (sin síntomas ni diagnóstico) cuando no debería crear ninguna consulta.

## Causa del Problema

En la función `new_medical_history` (archivo `backend/app/routes/doctor.py`), se estaba creando **siempre** un `MedicalRecord` sin verificar la acción seleccionada por el usuario (`save` vs `save_and_consult`).

## Solución Implementada

### 1. Modificación de `new_medical_history` función

Se agregó lógica para verificar el parámetro `action` del formulario:

```python
action = request.form.get('action', 'save')

if action == 'save':
    # Solo guardar historia clínica - crear MedicalRecord con campos de consulta vacíos
    # pero con observaciones que contienen los antecedentes
    
elif action == 'save_and_consult':
    # Crear historia clínica Y consulta médica completa
    # Validar que síntomas y diagnóstico sean obligatorios
```

### 2. Modificación de `get_for_patient` función

Se mejoró la función `MedicalHistory.get_for_patient()` para que solo considere que un paciente tiene historia clínica si tiene registros médicos con **información sustancial**:

```python
has_substantial_info = any([
    record.symptoms and record.symptoms.strip(),
    record.diagnosis and record.diagnosis.strip(),
    record.treatment and record.treatment.strip(),
    record.prescriptions and record.prescriptions.strip(),
    has_substantial_observations,  # Observaciones con antecedentes
    record.blood_pressure,
    record.heart_rate,
    record.temperature,
    record.weight,
    record.height
])
```

### 3. Detección de Observaciones Sustanciales

Se agregó lógica para detectar observaciones que contienen información de historia clínica:

```python
has_substantial_observations = any([
    'ANTECEDENTES PERSONALES' in obs_upper,
    'ANTECEDENTES FAMILIARES' in obs_upper,
    'ALERGIAS' in obs_upper,
    'MEDICAMENTOS ACTUALES' in obs_upper,
    'HÁBITOS' in obs_upper,
    len(record.observations.strip()) > 50
])
```

## Comportamiento Correcto Ahora

### Opción 1: "Solo Guardar Historia"
- Crea un `MedicalRecord` con:
  - `symptoms` = vacío
  - `diagnosis` = vacío
  - `treatment` = vacío
  - `prescriptions` = vacío
  - `observations` = información estructurada de antecedentes
  - `appointment_id` = NULL (no asociado a cita)
- **NO aparece como consulta médica** en el historial de consultas
- **SÍ cuenta como historia clínica** porque tiene observaciones sustanciales

### Opción 2: "Guardar Historia + Consulta"
- Crea un `MedicalRecord` con:
  - `symptoms` = obligatorio
  - `diagnosis` = obligatorio
  - `treatment`, `prescriptions` = opcionales
  - `observations` = información estructurada de antecedentes + observaciones de consulta
  - `appointment_id` = ID de la cita (si viene de una cita)
- **SÍ aparece como consulta médica** en el historial
- **SÍ cuenta como historia clínica** porque tiene información sustancial
- **La cita se marca como completada** si viene de una cita

## Archivos Modificados

1. **`backend/app/routes/doctor.py`** - Función `new_medical_history`
2. **`backend/app/models/medical_history.py`** - Función `get_for_patient`

## Scripts de Verificación Creados

1. **`clean_empty_medical_records.py`** - Para limpiar registros completamente vacíos
2. **`analyze_medical_records.py`** - Para analizar registros existentes
3. **`test_medical_history_logic.py`** - Para verificar la lógica de historia clínica

## Resultado

- ✅ **"Solo Guardar Historia"** ya no crea consultas médicas vacías
- ✅ La información de historia clínica se preserva correctamente
- ✅ Los botones "+ Consulta" aparecen solo cuando hay citas pendientes
- ✅ El dashboard no muestra citas ya completadas
- ✅ Una consulta por cita (funcionalidad implementada correctamente)

## Fecha de Corrección

7 de julio de 2025
