"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const CATEGORIES = [
  { value: "rent",         label: "🏠 Rent",          urdu: "کرایہ" },
  { value: "utilities",    label: "⚡ Utilities",      urdu: "بجلی/گیس/پانی" },
  { value: "salaries",     label: "👥 Salaries",       urdu: "تنخواہیں" },
  { value: "transport",    label: "🚗 Transport",      urdu: "ٹرانسپورٹ" },
  { value: "mobile",       label: "📱 Mobile/Internet",urdu: "موبائل/انٹرنیٹ" },
  { value: "office",       label: "🖥️ Office",         urdu: "دفتری اخراجات" },
  { value: "marketing",    label: "📢 Marketing",      urdu: "مارکیٹنگ" },
  { value: "maintenance",  label: "🔧 Maintenance",    urdu: "مرمت" },
  { value: "raw_material", label: "📦 Raw Material",   urdu: "خام مال" },
  { value: "miscellaneous",label: "📋 Miscellaneous",  urdu: "متفرق" },
];

const MONTHS = ["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

interface Expense {
  id: string; date: string; description: string;
  category: string; amount: number; vendor: string | null;
  paid_from: string; notes: string | null;
}

export default function ExpensesPage() {
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [orgId, setOrgId] = useState("");

  // Form state
  const [desc, setDesc] = useState("");
  const [category, setCategory] = useState("miscellaneous");
  const [amount, setAmount] = useState("");
  const [vendor, setVendor] = useState("");
  const [expDate, setExpDate] = useState(new Date().toISOString().split("T")[0]);
  const [paidFrom, setPaidFrom] = useState("cash");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  // Filters
  const [filterCat, setFilterCat] = useState("");
  const [filterMonth, setFilterMonth] = useState(new Date().getMonth() + 1);
  const [filterYear, setFilterYear] = useState(new Date().getFullYear());

  // Summary
  const [summary, setSummary] = useState<any>(null);

  const load = (org: string, cat?: string) => {
    const y = filterYear, m = filterMonth;
    const from = `${y}-${String(m).padStart(2,"0")}-01`;
    const lastDay = new Date(y, m, 0).getDate();
    const to = `${y}-${String(m).padStart(2,"0")}-${lastDay}`;
    let url = `${API}/api/expenses/list?org_id=${org}&from_date=${from}&to_date=${to}`;
    if (cat) url += `&category=${cat}`;

    fetch(url).then(r => r.json()).then(d => {
      setExpenses(d.expenses || []);
      setTotal(d.total || 0);
    }).catch(console.error).finally(() => setLoading(false));

    fetch(`${API}/api/expenses/summary/${org}?year=${y}&month=${m}`)
      .then(r => r.json()).then(setSummary).catch(console.error);
  };

  useEffect(() => {
    const org = localStorage.getItem("org_id") || "";
    setOrgId(org);
    if (org) load(org, filterCat || undefined);
    else setLoading(false);
  }, [filterMonth, filterYear, filterCat]);

  const handleCreate = async () => {
    if (!desc || !amount) { setError("Description and amount required"); return; }
    setError(""); setSaving(true);
    try {
      const res = await fetch(`${API}/api/expenses/create`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          org_id: orgId, description: desc, category,
          amount: parseFloat(amount), vendor: vendor || null,
          date: expDate, paid_from: paidFrom, notes: notes || null,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed");
      setShowForm(false);
      setDesc(""); setAmount(""); setVendor(""); setNotes("");
      load(orgId, filterCat || undefined);
    } catch (e: any) { setError(e.message); }
    finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this expense?")) return;
    await fetch(`${API}/api/expenses/${id}`, { method: "DELETE" });
    load(orgId, filterCat || undefined);
  };

  const catLabel = (val: string) => CATEGORIES.find(c => c.value === val)?.label || val;

  if (loading) return (
    <div className="p-8 flex items-center justify-center h-96">
      <div className="text-gray-400 animate-pulse">Loading expenses...</div>
    </div>
  );

  return (
    <div className="p-4 lg:p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Expenses</h1>
          <p className="text-sm text-gray-500 mt-1">Log and track all business expenses</p>
        </div>
        <button onClick={() => setShowForm(!showForm)}
          className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
          {showForm ? "Cancel" : "+ Add Expense"}
        </button>
      </div>

      {/* Add expense form */}
      {showForm && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
          <div className="text-sm font-semibold mb-3">New Expense</div>
          {error && <div className="bg-red-50 text-red-600 text-sm px-3 py-2 rounded-lg mb-3">{error}</div>}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-3">
            <div className="sm:col-span-2 lg:col-span-1">
              <label className="text-xs text-gray-500 mb-1 block">Description *</label>
              <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder="Bijli ka bill, kiraya, etc." value={desc} onChange={e => setDesc(e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Amount (Rs.) *</label>
              <input type="number" className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder="5000" value={amount} onChange={e => setAmount(e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Category</label>
              <select className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                value={category} onChange={e => setCategory(e.target.value)}>
                {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label} — {c.urdu}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Date</label>
              <input type="date" className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                value={expDate} onChange={e => setExpDate(e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Paid From</label>
              <select className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                value={paidFrom} onChange={e => setPaidFrom(e.target.value)}>
                <option value="cash">Cash in Hand</option>
                <option value="bank">Bank Account</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Vendor (optional)</label>
              <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder="LESCO, Punjab Gas, etc." value={vendor} onChange={e => setVendor(e.target.value)} />
            </div>
          </div>
          <div className="mb-3">
            <label className="text-xs text-gray-500 mb-1 block">Notes (optional)</label>
            <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="Any additional notes..." value={notes} onChange={e => setNotes(e.target.value)} />
          </div>
          <div className="flex gap-2 items-center">
            <button onClick={handleCreate} disabled={saving}
              className="bg-green-600 text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50">
              {saving ? "Saving..." : "Save Expense"}
            </button>
            <span className="text-xs text-gray-400">Journal entry created automatically</span>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-4 items-center">
        <select className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          value={filterMonth} onChange={e => setFilterMonth(parseInt(e.target.value))}>
          {MONTHS.slice(1).map((m, i) => <option key={i+1} value={i+1}>{m}</option>)}
        </select>
        <select className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          value={filterYear} onChange={e => setFilterYear(parseInt(e.target.value))}>
          {[2025, 2026, 2027].map(y => <option key={y} value={y}>{y}</option>)}
        </select>
        <select className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          value={filterCat} onChange={e => setFilterCat(e.target.value)}>
          <option value="">All categories</option>
          {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
        </select>
        <span className="text-sm text-gray-500 ml-auto font-medium">
          Total: <span className="text-red-600 font-bold">Rs. {total.toLocaleString()}</span>
        </span>
      </div>

      {/* Category summary pills */}
      {summary?.breakdown?.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {summary.breakdown.map((b: any) => (
            <button key={b.category}
              onClick={() => setFilterCat(filterCat === b.category ? "" : b.category)}
              className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                filterCat === b.category
                  ? "bg-red-100 border-red-300 text-red-700"
                  : "bg-white border-gray-200 text-gray-600 hover:border-red-300"
              }`}>
              {catLabel(b.category)} — Rs. {b.total.toLocaleString()}
            </button>
          ))}
        </div>
      )}

      {/* Expense list */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        {expenses.length === 0 ? (
          <div className="text-center py-12 text-gray-400 text-sm">
            No expenses for this period. Click "+ Add Expense" to log one.
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left py-3 text-gray-500 font-medium">Description</th>
                <th className="text-left py-3 text-gray-500 font-medium hidden sm:table-cell">Category</th>
                <th className="text-left py-3 text-gray-500 font-medium hidden sm:table-cell">Date</th>
                <th className="text-left py-3 text-gray-500 font-medium hidden sm:table-cell">Paid From</th>
                <th className="text-right py-3 text-gray-500 font-medium">Amount</th>
                <th className="text-right py-3 text-gray-500 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {expenses.map(e => (
                <tr key={e.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-3">
                    <div className="font-medium text-gray-800">{e.description}</div>
                    {e.vendor && <div className="text-xs text-gray-400">{e.vendor}</div>}
                  </td>
                  <td className="py-3 hidden sm:table-cell">
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                      {catLabel(e.category)}
                    </span>
                  </td>
                  <td className="py-3 text-gray-500 hidden sm:table-cell">{e.date}</td>
                  <td className="py-3 text-gray-500 hidden sm:table-cell capitalize">{e.paid_from}</td>
                  <td className="py-3 text-right font-semibold text-red-600">
                    Rs. {e.amount.toLocaleString()}
                  </td>
                  <td className="py-3 text-right">
                    <button onClick={() => handleDelete(e.id)}
                      className="text-gray-300 hover:text-red-500 text-xs transition-colors">✕</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
