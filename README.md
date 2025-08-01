# BillTracker Pro

BillTracker Pro is a desktop application for managing SaaS billing, built with Python and PyQt6. It provides a user-friendly interface for handling customers, products, invoices, and more.

## Features

*   **Dashboard:** Get a quick overview of your billing system.
*   **Company and Product Management:** Easily add, edit, and manage your customer companies and their products.
*   **Invoice Generation:** Create professional invoices for your customers.
*   **Invoice History:** Keep track of all your past invoices.
*   **Inventory Control:** Manage your product stock levels.
*   **Audit Trail:** Log all significant actions for accountability.
*   **Data Portability:** Import and export your data in CSV format.
*   **Customizable Settings:** Configure the application to suit your needs.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/saas-billing-app.git
    cd saas-billing-app
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\\Scripts\\activate`
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

To run the application, execute the following command:

```bash
python -m src.main
```

This will launch the BillTracker Pro application window. The application uses a SQLite database (`billing_app.db`) which will be created automatically in the root directory.
