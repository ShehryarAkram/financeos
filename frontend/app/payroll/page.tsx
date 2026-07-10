"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const MONTHS = ["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

interface Employee {
  id: string; name: string; designation: string | null;
  department: string | null; basic_salary: number;
  cnic: string | null; phone: string | null;
  bank_name: string | null; bank_account: string | null;
}

interface Payslip {
  id: string; employee: string; period: string;
  gross: number; deductions: number; net: number; is_paid: boolean;
}

export default function PayrollPage() {
  const [tab, setTab] = useState<"employees"|"process"|"payslips">("employees");
  const [orgId, setOrgId] = useState("");
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [payslips, setPayslips] = useState<Payslip[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  // Employee form
  const [empName, setEmpName] = useState("");
  const [empDesig, setEmpDesig] = useState("");
  const [empDept, setEmpDept] = useState("");
  const [empSalary, setEmpSalary] = useState("");
  const [empCnic, setEmpCnic] = useState("");
  const [empPhone, setEmpPhone] = useState("");
  const [empBank, setEmpBank] = useState("");
  const [empAcc, setEmpAcc] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  // Process payroll
  const [procYear, setProcYear] = useState(new Date().getFullYear());
  const [procMonth, setProcMonth] = useState(new Date().getMonth() + 1);
  const [processing, setProcessing] = useState(false);
  const [procResult, setProcResult] = useState<any>(null);

  // Salary preview
  const [preview, setPreview] = useState<any>(null);

  const loadEmployees = (org: string) => {
    fetch(`${API}/api/payroll/list?org_id=${org}`)
      .then(r => r.json()).then(d => setEmployees(Array.isArray(d) ? d : []))
      .catch(console.error).finally(() => setLoading(false));
  };

  const loadPayslips = (org: string) => {
    fetch(`${API}/api/payroll/payslips/${org}`)
      .then(r => r.json()).then(d => setPayslips(Array.isArray(d) ? d : []))
      .catch(console.error);
  };

  useEffect(() => {
    const org = localStorage.getItem("org_id") || "";
    setOrgId(org);
    if (org) { loadEmployees(org); loadPayslips(org); }
    else setLoading(false);
  }, []);

  const previewSalary = async (salary: string) => {
    if (!salary || parseFloat(salary) <= 0) { setPreview(null); return; }
    const res = await fetch(`${API}/api/payroll/calculate`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ basic_salary: parseFloat(salary), allowances: 0 }),
    });
    setPreview(await res.json());
  };

  const handleAddEmployee = async () => {
    if (!empName || !empSalary) { setError("Name and salary required"); return; }
    setError(""); setSaving(true);
    try {
      const res = await fetch(`${API}/api/payroll/create`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          org_id: orgId, name: empName, designation: empDesig || null,
          department: empDept || null, basic_salary: parseFloat(empSalary),
          cnic: empCnic || null, phone: empPhone || null,
          bank_name: empBank || null, bank_account: empAcc || null,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed");
      setShowForm(false);
      setEmpName(""); setEmpDesig(""); setEmpDept(""); setEmpSalary("");
      setEmpCnic(""); setEmpPhone(""); setEmpBank(""); setEmpAcc("");
      setPreview(null);
      loadEmployees(orgId);
    } catch (e: any) { setError(e.message); }
    finally { setSaving(false); }
  };

  const handleTerminate = async (id: string) => {
    if (!confirm("Terminate this employee?")) return;
    await fetch(`${API}/api/payroll/${id}`, {
      method: "PATCH", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "terminated" }),
    });
    loadEmployees(orgId);
  };

  const handleProcess = async () => {
    setProcessing(true); setProcResult(null);
    try {
      const res = await fetch(`${API}/api/payroll/process-month`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ org_id: orgId, year: procYear, month: procMonth }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed");
      setProcResult(data);
      loadPayslips(orgId);
    } catch (e: any) { setProcResult({ error: (e as any).message }); }
    finally { setProcessing(false); }
  };

  const totalPayroll = employees.reduce((s, e) => s + e.basic_salary, 0);

  if (loading) return (
    <div className="p-8 flex items-center justify-center h-96">
      <div className="text-gray-400 animate-pulse">Loading payroll...</div>
    </div>
  );

  return (
    <div className="p-4 lg:p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Payroll</h1>
        <p className="text-sm text-gray-500 mt-1">Employee management, salary processing, payslips</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <div className="text-2xl font-bold text-blue-600">{employees.length}</div>
          <div className="text-xs text-gray-500 mt-1">Active Employees</div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <div className="text-xl font-bold text-green-600">Rs. {totalPayroll.toLocaleString()}</div>
          <div className="text-xs text-gray-500 mt-1">Monthly Payroll</div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <div className="text-2xl font-bold text-orange-500">{payslips.length}</div>
          <div className="text-xs text-gray-500 mt-1">Payslips Generated</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1 mb-6">
        {[
          { id: "employees", label: "👥 Employees" },
          { id: "process",   label: "⚙️ Process Payroll" },
          { id: "payslips",  label: "📄 Payslips" },
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id as any)}
            className={`flex-1 py-2 rounded-md text-sm font-medium transition-colors ${
              tab === t.id ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Employees Tab */}
      {tab === "employees" && (
        <div>
          <div className="flex justify-end mb-4">
            <button onClick={() => setShowForm(!showForm)}
              className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
              {showForm ? "Cancel" : "+ Add Employee"}
            </button>
          </div>

          {showForm && (
            <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4">
              <div className="text-sm font-semibold mb-3">New Employee</div>
              {error && <div className="bg-red-50 text-red-600 text-sm px-3 py-2 rounded-lg mb-3">{error}</div>}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">Full Name *</label>
                  <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                    placeholder="Ali Hassan" value={empName} onChange={e => setEmpName(e.target.value)} />
                </div>
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">Basic Salary (Rs.) *</label>
                  <input type="number" className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                    placeholder="50000" value={empSalary}
                    onChange={e => { setEmpSalary(e.target.value); previewSalary(e.target.value); }} />
                </div>
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">Designation</label>
                  <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                    placeholder="Sales Manager" value={empDesig} onChange={e => setEmpDesig(e.target.value)} />
                </div>
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">Department</label>
                  <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                    placeholder="Sales" value={empDept} onChange={e => setEmpDept(e.target.value)} />
                </div>
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">CNIC</label>
                  <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                    placeholder="42101-1234567-1" value={empCnic} onChange={e => setEmpCnic(e.target.value)} />
                </div>
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">Phone</label>
                  <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                    placeholder="03001234567" value={empPhone} onChange={e => setEmpPhone(e.target.value)} />
                </div>
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">Bank Name</label>
                  <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                    placeholder="HBL / MCB / UBL" value={empBank} onChange={e => setEmpBank(e.target.value)} />
                </div>
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">Account Number</label>
                  <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                    placeholder="0123456789" value={empAcc} onChange={e => setEmpAcc(e.target.value)} />
                </div>
              </div>

              {preview && (
                <div className="bg-green-50 rounded-lg p-3 mb-3 text-xs grid grid-cols-3 gap-2">
                  <div><span className="text-gray-500">Gross:</span> <span className="font-medium">Rs. {preview.gross_salary?.toLocaleString()}</span></div>
                  <div><span className="text-gray-500">Deductions:</span> <span className="font-medium text-red-500">Rs. {preview.total_deductions?.toLocaleString()}</span></div>
                  <div><span className="text-gray-500">Net:</span> <span className="font-medium text-green-700">Rs. {preview.net_salary?.toLocaleString()}</span></div>
                </div>
              )}

              <button onClick={handleAddEmployee} disabled={saving}
                className="bg-green-600 text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50">
                {saving ? "Saving..." : "Save Employee"}
              </button>
            </div>
          )}

          <div className="bg-white rounded-xl border border-gray-200 p-5">
            {employees.length === 0 ? (
              <div className="text-center py-12 text-gray-400 text-sm">No employees yet. Add your first employee.</div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="text-left py-3 text-gray-500 font-medium">Name</th>
                    <th className="text-left py-3 text-gray-500 font-medium hidden sm:table-cell">Designation</th>
                    <th className="text-left py-3 text-gray-500 font-medium hidden sm:table-cell">Department</th>
                    <th className="text-right py-3 text-gray-500 font-medium">Salary</th>
                    <th className="text-right py-3 text-gray-500 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {employees.map(e => (
                    <tr key={e.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-3 font-medium text-gray-800">{e.name}</td>
                      <td className="py-3 text-gray-500 hidden sm:table-cell">{e.designation || "—"}</td>
                      <td className="py-3 text-gray-500 hidden sm:table-cell">{e.department || "—"}</td>
                      <td className="py-3 text-right font-medium">Rs. {e.basic_salary.toLocaleString()}</td>
                      <td className="py-3 text-right">
                        <button onClick={() => handleTerminate(e.id)}
                          className="text-red-400 hover:text-red-600 text-xs">Terminate</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* Process Payroll Tab */}
      {tab === "process" && (
        <div className="max-w-lg">
          <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4">
            <div className="text-sm font-semibold mb-4">Process Monthly Payroll</div>
            <div className="flex gap-3 mb-4">
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Year</label>
                <input type="number" className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-24 focus:outline-none focus:ring-2 focus:ring-green-500"
                  value={procYear} onChange={e => setProcYear(parseInt(e.target.value))} />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Month</label>
                <select className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                  value={procMonth} onChange={e => setProcMonth(parseInt(e.target.value))}>
                  {MONTHS.slice(1).map((m, i) => <option key={i+1} value={i+1}>{m}</option>)}
                </select>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-3 mb-4 text-xs">
              <div className="font-medium text-gray-700 mb-2">Will process for {employees.length} active employee(s):</div>
              {employees.map(e => (
                <div key={e.id} className="flex justify-between py-1">
                  <span>{e.name}</span>
                  <span className="font-medium">Rs. {e.basic_salary.toLocaleString()}</span>
                </div>
              ))}
              <div className="flex justify-between pt-2 border-t border-gray-200 font-semibold mt-1">
                <span>Total Payroll</span>
                <span>Rs. {totalPayroll.toLocaleString()}</span>
              </div>
            </div>

            <button onClick={handleProcess} disabled={processing || employees.length === 0}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 rounded-lg disabled:opacity-50">
              {processing ? "Processing..." : `Process ${MONTHS[procMonth]} ${procYear} Payroll`}
            </button>
          </div>

          {procResult && (
            <div className={`rounded-xl border p-5 ${procResult.error ? "border-red-200 bg-red-50" : "border-green-200 bg-green-50"}`}>
              {procResult.error ? (
                <div className="text-red-700 text-sm font-medium">⚠️ {procResult.error}</div>
              ) : (
                <div>
                  <div className="text-green-800 font-semibold mb-3">✅ Payroll Processed — {procResult.period}</div>
                  <div className="space-y-1 text-sm">
                    {procResult.payslips?.map((p: any, i: number) => (
                      <div key={i} className="flex justify-between">
                        <span className="text-green-700">{p.employee}</span>
                        <span className="font-medium text-green-800">Net: Rs. {p.net.toLocaleString()}</span>
                      </div>
                    ))}
                    <div className="flex justify-between pt-2 border-t border-green-200 font-bold mt-1">
                      <span>Total Net Payable</span>
                      <span>Rs. {procResult.total_net?.toLocaleString()}</span>
                    </div>
                  </div>
                  <div className="mt-3 text-xs text-green-600">Journal entry created → Salary Expense debited</div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Payslips Tab */}
      {tab === "payslips" && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          {payslips.length === 0 ? (
            <div className="text-center py-12 text-gray-400 text-sm">
              No payslips yet. Process monthly payroll to generate them.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-3 text-gray-500 font-medium">Employee</th>
                  <th className="text-left py-3 text-gray-500 font-medium">Period</th>
                  <th className="text-right py-3 text-gray-500 font-medium hidden sm:table-cell">Gross</th>
                  <th className="text-right py-3 text-gray-500 font-medium hidden sm:table-cell">Deductions</th>
                  <th className="text-right py-3 text-gray-500 font-medium">Net</th>
                  <th className="text-right py-3 text-gray-500 font-medium">PDF</th>
                </tr>
              </thead>
              <tbody>
                {payslips.map(p => (
                  <tr key={p.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-3 font-medium text-gray-800">{p.employee}</td>
                    <td className="py-3 text-gray-500">{p.period}</td>
                    <td className="py-3 text-right hidden sm:table-cell">Rs. {p.gross.toLocaleString()}</td>
                    <td className="py-3 text-right text-red-500 hidden sm:table-cell">- Rs. {p.deductions.toLocaleString()}</td>
                    <td className="py-3 text-right font-semibold text-green-600">Rs. {p.net.toLocaleString()}</td>
                    <td className="py-3 text-right">
                      <a href={`${API}/api/payroll/payslip/${p.id}/pdf`} target="_blank"
                        className="text-green-600 hover:text-green-700 text-xs font-medium">PDF ↗</a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
