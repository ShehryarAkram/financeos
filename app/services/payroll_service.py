"""
Payroll Service — Pakistan payroll calculations

Income tax slabs (FY 2024-25):
  Up to Rs. 600,000/year      → 0%
  Rs. 600,001 – 1,200,000    → 5% of amount exceeding 600,000
  Rs. 1,200,001 – 2,400,000  → Rs. 30,000 + 15% exceeding 1,200,000
  Rs. 2,400,001 – 3,600,000  → Rs. 210,000 + 25% exceeding 2,400,000
  Rs. 3,600,001 – 6,000,000  → Rs. 510,000 + 30% exceeding 3,600,000
  Above Rs. 6,000,000        → Rs. 1,230,000 + 35% exceeding 6,000,000
"""

from decimal import Decimal


def calculate_income_tax_monthly(monthly_salary: Decimal) -> Decimal:
    """Calculate monthly income tax deduction based on annual salary"""
    annual = monthly_salary * 12

    if annual <= 600_000:
        annual_tax = Decimal("0")
    elif annual <= 1_200_000:
        annual_tax = (annual - 600_000) * Decimal("0.05")
    elif annual <= 2_400_000:
        annual_tax = Decimal("30000") + (annual - 1_200_000) * Decimal("0.15")
    elif annual <= 3_600_000:
        annual_tax = Decimal("210000") + (annual - 2_400_000) * Decimal("0.25")
    elif annual <= 6_000_000:
        annual_tax = Decimal("510000") + (annual - 3_600_000) * Decimal("0.30")
    else:
        annual_tax = Decimal("1230000") + (annual - 6_000_000) * Decimal("0.35")

    return (annual_tax / 12).quantize(Decimal("0.01"))


def calculate_payslip(
    basic_salary: Decimal,
    allowances: Decimal = Decimal("0"),
    eobi_employee: Decimal = Decimal("370"),
    other_deductions: Decimal = Decimal("0"),
) -> dict:
    gross = basic_salary + allowances
    income_tax = calculate_income_tax_monthly(gross)
    total_deductions = eobi_employee + income_tax + other_deductions
    net_salary = gross - total_deductions

    return {
        "basic_salary": float(basic_salary),
        "allowances": float(allowances),
        "gross_salary": float(gross),
        "eobi_deduction": float(eobi_employee),
        "income_tax": float(income_tax),
        "other_deductions": float(other_deductions),
        "total_deductions": float(total_deductions),
        "net_salary": float(net_salary),
    }
