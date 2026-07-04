"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
interface Line { description: string; quantity: number; unit_price: number; }
interface Product { id: string; name: string; short_name: string; default_price: number; unit: string; }

export default function NewInvoicePage() {
  const router = useRouter();
  const [orgId, setOrgId] = useState("");
  const [contactName, setContactName] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [dueDays, setDueDays] = useState(30);
  const [notes, setNotes] = useState("");
  const [lines, setLines] = useState<Line[]>([{ description: "", quantity: 1, unit_price: 0 }]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [suggestions, setSuggestions] = useState<Product[]>([]);
  const [activeLine, setActiveLine] = useState<number | null>(null);

  useEffect(() => {
    const org = localStorage.getItem("org_id") || "";
    setOrgId(org);
    if (org) {
      fetch(`${API}/api/products/list?org_id=${org}`)
        .then(r => r.json())
        .then(d => setProducts(Array.isArray(d) ? d : []))
        .catch(() => setProducts([]));
    }
  }, []);

  const addLine = () => setLines([...lines, { description: "", quantity: 1, unit_price: 0 }]);
  const removeLine = (i: number) => setLines(lines.filter((_, idx) => idx !== i));

  const updateLine = (i: number, field: keyof Line, value: string | number) => {
    const u = [...lines];
    (u[i] as any)[field] = value;
    setLines(u);

    // Show product suggestions when typing description
    if (field === "description" && typeof value === "string" && value.length > 0) {
      const matches = products.filter(p =>
        p.short_name.toLowerCase().includes(value.toLowerCase()) ||
        p.name.toLowerCase().includes(value.toLowerCase())
      );
      setSuggestions(matches.slice(0, 5));
      setActiveLine(i);
    } else if (field === "description") {
      setSuggestions([]);
    }
  };

  const selectProduct = (i: number, product: Product) => {
    const u = [...lines];
    u[i] = { description: product.name, quantity: u[i].quantity, unit_price: product.default_price };
    setLines(u);
    setSuggestions([]);
    setActiveLine(null);
  };

  const subtotal = lines.reduce((s, l) => s + l.quantity * l.unit_price, 0);

  const handleSubmit = async (sendWhatsapp: boolean) => {
    if (!contactName.trim()) { setError("Customer name required"); return; }
    if (lines.some(l => !l.description || l.unit_price <= 0)) { setError("All items need description and price"); return; }
    setError(""); setLoading(true);
    try {
      const res = await fetch(`${API}/api/invoices/create`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          org_id: orgId, contact_name: contactName,
          contact_phone: contactPhone || "0000000000",
          lines, due_days: dueDays, notes,
          send_whatsapp: sendWhatsapp && !!contactPhone,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed");
      setResult({ ...data, whatsapp_sent: sendWhatsapp && !!contactPhone });
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  if (result) return (
    <div className="p-4 lg:p-8 max-w-lg mx-auto">
      <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
        <div className="text-5xl mb-4">✅</div>
        <h2 className="text-xl font-bold mb-1">{result.invoice_number} Created!</h2>
        <p className="text-gray-500 text-sm mb-1">Customer: {result.contact}</p>
        <p className="text-3xl font-bold text-green-600 my-4">Rs. {result.total?.toLocaleString()}</p>
        <div className="text-xs text-gray-400 mb-2">Due: {result.due_date}</div>
        <div className="text-xs text-gray-400 mb-6">
          Journal entry ✓ {result.whatsapp_sent ? "· WhatsApp sent ✓" : "· WhatsApp not sent"}
        </div>
        <div className="flex gap-3 justify-center">
          <button onClick={() => router.push("/invoices")}
            className="bg-white border border-gray-200 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg">
            View Invoices
          </button>
          <button onClick={() => { setResult(null); setContactName(""); setContactPhone(""); setLines([{ description: "", quantity: 1, unit_price: 0 }]); }}
            className="bg-green-600 text-white text-sm font-medium px-4 py-2 rounded-lg">
            + New Invoice
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="p-4 lg:p-8 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">New Invoice</h1>
        <p className="text-sm text-gray-500 mt-1">Creates invoice + accounting entry automatically</p>
      </div>
      {error && <div className="bg-red-50 text-red-600 text-sm px-4 py-2.5 rounded-lg mb-4">{error}</div>}

      {/* Customer */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4">
        <div className="text-sm font-semibold mb-3">Customer</div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Name *</label>
            <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="Ahmed Khan" value={contactName} onChange={e => setContactName(e.target.value)} />
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Phone (for WhatsApp)</label>
            <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="03001234567" value={contactPhone} onChange={e => setContactPhone(e.target.value)} />
          </div>
        </div>
      </div>

      {/* Items */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4">
        <div className="text-sm font-semibold mb-3">Items</div>

        {/* Column headers — desktop */}
        <div className="hidden sm:grid sm:grid-cols-12 gap-2 mb-2">
          <div className="col-span-5 text-xs text-gray-400 font-medium">Description</div>
          <div className="col-span-2 text-xs text-gray-400 font-medium">Qty</div>
          <div className="col-span-3 text-xs text-gray-400 font-medium">Unit Price (Rs.)</div>
          <div className="col-span-2 text-xs text-gray-400 font-medium text-right">Total</div>
        </div>

        {lines.map((line, i) => (
          <div key={i} className="mb-3 relative">
            {/* Mobile: stacked layout */}
            <div className="sm:hidden space-y-2 bg-gray-50 rounded-lg p-3 mb-1">
              <div>
                <label className="text-xs text-gray-400">Item description</label>
                <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-green-500 mt-1"
                  placeholder="e.g. Kapra, Daal, Service..." value={line.description}
                  onChange={e => updateLine(i, "description", e.target.value)} />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs text-gray-400">Quantity</label>
                  <input type="number" className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-green-500 mt-1"
                    value={line.quantity} onChange={e => updateLine(i, "quantity", parseFloat(e.target.value) || 0)} />
                </div>
                <div>
                  <label className="text-xs text-gray-400">Price per unit</label>
                  <input type="number" className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-green-500 mt-1"
                    value={line.unit_price} onChange={e => updateLine(i, "unit_price", parseFloat(e.target.value) || 0)} />
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">Line total: <span className="font-semibold text-gray-800">Rs. {(line.quantity * line.unit_price).toLocaleString()}</span></span>
                {lines.length > 1 && <button onClick={() => removeLine(i)} className="text-red-400 text-xs">Remove</button>}
              </div>
            </div>

            {/* Desktop: grid layout */}
            <div className="hidden sm:grid sm:grid-cols-12 gap-2 items-center">
              <div className="col-span-5 relative">
                <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="Item description" value={line.description}
                  onChange={e => updateLine(i, "description", e.target.value)} />
              </div>
              <div className="col-span-2">
                <input type="number" className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                  value={line.quantity} onChange={e => updateLine(i, "quantity", parseFloat(e.target.value) || 0)} />
              </div>
              <div className="col-span-3">
                <input type="number" className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                  value={line.unit_price} onChange={e => updateLine(i, "unit_price", parseFloat(e.target.value) || 0)} />
              </div>
              <div className="col-span-1 text-sm font-medium text-right text-gray-700">
                {(line.quantity * line.unit_price).toLocaleString()}
              </div>
              <div className="col-span-1 text-center">
                {lines.length > 1 && <button onClick={() => removeLine(i)} className="text-red-400 hover:text-red-600 text-lg">×</button>}
              </div>
            </div>

            {/* Product suggestions dropdown */}
            {activeLine === i && suggestions.length > 0 && (
              <div className="absolute left-0 right-0 top-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                {suggestions.map(p => (
                  <button key={p.id} onClick={() => selectProduct(i, p)}
                    className="w-full text-left px-4 py-2.5 text-sm hover:bg-green-50 flex justify-between items-center border-b border-gray-50 last:border-0">
                    <span><span className="font-medium">{p.short_name}</span> — {p.name}</span>
                    <span className="text-green-600 text-xs font-medium">Rs. {p.default_price.toLocaleString()}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}

        <button onClick={addLine} className="text-green-600 text-sm font-medium hover:text-green-700">+ Add Item</button>

        <div className="border-t border-gray-100 mt-4 pt-3 flex justify-between font-bold text-base">
          <span>Total</span>
          <span className="text-green-600">Rs. {subtotal.toLocaleString()}</span>
        </div>
      </div>

      {/* Options */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Due in (days)</label>
            <input type="number" className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              value={dueDays} onChange={e => setDueDays(parseInt(e.target.value))} />
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Notes</label>
            <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="Optional notes..." value={notes} onChange={e => setNotes(e.target.value)} />
          </div>
        </div>
      </div>

      {/* Two separate buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <button onClick={() => handleSubmit(false)} disabled={loading}
          className="w-full bg-gray-800 hover:bg-gray-900 text-white font-medium py-3 rounded-lg transition-colors disabled:opacity-50 text-sm">
          {loading ? "Saving..." : "💾 Save Invoice"}
        </button>
        <button onClick={() => handleSubmit(true)} disabled={loading || !contactPhone}
          title={!contactPhone ? "Add phone number to send via WhatsApp" : ""}
          className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 rounded-lg transition-colors disabled:opacity-50 text-sm">
          {loading ? "Saving..." : "📱 Save + Send WhatsApp"}
        </button>
      </div>
      {!contactPhone && (
        <p className="text-xs text-gray-400 text-center mt-2">Add customer phone to enable WhatsApp sending</p>
      )}
    </div>
  );
}
