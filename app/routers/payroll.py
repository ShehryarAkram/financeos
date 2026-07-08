from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
from datetime import date
import uuid

from app.core.database import get_db
from app.models.employee import Employee, Payslip, EmployeeStatus
from app.models.account import Account
from app.models.journal import EntrySource
from app.services.payroll_service import calculate_payslip, calculate_income_tax_monthly
from app.services.journal_service import JournalService

router = APIRouter()


class EmployeeCreate(BaseModel):
    org_id: str
    name: str
    cnic: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    basic_salary: float
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    join_date: Optional[str] = None


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    basic_salary: Optional[float] = None
    phone: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    status: Optional[str] = None


def emp_to_dict(e: Employee) -> dict:
    return {
        "id": str(e.id),
        "name": e.name,
        "cnic": e.cnic,
        "phone": e.phone,
        "department": e.department,
        "designation": e.designation,
        "basic_salary": float(e.basic_salary),
        "join_date": str(e.join_date),
        "bank_name": e.bank_name,
        "bank_account": e.bank_account,
        "status": e.status.value,
        "eobi_employee": float(e.eobi_employee),
        "eobi_employer": float(e.eobi_employer),
    }


@router.get("/list")
def list_employees(org_id: str, db: Session = Depends(get_db)):
    employees = db.query(Employee).filter(
        Employee.org_id == uuid.UUID(org_id),
        Employee.status == EmployeeStatus.active,
    ).order_by(Employee.name).all()
    return [emp_to_dict(e) for e in employees]


