# src/utils/invoice_number_service.py
import os
import json

class InvoiceNumberService:
    def __init__(self, storage_file="invoice_counter.json"):
        self.storage_file = storage_file
        self.counter = self._load_counter()

    def _load_counter(self):
        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        else:
            return {"counter": 0}

    def _save_counter(self):
        with open(self.storage_file, 'w') as f:
            json.dump(self.counter, f)

    def get_next_invoice_number(self):
        self.counter['counter'] += 1
        self._save_counter()
        return f"INV-{self.counter['counter']:05d}"

    def peek_next_invoice_number(self):
        return f"INV-{self.counter['counter'] + 1:05d}"
