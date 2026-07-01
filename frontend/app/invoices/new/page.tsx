"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

const ORG_ID = typeof window !== "undefined" ? localStorage.getItem("org_id") || "" : "";
const API = "http://localhost:8000";
interface Line { description: string; quantity: number; unit_price: number; }

export default function NewInvoicePage() {
  const router = useRouter();
  const [contactName, setContactName] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [dueDays, setDueDays] = useState(30);
  const [notes, setNotes] = useState("");
  const [lines, setLines] = useState<Line[]>([{ description: "", quantity: 1, unit_price: 0 }]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  const addLine = () => setLines([...lines, { description: "", quantity: 1, unit_price: 0 }]);
  const removeLine = (i: number) => setLines(lines.filter((_, idx) => idx !== i));
  const updateLine = (i: number, field: keyof Line, value: string | number) => {
    const u = [...lines]; (u[i] as any)[field] = value; setLines(u);
  };
  const subtotal = lines.reduce((s, l) => s + l.quantity * l.unit_price, 0);

  const handleSubmit = async () => {
    if (!contactName || !contactPhone) { setError("Contact name and phone required"); return; }
    if (lines.some(l => !l.description || l.unit_price <= 0)) { setError("All items need description and price"); return; }
    setError(""); setLoading(true);
    try {
      const res = await fetch(`${API}/api/invoices/create`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ org_id: ORG_ID, contact_name: contactName, contact_phone: contactPhone, lines, due_days: dueDays, notes }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed");
      setResult(data);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  if (result) return (
    <div className="p-8 max-w-lg">
      <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
        <div className="text-5xl mb-4">✅</div>
        <h2 className="text-xl font-bold mb-1">{result.invoice_number} Created!</h2>
        <p className="text-gray-500 text-sm mb-1">Customer: {result.contact}</p>
        <p className="text-3xl font-bold text-green-600 my-4">Rs. {result.total?.toLocaleString()}</p>
        <p className="text-xs text-gray-400 mb-6">Due: {result.due_date} · Journal entry created ✓</p>
        <div className="flex gap-3 justify-center">
          <button onClick={() => router.push("/invoices")} className="bg-white border border-gray-200 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg">View Invoices</button>
          <button onClick={() => { setResult(null); setContactName(""); setContactPhone(""); setLines([{ description: "", quantity: 1, unit_price: 0 }]); }}
            className="bg-green-600 text-white text-sm font-medium px-4 py-2 rounded-lg">+ New Invoice</button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="p-8 max-w-2xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">New Invoice</h1>
        <p className="text-sm text-gray-500 mt-1">Creates invoice + journal entry automatically</p>
      </div>
      {error && <div className="bg-red-50 text-red-600 text-sm px-4 py-3 rounded-lg mb-4">{error}</div>}

      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4">
        <div className="text-sm font-semibold mb-3">Customer</div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Name *</label>
            <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500" placeholder="City School" value={contactName} onChange={e => setContactName(e.target.value)} />
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Phone *</label>
            <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500" placeholder="03001234567" value={contactPhone} onChange={e => setContactPhone(e.target.value)} />
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4">
        <div className="text-sm font-semibold mb-3">Items</div>
        {lines.map((line, i) => (
          <div key={i} className="grid grid-cols-12 gap-2 items-center mb-2">
            <div className="col-span-5"><input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500" placeholder="Description" value={line.description} onChange={e => updateLine(i, "description", e.target.value)} /></div>
            <div className="col-span-2"><input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500" type="number" placeholder="Qty" value={line.quantity} onChange={e => updateLine(i, "quantity", parseFloat(e.target.value) || 0)} /></div>
            <div className="col-span-3"><input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500" type="number" placeholder="Price" value={line.unit_price} onChange={e => updateLine(i, "unit_price", parseFloat(e.target.value) || 0)} /></div>
            <div className="col-span-1 text-sm font-medium text-right text-gray-600">{(line.quantity * line.unit_price).toLocaleString()}</div>
            <div className="col-span-1 text-center">{lines.length > 1 && <button onClick={() => removeLine(i)} className="text-red-400 hover:text-red-600 text-xl leading-none">×</button>}</div>
          </div>
        ))}
        <button onClick={addLine} className="text-green-600 text-sm font-medium mt-2 hover:text-green-700">+ Add Item</button>
        <div className="border-t border-gray-100 mt-4 pt-3 flex justify-between font-bold text-base">
          <span>Total</span><span className="text-green-600">Rs. {subtotal.toLocaleString()}</span>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Due in (days)</label>
            <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500" type="number" value={dueDays} onChange={e => setDueDays(parseInt(e.target.value))} />
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Notes</label>
            <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500" placeholder="Payment instructions..." value={notes} onChange={e => setNotes(e.target.value)} />
          </div>
        </div>
      </div>

      <button onClick={handleSubmit} disabled={loading}
        className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 rounded-lg transition-colors disabled:opacity-50 text-base">
        {loading ? "Creating..." : "Create Invoice + Send on WhatsApp 📱"}
      </button>
    </div>
  );
}
