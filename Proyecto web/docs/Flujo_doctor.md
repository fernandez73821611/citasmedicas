Esta bien asi, entonces lo siguiente que te voy a mostrar seria los correcto:
✅ Lo que está correcto:
Verificar si el paciente es nuevo en el sistema
Crear historia clínica completa para pacientes nuevos
Ver historia existente para pacientes que ya tienen una
Realizar anamnesis por cada consulta
Mostrar historias completas (con información de otros doctores)

FLUJO PRECISO
Paciente llega al doctor →
¿Tiene historia clínica?
├── NO → Crear historia clínica completa + Anamnesis + Consulta
└── SÍ → Ver historia existente + Anamnesis + Consulta
Separar en dos formularios:

Historia Clínica (una vez por paciente) → Datos completos del MINSA
Consulta/Anamnesis (cada consulta) → Motivo, enfermedad actual, examen físico, diagnóstico, tratamiento

mportante:
Anamnesis se hace SIEMPRE (paciente nuevo o no)
La historia clínica se crea una sola vez por paciente
Cada consulta agrega un nuevo registro médico
3. En "Historias Clínicas":
Mostrar todas las historias de pacientes que el doctor ha atendido
Incluir información completa (otros doctores también)
Filtrar por: solo mis pacientes (no mostrar pacientes de otros doctores)
4. Sugerencia adicional:
En el dashboard, mostrar si el paciente "Tiene historia" o es "Paciente nuevo"
Botones diferentes: "Crear Historia + Consulta" vs "Ver Historia + Consulta"

Datos del minsa
Datos de Identificación (Header)
Número de Historia Clínica (único)
Fecha de apertura
Datos del paciente: nombres, apellidos, DNI, fecha nacimiento, edad, sexo
Dirección y teléfono
Persona de contacto de emergencia
Anamnesis (Por cada consulta)
Motivo de consulta (por qué viene el paciente)
Enfermedad actual (historia detallada del problema actual)
Antecedentes personales: enfermedades previas, cirugías, alergias, medicamentos
Antecedentes familiares: enfermedades hereditarias relevantes
Hábitos: tabaco, alcohol, drogas, actividad física
Examen Físico
Signos vitales: presión arterial, pulso, temperatura, respiración, peso, talla
Examen físico general y por sistemas
Examen regional (según la especialidad)
Diagnóstico y Plan
Diagnóstico presuntivo/definitivo (usar CIE-10)
Exámenes auxiliares solicitados
Tratamiento prescrito
Indicaciones y recomendaciones
Próxima cita
Datos Administrativos
Fecha y hora de atención
Médico tratante (nombre, CMP, firma)
Especialidad

✅ Reglas Excelentes y Bien Definidas:
🔍 1. NO INVENTAR - BASARSE EN ARCHIVOS EXISTENTES
Principio fundamental correcto: revisar estructura antes de crear
Evita código inconsistente y duplicado
Mantiene patrones arquitectónicos establecidos
💬 2. SOLICITAR CONTEXTO ANTES DE IMPLEMENTAR
Metodología sólida: análisis previo antes de implementación
Previene errores por falta de comprensión del sistema
Asegura integración adecuada con código existente
📝 3. DESARROLLO TAREA POR TAREA
Enfoque incremental y controlado
Permite validación continua
Reduce riesgos de implementación
✋ 4. CONFIRMACIÓN OBLIGATORIA ENTRE TAREAS
Control de calidad excelente
Evita avanzar con errores
Asegura comprensión y aprobación
🔄 5. FLUJO DE TRABAJO ESTABLECIDO
Proceso claro y repetible
Pasos lógicos y ordenados
Metodología profesional

## IMPLEMENTACIÓN

## **Fase 1: Modelos de Base de Datos** ✅ **COMPLETADO**
- [x] ✅ Crear modelo `MedicalHistory` (Historia Clínica)
- [x] ✅ Actualizar modelo `MedicalRecord` (Registro Médico/Consulta)
- [x] ✅ Establecer relaciones entre modelos
- [x] ✅ Crear migración de base de datos (implementación lógica)

## **Fase 2: Formularios y Templates** ✅ **COMPLETADO**
- [x] ✅ Crear formulario de Historia Clínica (datos MINSA)
- [x] ✅ Actualizar formulario de Consulta/Anamnesis
- [x] ✅ Crear template para nueva historia clínica
- [x] ✅ Actualizar template de consulta

## **Fase 3: Lógica de Negocio** ✅ **COMPLETADO**
- [x] ✅ Implementar verificación de historia existente
- [x] ✅ Crear lógica para generar número único de historia
- [x] ✅ Implementar flujo condicional (paciente nuevo/existente)
- [x] ✅ Actualizar rutas del doctor

## **Fase 4: Dashboard y Navegación** ✅ **COMPLETADO**
- [x] ✅ Modificar dashboard para mostrar estado del paciente
- [x] ✅ Crear botones diferenciados ("Crear Historia + Consulta" vs "Ver Historia + Consulta")
- [x] ✅ Actualizar sección "Historias Clínicas" con filtros
- [x] ✅ Implementar visualización completa de historias

## **Fase 5: Validación y Pruebas**
- [ ] Probar flujo completo con pacientes nuevos
- [ ] Probar flujo con pacientes existentes
- [ ] Validar numeración única de historias
- [ ] Verificar acceso correcto a historias por doctor