# src/utils/invoice_template.py
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.units import inch
import os

class InvoiceTemplate:

    def __init__(self, canvas, width, height, settings):
        self.c = canvas
        self.width = width
        self.height = height
        self.settings = settings
        self.styles = getSampleStyleSheet()

        # Professional Color Scheme
        self.primary_color = colors.HexColor('#1A237E') # Deep Indigo
        self.secondary_color = colors.HexColor('#5C6BC0') # Lighter Indigo
        self.accent_color = colors.HexColor('#FF6F00') # Amber
        self.text_color = colors.HexColor('#263238') # Blue Grey
        self.light_text_color = colors.HexColor('#FFFFFF')
        self.subtle_gray = colors.HexColor('#ECEFF1')

        # Register a modern, clean font if available (e.g., Roboto)
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../resources/Roboto-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('Roboto', font_path))
        font_path_bold = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../resources/Roboto-Bold.ttf'))
        pdfmetrics.registerFont(TTFont('Roboto-Bold', font_path_bold))

        self.font_name = 'Roboto'
        self.font_name_bold = 'Roboto-Bold'

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
        is_intra_state = customer_state_code == self.settings.state_code
        if is_intra_state:
            cgst = subtotal * 0.09
            sgst = subtotal * 0.09
            return { "tax_type": "CGST/SGST", "cgst": cgst, "sgst": sgst, "igst": 0, "total_tax": cgst + sgst }
        else:
            igst = subtotal * 0.18
            return { "tax_type": "IGST", "cgst": 0, "sgst": 0, "igst": igst, "total_tax": igst }

    def draw_invoice(self, invoice_data):
        self.draw_header(invoice_data)
        self.draw_customer_info(invoice_data)
        table_y_end, subtotal = self.draw_items_table(invoice_data)
        self.draw_summary(invoice_data, subtotal, table_y_end - 0.3*inch)
        self.draw_footer()

    def draw_header(self, invoice_data):
        self.c.saveState()

        # Background rectangle
        self.c.setFillColor(self.primary_color)
        self.c.rect(0, self.height - 1.5*inch, self.width, 1.5*inch, fill=1, stroke=0)

        # Company Logo (if available)
        if self.settings.logo_path and os.path.exists(self.settings.logo_path):
            logo = Image(self.settings.logo_path, width=1*inch, height=1*inch)
            logo.drawOn(self.c, 0.5*inch, self.height - 1.25*inch)
            company_x = 1.7*inch
        else:
            company_x = 0.5*inch

        # Company Name & Address
        self.c.setFillColor(self.light_text_color)
        self.c.setFont(self.font_name_bold, 22)
        self.c.drawString(company_x, self.height - 0.6*inch, self.settings.company_name.upper())

        self.c.setFont(self.font_name, 9)
        company_address = self.settings.address.split('\n')
        y_pos = self.height - 0.8*inch
        for line in company_address:
            self.c.drawString(company_x, y_pos, line)
            y_pos -= 0.15*inch
        self.c.drawString(company_x, y_pos, f"GSTIN: {self.settings.gstin}")

        # Invoice Title and Details
        self.c.setFont(self.font_name_bold, 28)
        self.c.setFillColor(self.light_text_color)
        self.c.drawRightString(self.width - 0.5*inch, self.height - 0.7*inch, "INVOICE")

        self.c.setFont(self.font_name, 10)
        self.c.setFillColor(self.subtle_gray)
        self.c.drawRightString(self.width - 0.5*inch, self.height - 1.0*inch, f"Invoice #: {invoice_data['invoice_number']}")
        self.c.drawRightString(self.width - 0.5*inch, self.height - 1.15*inch, f"Date: {invoice_data['date']}")
        if invoice_data.get('vehicle_number'):
            self.c.drawRightString(self.width - 0.5*inch, self.height - 1.3*inch, f"Vehicle: {invoice_data['vehicle_number']}")

        # Payment Status
        status = invoice_data.get('payment_status', 'Pending').upper()
        status_color = self.get_status_color(status)
        self.c.setFont(self.font_name_bold, 12)
        self.c.setFillColor(status_color)
        self.c.drawRightString(self.width - 0.5*inch, self.height - 0.4*inch, status)


        self.c.restoreState()

    def draw_customer_info(self, invoice_data):
        self.c.saveState()
        y_pos = self.height - 2.0*inch

        self.c.setFont(self.font_name_bold, 11)
        self.c.setFillColor(self.secondary_color)
        self.c.drawString(0.5*inch, y_pos, "BILL TO")

        p_style = ParagraphStyle(name='Normal', fontName=self.font_name, fontSize=10, textColor=self.text_color, leading=14)

        customer_details = [
            f"<b>{invoice_data['customer']['name']}</b>",
            invoice_data['customer']['address'].replace('\n', '<br/>'),
            f"GSTIN: {invoice_data['customer']['gstin']}",
            f"State Code: {invoice_data['customer']['state_code']}"
        ]
        customer_text = Paragraph("<br/>".join(customer_details), p_style)

        customer_text.wrapOn(self.c, 4*inch, 2*inch)
        customer_text.drawOn(self.c, 0.5*inch, y_pos - 0.2*inch - customer_text.height)

        self.c.restoreState()

    def get_status_color(self, status):
        if status == 'PAID':
            return colors.HexColor('#4CAF50') # Green
        elif status == 'PENDING':
            return colors.HexColor('#FFC107') # Amber
        elif status == 'OVERDUE':
            return colors.HexColor('#F44336') # Red
        else:
            return self.text_color

    def draw_items_table(self, invoice_data):
        header_style = ParagraphStyle(name='Header', fontName=self.font_name_bold, fontSize=9, textColor=self.light_text_color, alignment=TA_CENTER)

        col_widths = [0.4*inch, 3.1*inch, 1.2*inch, 0.8*inch, 1.4*inch]
        data = [[Paragraph(h, header_style) for h in ["#", "ITEM", "PRICE", "QTY", "TOTAL"]]]

        subtotal = 0
        normal_style = ParagraphStyle(name='Normal', fontName=self.font_name, fontSize=9, textColor=self.text_color)
        right_align_style = ParagraphStyle(name='NormalRight', parent=normal_style, alignment=TA_RIGHT)
        center_align_style = ParagraphStyle(name='NormalCenter', parent=normal_style, alignment=TA_CENTER)

        for i, item in enumerate(invoice_data['items']):
            price = self.safe_float(item['price_per_unit'])
            quantity = self.safe_int(item['quantity'])
            total_item = price * quantity
            subtotal += total_item
            data.append([
                Paragraph(str(i + 1), center_align_style),
                Paragraph(item['product_name'], normal_style),
                Paragraph(f"₹{price:,.2f}", right_align_style),
                Paragraph(str(quantity), center_align_style),
                Paragraph(f"₹{total_item:,.2f}", right_align_style)
            ])

        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.secondary_color),
            ('GRID', (0, 0), (-1, -1), 0.5, self.subtle_gray),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
        ]))

        table_height = table.wrapOn(self.c, self.width - inch, self.height)[1]
        table_y_start = self.height - 3.2*inch - table_height
        table.drawOn(self.c, 0.5*inch, table_y_start)

        return table_y_start, subtotal

    def draw_summary(self, invoice_data, subtotal, y_pos):
        tax_info = self.get_tax_info(subtotal, invoice_data['customer']['state_code'])
        total = subtotal + tax_info['total_tax']

        summary_style = ParagraphStyle(name='Summary', fontName=self.font_name, fontSize=10, textColor=self.text_color, alignment=TA_RIGHT)
        summary_style_bold = ParagraphStyle(name='SummaryBold', parent=summary_style, fontName=self.font_name_bold)

        summary_data = [
            [Paragraph("Subtotal", summary_style), Paragraph(f"₹{subtotal:,.2f}", summary_style)],
        ]
        if tax_info['tax_type'] == 'IGST':
            summary_data.append([Paragraph("IGST (18%)", summary_style), Paragraph(f"₹{tax_info['igst']:,.2f}", summary_style)])
        else:
            summary_data.append([Paragraph("CGST (9%)", summary_style), Paragraph(f"₹{tax_info['cgst']:,.2f}", summary_style)])
            summary_data.append([Paragraph("SGST (9%)", summary_style), Paragraph(f"₹{tax_info['sgst']:,.2f}", summary_style)])

        summary_data.append([Paragraph("Total", summary_style_bold), Paragraph(f"₹{total:,.2f}", summary_style_bold)])

        summary_table = Table(summary_data, colWidths=[1.5*inch, 1.5*inch], hAlign='RIGHT')
        summary_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LINEABOVE', (0, -1), (-1, -1), 1, self.text_color),
        ]))

        summary_table.wrapOn(self.c, 3*inch, 2*inch)
        summary_table.drawOn(self.c, self.width - 3.6*inch, y_pos - summary_table._height)

    def draw_footer(self):
        self.c.saveState()
        y_pos = 1.5*inch

        # Terms and Conditions
        self.c.setFont(self.font_name_bold, 9)
        self.c.setFillColor(self.text_color)
        self.c.drawString(0.5*inch, y_pos, "Terms & Conditions")

        terms_style = ParagraphStyle(name='Terms', fontName=self.font_name, fontSize=8, textColor=self.text_color, leading=12)
        terms = Paragraph("1. Payment is due within 15 days. <br/>2. All goods remain the property of the seller until paid for in full.", terms_style)
        terms.wrapOn(self.c, 4*inch, 1*inch)
        terms.drawOn(self.c, 0.5*inch, y_pos - 0.1*inch - terms.height)

        # Authorized Signatory
        self.c.line(self.width - 3.5*inch, y_pos, self.width - 0.5*inch, y_pos)
        self.c.setFont(self.font_name, 9)
        self.c.drawRightString(self.width - 0.5*inch, y_pos - 0.15*inch, "Authorized Signatory")
        self.c.setFont(self.font_name_bold, 10)
        self.c.drawRightString(self.width - 0.5*inch, y_pos + 0.1*inch, f"For {self.settings.company_name}")

        # Footer line and message
        self.c.setStrokeColor(self.primary_color)
        self.c.setLineWidth(2)
        self.c.line(0, 0.5*inch, self.width, 0.5*inch)

        footer_style = ParagraphStyle(name='Footer', fontName=self.font_name, fontSize=8, textColor=self.secondary_color, alignment=TA_CENTER)
        footer_text = Paragraph("Thank you for your business!", footer_style)
        footer_text.wrapOn(self.c, self.width-inch, 0.5*inch)
        footer_text.drawOn(self.c, 0.5*inch, 0.25*inch)

        self.c.restoreState()
