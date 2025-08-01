# src/utils/invoice_template.py
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer
from reportlab.lib import colors
from reportlab.lib.units import inch

class InvoiceTemplate:

    def __init__(self, canvas, width, height, settings):
        self.c = canvas
        self.width = width
        self.height = height
        self.settings = settings
        self.styles = getSampleStyleSheet()
        self.primary_color = colors.HexColor('#2c3e50')
        self.secondary_color = colors.HexColor('#34495e')
        self.text_color = colors.HexColor('#34495e')
        self.light_text_color = colors.HexColor('#ecf0f1')

    def safe_float(self, value):
        try:
            return float(value) if value is not None else 0.0
        except (ValueError, TypeError):
            return 0.0

    def safe_int(self, value):
        try:
            return int(self.safe_float(value))
        except (ValueError, TypeError):
            return 0

    def get_tax_info(self, subtotal, customer_state_code):
        if customer_state_code == self.settings.state_code:
            cgst = subtotal * 0.09
            sgst = subtotal * 0.09
            return { "tax_type": "CGST/SGST", "cgst": cgst, "sgst": sgst, "total_tax": cgst + sgst }
        else:
            igst = subtotal * 0.18
            return { "tax_type": "IGST", "igst": igst, "total_tax": igst }

    def draw_invoice(self, invoice_data):
        self.draw_header(invoice_data)
        self.draw_customer_info(invoice_data)
        table_y_end, subtotal = self.draw_items_table(invoice_data)
        self.draw_summary(invoice_data, subtotal, table_y_end - 0.2*inch)
        self.draw_footer()

    def draw_header(self, invoice_data):
        self.c.saveState()
        self.c.setFillColor(self.primary_color)
        self.c.rect(0, self.height - 1.2*inch, self.width, 1.2*inch, fill=1, stroke=0)

        self.c.setFillColor(self.light_text_color)
        self.c.setFont("Helvetica-Bold", 24)
        self.c.drawString(0.5*inch, self.height - 0.5*inch, self.settings.company_name.upper())

        self.c.setFont("Helvetica", 10)
        company_address = self.settings.address.split('\n')
        y_pos = self.height - 0.75*inch
        for line in company_address:
            self.c.drawString(0.5*inch, y_pos, line)
            y_pos -= 0.15*inch

        self.c.setFont("Helvetica-Bold", 18)
        self.c.setFillColor(colors.white)
        self.c.drawRightString(self.width - 0.5*inch, self.height - 0.5*inch, "INVOICE")

        self.c.setFont("Helvetica", 10)
        self.c.setFillColor(self.light_text_color)
        self.c.drawRightString(self.width - 0.5*inch, self.height - 0.75*inch, f"Invoice #: {invoice_data['invoice_number']}")
        self.c.drawRightString(self.width - 0.5*inch, self.height - 0.9*inch, f"Date: {invoice_data['date']}")

        self.c.restoreState()

    def draw_customer_info(self, invoice_data):
        self.c.saveState()
        self.c.setFont("Helvetica-Bold", 10)
        self.c.setFillColor(self.text_color)
        self.c.drawString(0.5*inch, self.height - 1.6*inch, "BILL TO:")

        p_style = self.styles['Normal']
        p_style.textColor = self.text_color
        p_style.fontName = 'Helvetica'
        p_style.fontSize = 10
        p_style.leading = 12

        customer_name = Paragraph(invoice_data['customer']['name'], p_style)
        customer_address = Paragraph(invoice_data['customer']['address'].replace('\n', '<br/>'), p_style)
        customer_gstin = Paragraph(f"GSTIN: {invoice_data['customer']['gstin']}", p_style)

        customer_name.wrapOn(self.c, 3*inch, 0.5*inch)
        customer_name.drawOn(self.c, 0.5*inch, self.height - 1.8*inch)

        customer_address.wrapOn(self.c, 3*inch, 1*inch)
        customer_address.drawOn(self.c, 0.5*inch, self.height - 2.0*inch - customer_name.height)

        customer_gstin.wrapOn(self.c, 3*inch, 0.5*inch)
        customer_gstin.drawOn(self.c, 0.5*inch, self.height - 2.2*inch - customer_name.height - customer_address.height)

        self.c.restoreState()

    def draw_items_table(self, invoice_data):
        header_style = ParagraphStyle(name='Header', parent=self.styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.white, alignment=TA_CENTER)

        data = [
            [Paragraph(h, header_style) for h in ["#", "ITEM DESCRIPTION", "PRICE", "QTY", "TOTAL"]]
        ]

        subtotal = 0
        normal_style_left = ParagraphStyle(name='NormalLeft', parent=self.styles['Normal'], alignment=TA_LEFT)
        normal_style_right = ParagraphStyle(name='NormalRight', parent=self.styles['Normal'], alignment=TA_RIGHT)

        for i, item in enumerate(invoice_data['items']):
            price = self.safe_float(item['price_per_unit'])
            quantity = self.safe_int(item['quantity'])
            total_item = price * quantity
            subtotal += total_item
            data.append([
                Paragraph(str(i + 1), self.styles['Normal']),
                Paragraph(item['product_name'], normal_style_left),
                Paragraph(f"₹{price:,.2f}", normal_style_right),
                Paragraph(str(quantity), self.styles['Normal']),
                Paragraph(f"₹{total_item:,.2f}", normal_style_right)
            ])

        table = Table(data, colWidths=[0.4*inch, 3.5*inch, 1.2*inch, 0.8*inch, 1.4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
        ]))

        table_height = table.wrapOn(self.c, self.width - inch, self.height)[1]
        table_y_start = self.height - 2.8*inch - table_height
        table.drawOn(self.c, 0.5*inch, table_y_start)

        return table_y_start, subtotal

    def draw_summary(self, invoice_data, subtotal, y_pos):
        tax_info = self.get_tax_info(subtotal, invoice_data['customer']['state_code'])
        total = subtotal + tax_info['total_tax']

        summary_data = [['Subtotal', f"₹{subtotal:,.2f}"]]
        if tax_info['tax_type'] == 'IGST':
            summary_data.append(['IGST (18%)', f"₹{tax_info['igst']:,.2f}"])
        else:
            summary_data.append(['CGST (9%)', f"₹{tax_info['cgst']:,.2f}"])
            summary_data.append(['SGST (9%)', f"₹{tax_info['sgst']:,.2f}"])

        summary_table = Table(summary_data, colWidths=[1.5*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
        ]))

        summary_table.wrapOn(self.c, 3*inch, 1*inch)
        summary_table.drawOn(self.c, self.width - 2*inch, y_pos)

        # Draw Total
        self.c.saveState()
        self.c.setFillColor(self.primary_color)
        self.c.rect(self.width - 2.5*inch, y_pos - 0.5*inch, 2*inch, 0.4*inch, fill=1, stroke=0)
        self.c.setFillColor(colors.white)
        self.c.setFont("Helvetica-Bold", 12)
        self.c.drawString(self.width - 2.4*inch, y_pos - 0.4*inch + 10, "Total:")
        self.c.drawRightString(self.width - 0.6*inch, y_pos - 0.4*inch + 10, f"₹{total:,.2f}")
        self.c.restoreState()

    def draw_footer(self):
        self.c.saveState()
        self.c.setFont("Helvetica", 9)
        self.c.setFillColor(self.text_color)

        terms_style = ParagraphStyle(name='Terms', parent=self.styles['Normal'], fontSize=9, textColor=self.text_color)
        terms = Paragraph("<b>Terms & Conditions:</b><br/>1. Please pay within 15 days.<br/>2. No returns after 30 days.", terms_style)
        terms.wrapOn(self.c, 4*inch, 1*inch)
        terms.drawOn(self.c, 0.5*inch, 1.2*inch)

        self.c.setFont("Helvetica-Bold", 10)
        self.c.drawString(self.width - 3.5*inch, 1.5*inch, "For " + self.settings.company_name)
        self.c.line(self.width - 3.5*inch, 0.8*inch, self.width - 0.5*inch, 0.8*inch)
        self.c.setFont("Helvetica", 9)
        self.c.drawRightString(self.width - 0.5*inch, 0.6*inch, "Authorized Signatory")

        self.c.setFont("Helvetica-Oblique", 8)
        self.c.setFillColor(colors.grey)
        self.c.drawCentredString(self.width/2.0, 0.25*inch, "This is a computer-generated invoice and does not require a signature.")
        self.c.restoreState()
