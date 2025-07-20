# Configuración Completa de Grupos Etarios - Sistema Médico

## Grupos Etarios Definidos

### 1. **Lactante (0-2 años)**
- **Rango**: 0 meses a 23 meses (menores de 2 años)
- **Subcategorías médicas**:
  - Recién nacido: 0-28 días
  - Lactante menor: 1-6 meses
  - Lactante mayor: 6-24 meses
- **Restricciones en triage**:
  - ❌ **Presión arterial**: No medible confiablemente
  - ❌ **Frecuencia respiratoria**: Solo observación, no número exacto
  - ✅ **Frecuencia cardíaca**: CRÍTICO (100-160 bpm)
  - ✅ **Temperatura**: CRÍTICO (36.5-37.8°C)
  - ✅ **Peso**: CRÍTICO para desarrollo
  - ✅ **Altura**: CRÍTICO para desarrollo
- **Campos especiales**: Alimentación, sueño, irritabilidad, fontanela

### 2. **Preescolar (2-6 años)**
- **Rango**: 2 años a 5 años 11 meses
- **Subcategorías**:
  - Preescolar menor: 2-3 años
  - Preescolar mayor: 3-6 años
- **Restricciones en triage**:
  - **Menor de 3 años**:
    - ❌ **Presión arterial**: No confiable hasta los 3 años
    - ✅ **Frecuencia cardíaca**: CRÍTICO (90-130 bpm)
    - ✅ **Temperatura**: CRÍTICO (36.0-37.5°C)
    - ⚪ **Frecuencia respiratoria**: Opcional (12-20 rpm)
    - ✅ **Peso**: Importante para desarrollo
    - ✅ **Altura**: Importante para desarrollo
  - **3 años o más**:
    - ✅ **Presión arterial**: CRÍTICO (85-110/55-75 mmHg)
    - ✅ **Frecuencia cardíaca**: CRÍTICO (90-130 bpm)
    - ✅ **Temperatura**: CRÍTICO (36.0-37.5°C)
    - ⚪ **Frecuencia respiratoria**: Opcional (12-20 rpm)
    - ✅ **Peso**: Importante para desarrollo
    - ✅ **Altura**: Importante para desarrollo
- **Campos especiales**: Desarrollo psicomotor, vacunación

### 3. **Escolar (6-12 años)**
- **Rango**: 6 años a 11 años 11 meses
- **Restricciones en triage**:
  - ✅ **Presión arterial**: CRÍTICO (90-120/60-80 mmHg)
  - ✅ **Frecuencia cardíaca**: CRÍTICO (70-110 bpm)
  - ✅ **Temperatura**: CRÍTICO (36.0-37.5°C)
  - ⚪ **Frecuencia respiratoria**: Opcional (12-20 rpm)
  - ✅ **Peso**: Importante
  - ✅ **Altura**: Importante
- **Campos especiales**: Actividad física, rendimiento escolar

### 4. **Adolescente (12-18 años)**
- **Rango**: 12 años a 17 años 11 meses
- **Subcategorías**:
  - Adolescente temprano: 12-14 años
  - Adolescente tardío: 15-17 años
- **Restricciones en triage**:
  - ✅ **Presión arterial**: Normal (100-130/70-85 mmHg)
  - ✅ **Frecuencia cardíaca**: Normal (60-100 bpm)
  - ✅ **Temperatura**: Normal (36.0-37.5°C)
  - ⚪ **Frecuencia respiratoria**: Opcional (12-20 rpm)
  - ✅ **Peso**: Importante
  - ✅ **Altura**: Importante
- **Campos especiales**: Desarrollo sexual, privacidad, consentimiento

### 5. **Adulto (18+ años)**
- **Rango**: 18 años en adelante
- **Subcategorías**:
  - Adulto joven: 18-39 años
  - Adulto medio: 40-64 años
  - Adulto mayor: 65+ años
- **Restricciones en triage**:
  - ✅ **Presión arterial**: Normal (120/80 mmHg)
  - ✅ **Frecuencia cardíaca**: Normal (60-100 bpm)
  - ✅ **Temperatura**: Normal (36.0-37.5°C)
  - ⚪ **Frecuencia respiratoria**: Opcional (12-20 rpm)
  - ✅ **Peso**: Importante
  - ✅ **Altura**: Importante
- **Campos especiales**: Historial médico completo, medicamentos, antecedentes

## Casos Especiales Considerados

### Adulto Mayor (65+ años)
- **Consideraciones especiales**:
  - Presión arterial: Tolerancia hasta 140/90 mmHg
  - Frecuencia cardíaca: Puede ser más baja (50-90 bpm)
  - Temperatura: Puede ser más baja (35.5-37.0°C)
  - Polifarmacia: Múltiples medicamentos
  - Comorbilidades: Múltiples condiciones

### Embarazadas
- **Consideraciones especiales**:
  - Presión arterial: Vigilar preeclampsia
  - Frecuencia cardíaca: Puede estar elevada
  - Temperatura: Vigilar infecciones
  - Peso: Ganancia según trimestre

### Casos Límite
- **Paciente de 2 años exactos**: Se considera preescolar menor
- **Paciente de 6 años exactos**: Se considera escolar
- **Paciente de 12 años exactos**: Se considera adolescente
- **Paciente de 18 años exactos**: Se considera adulto

## Implementación en el Sistema

### Backend (Python)
```python
@property
def age_group(self):
    age = self.age
    if age < 2:
        return 'lactante'
    elif age < 6:
        return 'preescolar'
    elif age < 12:
        return 'escolar'
    elif age < 18:
        return 'adolescente'
    else:
        return 'adulto'
```

### Frontend (JavaScript)
```javascript
// Configuración aplicada en consultation_form.html
// Maneja todos los grupos etarios con restricciones específicas
```

### Validaciones
- Todos los campos obligatorios se marcan dinámicamente
- Campos bloqueados se deshabilitan visualmente
- Tooltips explicativos para cada restricción
- Validación de rangos normales por edad

## Recomendaciones Médicas

1. **Siempre consultar con el médico** para casos dudosos
2. **Documentar excepciones** cuando se salga de los rangos normales
3. **Considerar el contexto clínico** además de la edad
4. **Revisar periódicamente** los rangos según nuevas guías médicas
5. **Capacitar al personal** en las diferencias por grupo etario

---

**Nota**: Esta configuración sigue las guías pediátricas y médicas estándar, pero debe ser validada por profesionales médicos antes de uso en producción.
