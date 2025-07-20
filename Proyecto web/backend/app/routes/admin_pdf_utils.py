from flask import render_template
from weasyprint import HTML
import io


def render_report_pdf(stats, specialty_stats, monthly_stats, doctor_stats, start_date, end_date, period):
    """
    Renderiza el PDF del reporte administrativo usando una plantilla HTML.
    """
    html = render_template(
        'admin/report_pdf.html',
        stats=stats,
        specialty_stats=specialty_stats,
        monthly_stats=monthly_stats,
        doctor_stats=doctor_stats,
        start_date=start_date,
        end_date=end_date,
        period=period,
        title='Reporte Administrativo'
    )
    pdf_file = io.BytesIO()
    HTML(string=html).write_pdf(pdf_file)
    pdf_file.seek(0)
    return pdf_file
