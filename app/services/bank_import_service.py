"""
Bank CSV Import Service

Supports Pakistani bank statement formats:
- HBL: Date, Description, Debit, Credit, Balance
- MCB: Date, Narration, Withdrawal, Deposit, Balance
- UBL: Date, Description, Debit, Credit, Balance
- Generic: auto-detect columns

Auto-categorizes transactions using keywords.
"""

import pandas as pd
import io
from decimal import Decimal
from datetime import datetime


CATEGORY_KEYWORDS = {
    "salary":     ["salary","payroll","wages","tنخواہ"],
    "utilities":  ["lesco","sngpl","sui gas","wasa","ptcl","electricity","gas bill"],
    "mobile":     ["jazz","telenor","ufone","zong","mobilink","sms","topup"],
    "rent":       ["rent","kiraya","lease"],
    "transport":  ["fuel","petrol","uber","careem","toll","parking"],
    "tax":        ["fbr","tax","withholding","wht","gst"],
    "bank_charge":["charges","fee","commission","markup","profit"],
    "transfer":   ["transfer","trf","ibft","raast","easypaisa","jazzcash"],
}


def detect_bank(df: pd.DataFrame) -> str:
    cols = [c.lower().strip() for c in df.columns]
    if "withdrawal" in cols or "deposit" in cols:
        return "mcb"
    if "debit" in cols and "credit" in cols:
        return "hbl_ubl"
    return "generic"


def parse_amount(val) -> Decimal:
    if pd.isna(val) or val == "" or val == "-":
        return Decimal("0")
    clean = str(val).replace(",", "").replace(" ", "").strip()
    try:
        return Decimal(clean)
    except Exception:
        return Decimal("0")


def guess_category(description: str) -> str:
    desc_lower = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            return category
    return "miscellaneous"


def parse_bank_csv(file_content: bytes, filename: str = "") -> list[dict]:
    """
    Parse bank CSV and return list of normalized transactions.
    Each transaction: {date, description, debit, credit, balance, category, raw}
    """
    try:
        # Try reading with different encodings
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                df = pd.read_csv(io.BytesIO(file_content), encoding=encoding, skiprows=0)
                break
            except Exception:
                continue

        # Clean column names
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        # Drop completely empty rows
        df = df.dropna(how="all")

        bank = detect_bank(df)
        transactions = []

        for _, row in df.iterrows():
            try:
                # Date parsing
                date_val = None
                for date_col in ["date", "transaction_date", "value_date", "posting_date"]:
                    if date_col in row.index and not pd.isna(row.get(date_col)):
                        try:
                            date_val = pd.to_datetime(str(row[date_col]), dayfirst=True).date()
                            break
                        except Exception:
                            continue

                if not date_val:
                    continue

                # Description
                desc = ""
                for desc_col in ["description", "narration", "particulars", "details", "remarks"]:
                    if desc_col in row.index and not pd.isna(row.get(desc_col)):
                        desc = str(row[desc_col]).strip()
                        break

                if not desc or desc.lower() in ["nan", ""]:
                    continue

                # Amounts
                if bank == "mcb":
                    debit = parse_amount(row.get("withdrawal", 0))
                    credit = parse_amount(row.get("deposit", 0))
                else:
                    debit = parse_amount(row.get("debit", 0))
                    credit = parse_amount(row.get("credit", 0))

                balance = parse_amount(row.get("balance", row.get("running_balance", 0)))

                if debit == 0 and credit == 0:
                    continue

                transactions.append({
                    "date": str(date_val),
                    "description": desc,
                    "debit": float(debit),
                    "credit": float(credit),
                    "balance": float(balance),
                    "category": guess_category(desc),
                    "type": "debit" if debit > 0 else "credit",
                    "amount": float(debit if debit > 0 else credit),
                })

            except Exception:
                continue

        return transactions

    except Exception as e:
        raise ValueError(f"Could not parse CSV: {str(e)}")
