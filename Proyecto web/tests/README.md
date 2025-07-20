# 🧪 TESTS - Sistema Médico

Esta carpeta contiene todos los archivos de prueba y scripts de demostración para el sistema médico.

## 📁 Estructura

### **Scripts de Prueba de Flujo de Trabajo**
- `test_today_flow.py` - Prueba del flujo con cita existente de hoy
- `test_triage_flow.py` - Prueba del flujo completo incluyendo triage
- `test_web_flow.py` - Simulación del flujo desde la perspectiva web
- `test_payment_flow.py` - Prueba del flujo de pago
- `test_paid_flow.py` - Prueba con factura ya pagada
- `demo_flow.py` - Demostración completa del flujo desde cero

### **Scripts de Prueba de Fechas**
- `test_available_dates.py` - Prueba de fechas disponibles
- `test_date_ranges.py` - Prueba de rangos de fechas
- `test_api_available_times.py` - Prueba de API de horarios disponibles

## 🚀 Uso

Para ejecutar cualquier prueba:

```bash
cd tests
python nombre_del_script.py
```

## 📝 Notas

- Los scripts están configurados para trabajar con la base de datos de desarrollo
- Algunos scripts crean datos de prueba que pueden necesitar limpieza posterior
- Los scripts requieren que el entorno virtual esté activado
