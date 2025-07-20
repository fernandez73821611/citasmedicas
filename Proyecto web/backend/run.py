import os
from app import create_app, db
from app.models import User, Patient, Appointment, MedicalRecord, Specialty
from app.models.invoice import Invoice, InvoiceService

# Crear la aplicación
app = create_app(os.getenv('FLASK_ENV') or 'default')

# Configurar el user_loader para Flask-Login
@app.login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Contexto de shell para facilitar debugging
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Patient': Patient, 
        'Appointment': Appointment,
        'MedicalRecord': MedicalRecord,
        'Specialty': Specialty,
        'Invoice': Invoice,
        'InvoiceService': InvoiceService
    }

if __name__ == '__main__':
    app.run(debug=True)
