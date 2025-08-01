# src/tabs/dashboard_tab.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QGridLayout
from PyQt6.QtCore import Qt
from sqlalchemy import func
from src.utils.theme import DARK_THEME
from src.utils.database import SessionLocal
from src.models import Invoice, CustomerCompany, InvoiceItem
from src.utils.plot_canvas import PlotCanvas

from src.tabs.base_tab import BaseTab

class DashboardTab(BaseTab):
    def __init__(self):
        super().__init__()
        self.db_session = self.get_db_session()
        self.init_ui()
        self.load_dashboard_data()
        self.apply_styles()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(28)

        # --- Date Filters ---
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(16)
        from PyQt6.QtWidgets import QDateEdit, QPushButton
        from PyQt6.QtCore import QDate
        filter_layout.addWidget(QLabel("From:"))
        self.from_date = QDateEdit(QDate.currentDate().addMonths(-1))
        self.from_date.setCalendarPopup(True)
        filter_layout.addWidget(self.from_date)
        filter_layout.addWidget(QLabel("To:"))
        self.to_date = QDateEdit(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        filter_layout.addWidget(self.to_date)
        self.filter_btn = QPushButton("Apply Filter")
        filter_layout.addWidget(self.filter_btn)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # --- Stats Cards ---
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(24)
        self.total_invoices_card = self.create_stat_card("Total Invoices", "0")
        self.total_companies_card = self.create_stat_card("Total Customers", "0")
        self.total_revenue_card = self.create_stat_card("Total Revenue", "\u20b90.00")
        stats_layout.addWidget(self.total_invoices_card)
        stats_layout.addWidget(self.total_companies_card)
        stats_layout.addWidget(self.total_revenue_card)
        main_layout.addLayout(stats_layout)

        # --- Graphs ---
        grid_layout = QGridLayout()
        grid_layout.setSpacing(28)
        self.top_products_chart = PlotCanvas(self, width=5, height=4)
        self.invoice_stats_chart = PlotCanvas(self, width=5, height=4)
        grid_layout.addWidget(self.top_products_chart, 0, 0)
        grid_layout.addWidget(self.invoice_stats_chart, 0, 1)
        main_layout.addLayout(grid_layout)
        main_layout.addStretch()

        # Connect filter
        self.filter_btn.clicked.connect(self.load_dashboard_data)

    def create_stat_card(self, title, value):
        card = QFrame()
        card.setObjectName("stat-card")
        layout = QVBoxLayout(card)
        title_label = QLabel(title)
        title_label.setObjectName("stat-title")
        value_label = QLabel(value)
        value_label.setObjectName("stat-value")
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        return card

    def create_graph_placeholder(self, title):
        graph_frame = QFrame()
        graph_frame.setObjectName("graph-card")
        layout = QVBoxLayout(graph_frame)
        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        return graph_frame

    def load_dashboard_data(self):
        from PyQt6.QtCore import QDate
        from sqlalchemy import and_
        # Date filter
        from_date = self.from_date.date().toPyDate() if hasattr(self, 'from_date') else None
        to_date = self.to_date.date().toPyDate() if hasattr(self, 'to_date') else None
        invoice_query = self.db_session.query(Invoice)
        if from_date and to_date:
            invoice_query = invoice_query.filter(and_(Invoice.date >= from_date, Invoice.date <= to_date))
        total_invoices = invoice_query.count()
        paid_invoices = invoice_query.filter(Invoice.payment_status == "Paid").count()
        unpaid_invoices = invoice_query.filter(Invoice.payment_status != "Paid").count()
        total_companies = self.db_session.query(CustomerCompany).count()
        total_revenue = invoice_query.with_entities(func.sum(Invoice.total_amount)).scalar() or 0

        # Top products in date range
        top_products = self.db_session.query(
            InvoiceItem.product_name,
            func.sum(InvoiceItem.quantity)
        ).join(Invoice, InvoiceItem.invoice_id == Invoice.id)
        if from_date and to_date:
            top_products = top_products.filter(and_(Invoice.date >= from_date, Invoice.date <= to_date))
        top_products = top_products.group_by(InvoiceItem.product_name).order_by(func.sum(InvoiceItem.quantity).desc()).limit(5).all()

        self.total_invoices_card.findChild(QLabel, "stat-value").setText(str(total_invoices))
        self.total_companies_card.findChild(QLabel, "stat-value").setText(str(total_companies))
        self.total_revenue_card.findChild(QLabel, "stat-value").setText(f"₹{total_revenue:,.2f}")

        # Update bar chart
        if top_products:
            product_names = [p[0] for p in top_products]
            quantities = [float(p[1]) for p in top_products]
            if any(q > 0 for q in quantities):
                self.top_products_chart.plot_bar(
                    product_names,
                    quantities,
                    "Top 5 Products by Quantity Sold",
                    "Product",
                    "Quantity Sold"
                )
            else:
                self.top_products_chart.axes.cla()
                self.top_products_chart.axes.text(0.5, 0.5, 'No sales data available',
                    horizontalalignment='center', verticalalignment='center')
                self.top_products_chart.draw()

        # Remove pie chart for now, show placeholder
        self.invoice_stats_chart.axes.cla()
        self.invoice_stats_chart.axes.text(0.5, 0.5, 'Invoice status chart is temporarily disabled',
            horizontalalignment='center', verticalalignment='center', fontsize=14, color=DARK_THEME['text_secondary'])
        self.invoice_stats_chart.draw()

    def apply_styles(self):
        self.setStyleSheet(f"""
            QWidget {{
                font-family: 'Segoe UI', 'Roboto', Arial, sans-serif;
                font-size: 15px;
            }}
            QFrame#stat-card {{
                background-color: {DARK_THEME['bg_surface']};
                border: 1px solid {DARK_THEME['border_main']};
                border-radius: 14px;
                padding: 24px 32px 20px 32px;
                min-width: 180px;
            }}
            QLabel#stat-title {{
                color: {DARK_THEME['text_secondary']};
                font-size: 15px;
                font-weight: 500;
                letter-spacing: 0.5px;
            }}
            QLabel#stat-value {{
                color: {DARK_THEME['text_primary']};
                font-size: 32px;
                font-weight: 700;
                padding-top: 8px;
                letter-spacing: 1px;
            }}
            QFrame#graph-card {{
                background-color: {DARK_THEME['bg_surface']};
                border: 1px solid {DARK_THEME['border_main']};
                border-radius: 14px;
                padding: 32px 24px 24px 24px;
                min-height: 260px;
            }}
            QFrame#graph-card QLabel {{
                color: {DARK_THEME['text_secondary']};
                font-size: 17px;
                font-weight: 600;
            }}
            QDateEdit, QPushButton {{
                background-color: {DARK_THEME['bg_input']};
                color: {DARK_THEME['text_primary']};
                border: 1px solid {DARK_THEME['border_main']};
                border-radius: 6px;
                padding: 8px 12px;
            }}
            QPushButton {{
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
        """)
