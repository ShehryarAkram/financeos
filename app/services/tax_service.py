"""
FBR Tax Service — Pakistan tax calculations

WHT Rates (as of 2024-25):
  Section 153A (goods):    4.5% filer / 9% non-filer
  Section 153B (services): 8%   filer / 16% non-filer
  Section 236G (advance):  0.1% filer / 0.2% non-filer

Sales Tax: Standard 17% GST
           Reduced rates: 5%, 10%, 12% for specific sectors
"""

from decimal import Decimal
from enum import Enum


class WHTSection(str, Enum):
    section_153a = "153a"   # goods
    section_153b = "153b"   # services
    section_236g = "236g"   # advance tax on sale to distributors
    none = "none"


class SalesTaxRate(str, Enum):
    exempt = "0"
    reduced_5 = "5"
    reduced_10 = "10"
    reduced_12 = "12"
    standard_17 = "17"


WHT_RATES = {
    WHTSection.section_153a: {"filer": Decimal("4.5"), "non_filer": Decimal("9.0")},
    WHTSection.section_153b: {"filer": Decimal("8.0"), "non_filer": Decimal("16.0")},
    WHTSection.section_236g: {"filer": Decimal("0.1"), "non_filer": Decimal("0.2")},
}


def calculate_wht(
    amount: Decimal,
    section: WHTSection,
    supplier_is_filer: bool = False,
) -> dict:
    """Calculate withholding tax on a payment"""
    if section == WHTSection.none:
        return {"wht_amount": Decimal("0"), "rate": Decimal("0"), "section": "none"}

    rates = WHT_RATES.get(section, WHT_RATES[WHTSection.section_153a])
    rate = rates["filer"] if supplier_is_filer else rates["non_filer"]
    wht_amount = (amount * rate / 100).quantize(Decimal("0.01"))
    net_payable = amount - wht_amount

    return {
        "gross_amount": float(amount),
        "wht_rate": float(rate),
        "wht_amount": float(wht_amount),
        "net_payable": float(net_payable),
        "section": section.value,
        "supplier_status": "filer" if supplier_is_filer else "non-filer",
    }


def calculate_sales_tax(amount: Decimal, rate_percent: float = 17.0) -> dict:
    """Calculate GST/sales tax on invoice"""
    rate = Decimal(str(rate_percent))
    tax_amount = (amount * rate / 100).quantize(Decimal("0.01"))
    total = amount + tax_amount

    return {
        "subtotal": float(amount),
        "tax_rate": float(rate),
        "tax_amount": float(tax_amount),
        "total_with_tax": float(total),
    }


def get_monthly_tax_summary(journal_entries: list) -> dict:
    """
    Summarize tax liabilities for monthly FBR return.
    Returns data needed for Sales Tax Return filing.
    """
    total_sales = Decimal("0")
    total_purchases = Decimal("0")
    tax_collected = Decimal("0")
    tax_paid = Decimal("0")
    wht_deducted = Decimal("0")

    for entry in journal_entries:
        for line in entry.get("lines", []):
            account_type = line.get("account_type", "")
            amount = Decimal(str(line.get("amount", 0)))

            if account_type == "income":
                total_sales += amount
            elif account_type == "expense":
                total_purchases += amount
            elif line.get("account_code") == "2002":  # Sales Tax Payable
                tax_collected += amount
            elif line.get("account_code") == "2003":  # WHT Payable
                wht_deducted += amount

    return {
        "total_sales": float(total_sales),
        "total_purchases": float(total_purchases),
        "output_tax": float(tax_collected),
        "input_tax": float(tax_paid),
        "wht_deducted": float(wht_deducted),
        "net_tax_payable": float(tax_collected - tax_paid),
    }
