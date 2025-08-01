# src/utils/invoice_template.py
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib import colors

class InvoiceTemplate:

    def safe_float(self, value):
        try:
            num = float(value)
            if not (num == num and num != float('inf') and num != float('-inf')):
                return 0.0
            return num
        except Exception:
            return 0.0

    def safe_int(self, value):
        try:
            num = int(float(value))
            return num
        except Exception:
            return 0
    def __init__(self, canvas, width, height, settings):
        self.c = canvas
        self.width = width
        self.height = height
        self.settings = settings

    def draw_invoice(self, invoice_data):
        self.draw_modern_header()
        self.draw_modern_customer_info(invoice_data)
        self.draw_modern_invoice_details(invoice_data)
        self.draw_modern_items_table(invoice_data)
        self.draw_modern_summary(invoice_data)
        self.draw_modern_footer()

    def draw_modern_header(self):
        self.c.setFillColorRGB(0.13, 0.32, 0.56)
        self.c.rect(0, 760, self.width, 60, fill=1, stroke=0)
        self.c.setFillColorRGB(1, 1, 1)
        self.c.setFont("Helvetica-Bold", 28)
        self.c.drawString(50, 790, self.settings.company_name)
        self.c.setFont("Helvetica", 12)
        self.c.drawString(50, 775, self.settings.address)
        self.c.drawString(50, 760, f"GSTIN: {self.settings.gstin} | PAN: {self.settings.pan_number}")
        self.c.setFillColorRGB(0, 0, 0)

    def draw_modern_customer_info(self, invoice_data):
        self.c.setFont("Helvetica-Bold", 13)
        self.c.drawString(50, 730, "Bill To:")
        self.c.setFont("Helvetica", 12)
        self.c.drawString(120, 730, invoice_data['customer']['name'])
        self.c.drawString(120, 715, invoice_data['customer']['address'])
        self.c.drawString(120, 700, f"GSTIN: {invoice_data['customer']['gstin']}")

    def draw_modern_invoice_details(self, invoice_data):
        self.c.setFont("Helvetica-Bold", 13)
        self.c.drawString(350, 730, "Invoice Details:")
        self.c.setFont("Helvetica", 12)
        self.c.drawString(350, 715, f"Invoice #: {invoice_data['invoice_number']}")
        self.c.drawString(350, 700, f"Date: {invoice_data['date']}")
        self.c.drawString(350, 685, f"Vehicle: {invoice_data['vehicle_number']}")

    def draw_modern_items_table(self, invoice_data):
        self.c.setFont("Helvetica-Bold", 12)
        self.c.drawString(50, 660, "Items:")
        data = [["Product Name", "Price", "Quantity", "Total"]]
        for item in invoice_data['items']:
            data.append([
                item['product_name'],
                f"₹{item['price_per_unit']:,.2f}",
                str(item['quantity']),
                f"₹{item['quantity'] * item['price_per_unit']:,.2f}"
            ])
        table = Table(data, colWidths=[180, 80, 80, 80])
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ])
        table.setStyle(style)
        table.wrapOn(self.c, self.width, self.height)
        table.drawOn(self.c, 50, 600 - 24 * len(data))

    def draw_modern_summary(self, invoice_data):
        total = invoice_data['total_amount']
        self.c.setFont("Helvetica-Bold", 13)
        self.c.drawString(350, 570, f"Total: ₹{total:,.2f}")

    def draw_modern_footer(self):
        self.c.setFont("Helvetica-Oblique", 10)
        self.c.setFillColorRGB(0.4, 0.4, 0.4)
        self.c.drawString(50, 40, "Thank you for your business!")
        self.c.setFillColorRGB(0, 0, 0)

    def draw_header(self):
        self.c.setFont("Helvetica-Bold", 24)
        self.c.drawString(50, 750, self.settings.company_name)
        self.c.setFont("Helvetica", 12)
        self.c.drawString(50, 730, self.settings.address)
        self.c.drawString(50, 715, f"GSTIN: {self.settings.gstin}")
        self.c.drawString(50, 700, f"PAN: {self.settings.pan_number}")
        self.c.drawString(50, 685, f"Email: {self.settings.email}")
        self.c.drawString(50, 670, f"UPI ID: {self.settings.upi_id}")

    def draw_customer_info(self, invoice_data):
        self.c.setFont("Helvetica-Bold", 12)
        self.c.drawString(350, 750, "Bill To:")
        self.c.setFont("Helvetica", 12)
        self.c.drawString(350, 730, invoice_data['customer']['name'])
        self.c.drawString(350, 715, invoice_data['customer']['address'])
        self.c.drawString(350, 700, f"GSTIN: {invoice_data['customer']['gstin']}")

    def draw_invoice_details(self, invoice_data):
        self.c.setFont("Helvetica-Bold", 12)
        self.c.drawString(50, 630, f"Invoice Number: {invoice_data['invoice_number']}")
        self.c.drawString(50, 615, f"Invoice Date: {invoice_data['date']}")
        self.c.drawString(50, 600, f"Vehicle Number: {invoice_data['vehicle_number']}")

    def draw_items_table(self, invoice_data):
        table_data = [["#", "Product", "Quantity", "Price", "Total"]]
        for i, item in enumerate(invoice_data['items']):
            quantity = self.safe_int(item.get('quantity', 0))
            price_per_unit = self.safe_float(item.get('price_per_unit', 0.0))
            table_data.append([
                str(i + 1),
                item.get('product_name', ''),
                str(quantity),
                f"₹{price_per_unit:.2f}",
                f"₹{quantity * price_per_unit:.2f}"
            ])

        table = Table(table_data, colWidths=[30, 250, 70, 70, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        table.wrapOn(self.c, self.width, self.height)
        table.drawOn(self.c, 50, 450)

    def get_tax_info(self, subtotal, customer_state_code):
        if customer_state_code == self.settings.state_code:
            cgst = subtotal * 0.09
            sgst = subtotal * 0.09
            return {
                "tax_type": "CGST/SGST",
                "cgst": cgst,
                "sgst": sgst,
                "total_tax": cgst + sgst,
            }
        else:
            igst = subtotal * 0.18
            return {
                "tax_type": "IGST",
                "igst": igst,
                "total_tax": igst,
            }

    def draw_summary(self, invoice_data):
        subtotal = sum(self.safe_int(item.get('quantity', 0)) * self.safe_float(item.get('price_per_unit', 0.0)) for item in invoice_data['items'])
        tax_info = self.get_tax_info(subtotal, invoice_data['customer']['state_code'])
        total = subtotal + tax_info['total_tax']

        self.c.setFont("Helvetica-Bold", 12)
        self.c.drawString(400, 400, "Subtotal:")
        if tax_info['tax_type'] == 'IGST':
            self.c.drawString(400, 380, "IGST (18%):")
        else:
            self.c.drawString(400, 380, "CGST (9%):")
            self.c.drawString(400, 360, "SGST (9%):")
        self.c.drawString(400, 340, "Total:")

        self.c.setFont("Helvetica", 12)
        self.c.drawString(500, 400, f"₹{subtotal:.2f}")
        if tax_info['tax_type'] == 'IGST':
            self.c.drawString(500, 380, f"₹{tax_info['igst']:.2f}")
        else:
            self.c.drawString(500, 380, f"₹{tax_info['cgst']:.2f}")
            self.c.drawString(500, 360, f"₹{tax_info['sgst']:.2f}")
        self.c.drawString(500, 340, f"₹{total:.2f}")

    def draw_footer(self):
        self.c.setFont("Helvetica-Oblique", 10)
        self.c.drawString(50, 100, self.settings.tagline)
