// JavaScript principal del Sistema de Gestión Médica

document.addEventListener('DOMContentLoaded', function() {
    
    // Auto-hide alerts después de 5 segundos
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Confirmar acciones de eliminación
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('¿Estás seguro de que deseas eliminar este elemento?')) {
                e.preventDefault();
            }
        });
    });
    
    // Validación de formularios
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Tooltips de Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Manejo del menú móvil
    const mobileMenuToggle = document.querySelector('[data-bs-target="#sidebarMenu"]');
    const sidebar = document.getElementById('sidebarMenu');
    
    if (mobileMenuToggle && sidebar) {
        // Cerrar menú al hacer clic en un enlace (solo en móvil)
        const sidebarLinks = sidebar.querySelectorAll('.nav-link');
        sidebarLinks.forEach(function(link) {
            link.addEventListener('click', function() {
                if (window.innerWidth < 768) {
                    const bsCollapse = new bootstrap.Collapse(sidebar, {
                        hide: true
                    });
                }
            });
        });
        
        // Cerrar menú al hacer clic fuera del sidebar (solo en móvil)
        document.addEventListener('click', function(event) {
            if (window.innerWidth < 768) {
                const isClickInsideSidebar = sidebar.contains(event.target);
                const isClickOnToggle = mobileMenuToggle.contains(event.target);
                
                if (!isClickInsideSidebar && !isClickOnToggle && sidebar.classList.contains('show')) {
                    const bsCollapse = new bootstrap.Collapse(sidebar, {
                        hide: true
                    });
                }
            }
        });
    }
    
    // Ajustar layout en cambio de orientación/tamaño de pantalla
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 768 && sidebar && sidebar.classList.contains('show')) {
            // En desktop, asegurar que el sidebar esté visible
            sidebar.classList.remove('show');
        }
    });
    
    console.log('Sistema de Gestión Médica - JavaScript cargado correctamente');
});
