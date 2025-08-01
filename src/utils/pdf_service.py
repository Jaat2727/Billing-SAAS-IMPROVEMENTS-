# src/utils/pdf_service.py
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from .invoice_template import InvoiceTemplate

class PdfService:
    def __init__(self, settings):
        self.settings = settings

    def generate_invoice(self, invoice_data, file_path=None):
        if file_path is None:
            file_path = f"invoice_{invoice_data['invoice_number']}.pdf"
        c = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter

        template = InvoiceTemplate(c, width, height, self.settings)
        template.draw_invoice(invoice_data)

        c.save()
        return file_path
