# model.py
import re
from dataclasses import dataclass
from typing import List

@dataclass
class LineItem:
    description: str
    quantity: int
    unit_price: float
    total: float

@dataclass
class Invoice:
    invoice_no: str
    date: str
    vendor: str
    items: List[LineItem]
    subtotal: float
    tax: float
    total: float

def parse_invoice_text(raw_text: str) -> Invoice:
    """
    Rudimentary regex-based parser for demo invoices.
    Pulls out invoice number, date, vendor name and total amount.
    """
    # Invoice number
    m = re.search(r"Invoice\s*No[:\s]+(\S+)", raw_text, re.IGNORECASE)
    invoice_no = m.group(1) if m else ""

    # Date (common formats)
    m = re.search(r"Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                  raw_text, re.IGNORECASE)
    date = m.group(1) if m else ""

    # Total due
    m = re.search(r"Total\s+Amount\s+Due[:\s]+\$?([\d,\.]+)",
                  raw_text, re.IGNORECASE)
    total = float(m.group(1).replace(",", "")) if m else 0.0

    # Vendor = first non-blank line
    vendor = next((ln for ln in raw_text.splitlines() if ln.strip()), "")

    return Invoice(
        invoice_no=invoice_no,
        date=date,
        vendor=vendor,
        items=[],     # extend here if you want to parse line-items
        subtotal=0.0, # ditto
        tax=0.0,      # ditto
        total=total
    )