@router.post("/create")
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    emp = Employee(
        org_id=uuid.UUID(payload.org_id),
        name=payload.name,
        cnic=payload.cnic,
        phone=payload.phone,
        department=payload.department,
        designation=payload.designation,
        basic_salary=Decimal(str(payload.basic_salary)),
        bank_name=payload.bank_name,
        bank_account=payload.bank_account,
        join_date=date.fromisoformat(payload.join_date) if payload.join_date else date.today(),
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp_to_dict(emp)


@router.patch("/{emp_id}")
def update_employee(emp_id: str, payload: EmployeeUpdate, db: Session = Depends(get_db)):
    emp = db.get(Employee, uuid.UUID(emp_id))
    if not emp:
        raise HTTPException(404, "Employee not found")
    data = payload.model_dump(exclude_unset=True)
    if "status" in data:
        data["status"] = EmployeeStatus(data["status"])
    if "basic_salary" in data:
        data["basic_salary"] = Decimal(str(data["basic_salary"]))
    for k, v in data.items():
        setattr(emp, k, v)
    db.commit()
    db.refresh(emp)
    return emp_to_dict(emp)


@router.post("/calculate")
def calculate_salary(payload: dict):
    """Preview payslip calculation before processing"""
    basic = Decimal(str(payload.get("basic_salary", 0)))
    allowances = Decimal(str(payload.get("allowances", 0)))
    return calculate_payslip(basic, allowances)


@router.post("/process-month")
def process_monthly_payroll(payload: dict, db: Session = Depends(get_db)):
    """
    Process payroll for all active employees for a given month.
    Creates payslips + journal entries.
    """
    org_id = uuid.UUID(payload["org_id"])
    year = payload["year"]
    month = payload["month"]

    employees = db.query(Employee).filter(
        Employee.org_id == org_id,
        Employee.status == EmployeeStatus.active,
    ).all()

    if not employees:
        raise HTTPException(400, "No active employees found")

    # Check if already processed
    existing = db.query(Payslip).filter(
        Payslip.org_id == org_id,
        Payslip.year == year,
        Payslip.month == month,
    ).first()
    if existing:
        raise HTTPException(400, f"Payroll for {year}-{month:02d} already processed")

    # Get salary expense and payable accounts
    salary_exp = db.query(Account).filter(
        Account.org_id == org_id, Account.code == "5103"
    ).first()
    salary_pay = db.query(Account).filter(
        Account.org_id == org_id, Account.code == "2004"
    ).first()

    payslips_created = []
    total_gross = Decimal("0")
    total_net = Decimal("0")

    for emp in employees:
        calc = calculate_payslip(
            basic_salary=emp.basic_salary,
            eobi_employee=emp.eobi_employee,
        )
        gross = Decimal(str(calc["gross_salary"]))
        net = Decimal(str(calc["net_salary"]))
        total_gross += gross
        total_net += net

        payslip = Payslip(
            org_id=org_id,
            employee_id=emp.id,
            year=year,
            month=month,
            basic_salary=emp.basic_salary,
            allowances=Decimal("0"),
            gross_salary=gross,
            eobi_deduction=Decimal(str(calc["eobi_deduction"])),
            income_tax=Decimal(str(calc["income_tax"])),
            total_deductions=Decimal(str(calc["total_deductions"])),
            net_salary=net,
        )
        db.add(payslip)
        payslips_created.append({
            "employee": emp.name,
            "gross": float(gross),
            "deductions": float(Decimal(str(calc["total_deductions"]))),
            "net": float(net),
        })

    # Create journal entry for total payroll
    # DR Salary Expense / CR Salaries Payable
    if salary_exp and salary_pay:
        JournalService.create_entry(
            db=db,
            org_id=org_id,
            entry_date=date(year, month, 1),
            narration=f"Payroll {year}-{month:02d} — {len(employees)} employees",
            source=EntrySource.manual,
            lines=[
                {"account_id": salary_exp.id, "debit": total_gross, "credit": 0},
                {"account_id": salary_pay.id, "debit": 0, "credit": total_gross},
            ],
        )

    db.commit()

    return {
        "status": "processed",
        "period": f"{year}-{month:02d}",
        "employees": len(employees),
        "total_gross": float(total_gross),
        "total_net": float(total_net),
        "payslips": payslips_created,
    }


@router.get("/payslips/{org_id}")
def list_payslips(org_id: str, year: int = None, month: int = None, db: Session = Depends(get_db)):
    query = db.query(Payslip).filter(Payslip.org_id == uuid.UUID(org_id))
    if year:
        query = query.filter(Payslip.year == year)
    if month:
        query = query.filter(Payslip.month == month)
    payslips = query.order_by(Payslip.year.desc(), Payslip.month.desc()).all()

    result = []
    for p in payslips:
        emp = db.get(Employee, p.employee_id)
        result.append({
            "id": str(p.id),
            "employee": emp.name if emp else "Unknown",
            "period": f"{p.year}-{str(p.month).zfill(2)}",
            "gross": float(p.gross_salary),
            "deductions": float(p.total_deductions),
            "net": float(p.net_salary),
            "is_paid": p.is_paid,
        })
    return result


@router.get("/payslip/{payslip_id}/pdf")
def payslip_pdf(payslip_id: str, db: Session = Depends(get_db)):
    """Generate payslip PDF"""
    from reportlab.lib.pagesizes import A5
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib.enums import TA_CENTER
    import io

    ps = db.get(Payslip, uuid.UUID(payslip_id))
    if not ps:
        raise HTTPException(404, "Payslip not found")

    emp = db.get(Employee, ps.employee_id)
    from app.models.organization import Organization
    org = db.get(Organization, ps.org_id)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A5, rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    green = colors.HexColor("#16a34a")
    elements = []

    # Header
    elements.append(Paragraph(f"<font size=14 color='#16a34a'><b>{org.name if org else 'Company'}</b></font>", styles["Normal"]))
    elements.append(Paragraph("<font size=10>SALARY SLIP</font>", ParagraphStyle("c", alignment=TA_CENTER, fontSize=10)))
    elements.append(Spacer(1, 5*mm))

    # Employee info
    MONTHS = ["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    info = [
        ["Employee:", emp.name if emp else "—", "Period:", f"{MONTHS[ps.month]} {ps.year}"],
        ["Designation:", emp.designation or "—", "Department:", emp.department or "—"],
        ["CNIC:", emp.cnic or "—", "Join Date:", str(emp.join_date) if emp else "—"],
    ]
    info_table = Table(info, colWidths=[25*mm, 45*mm, 25*mm, 35*mm])
    info_table.setStyle(TableStyle([
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("TEXTCOLOR", (0,0), (0,-1), colors.grey),
        ("TEXTCOLOR", (2,0), (2,-1), colors.grey),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 5*mm))

    # Earnings / Deductions
    earn_data = [
        ["EARNINGS", "Amount", "DEDUCTIONS", "Amount"],
        ["Basic Salary", f"Rs. {ps.basic_salary:,.0f}", "EOBI", f"Rs. {ps.eobi_deduction:,.0f}"],
        ["Allowances", f"Rs. {ps.allowances:,.0f}", "Income Tax", f"Rs. {ps.income_tax:,.0f}"],
        ["", "", "Other", f"Rs. {ps.other_deductions:,.0f}"],
        ["Gross Salary", f"Rs. {ps.gross_salary:,.0f}", "Total Deductions", f"Rs. {ps.total_deductions:,.0f}"],
    ]
    earn_table = Table(earn_data, colWidths=[35*mm, 30*mm, 35*mm, 30*mm])
    earn_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (1,0), green),
        ("BACKGROUND", (2,0), (3,0), colors.HexColor("#dc2626")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("GRID", (0,0), (-1,-1), 0.3, colors.lightgrey),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 4),
    ]))
    elements.append(earn_table)
    elements.append(Spacer(1, 5*mm))

    # Net salary box
    net_data = [["NET SALARY PAYABLE", f"Rs. {ps.net_salary:,.0f}"]]
    net_table = Table(net_data, colWidths=[100*mm, 30*mm])
    net_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), green),
        ("TEXTCOLOR", (0,0), (-1,-1), colors.white),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("ALIGN", (1,0), (1,0), "RIGHT"),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    elements.append(net_table)
    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph(
        "<font size=7 color='grey'>Generated by FinanceOS — Pakistan ka apna hisaab kitab</font>",
        ParagraphStyle("f", alignment=TA_CENTER)
    ))

    doc.build(elements)
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=payslip-{payslip_id[:8]}.pdf"}
    )
