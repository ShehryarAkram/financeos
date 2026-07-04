"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const UNITS = ["piece", "kg", "gram", "meter", "litre", "dozen", "box", "carton", "bag"];

interface Product { id: string; name: string; short_name: string; default_price: number; unit: string; }

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [orgId, setOrgId] = useState("");
  const [name, setName] = useState("");
  const [shortName, setShortName] = useState("");
  const [price, setPrice] = useState("");
  const [unit, setUnit] = useState("piece");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = (org: string) => {
    fetch(`${API}/api/products/list?org_id=${org}`)
      .then(r => r.json())
      .then(d => setProducts(Array.isArray(d) ? d : []))
      .catch(() => setProducts([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    const org = localStorage.getItem("org_id") || "";
    setOrgId(org);
    if (org) load(org);
    else setLoading(false);
  }, []);

  const handleCreate = async () => {
    if (!name || !shortName || !price) { setError("All fields required"); return; }
    setError(""); setSaving(true);
    try {
      const res = await fetch(`${API}/api/products/create`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ org_id: orgId, name, short_name: shortName, default_price: parseFloat(price), unit }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed");
      setName(""); setShortName(""); setPrice(""); setUnit("piece");
      setShowForm(false);
      load(orgId);
    } catch (e: any) { setError(e.message); }
    finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Remove this product?")) return;
    await fetch(`${API}/api/products/${id}`, { method: "DELETE" });
    load(orgId);
  };

  if (loading) return <div className="p-8 flex items-center justify-center h-96"><div className="text-gray-400 animate-pulse">Loading...</div></div>;

  return (
    <div className="p-4 lg:p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Product Catalog</h1>
          <p className="text-sm text-gray-500 mt-1">Pre-add items for quick invoice filling</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
          {showForm ? "Cancel" : "+ Add Product"}
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
          {error && <div className="bg-red-50 text-red-600 text-sm px-3 py-2 rounded-lg mb-3">{error}</div>}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Full name *</label>
              <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder="Basmati Rice 1kg" value={name} onChange={e => setName(e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Short name (for quick search) *</label>
              <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder="rice" value={shortName} onChange={e => setShortName(e.target.value.toLowerCase())} />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Default price (Rs.) *</label>
              <input type="number" className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder="250" value={price} onChange={e => setPrice(e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Unit</label>
              <select className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                value={unit} onChange={e => setUnit(e.target.value)}>
                {UNITS.map(u => <option key={u} value={u}>{u}</option>)}
              </select>
            </div>
          </div>
          <button onClick={handleCreate} disabled={saving}
            className="bg-green-600 text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50">
            {saving ? "Saving..." : "Save Product"}
          </button>
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 p-4">
        {products.length === 0 ? (
          <div className="text-center py-12 text-gray-400 text-sm">
            No products yet.<br />Add items like "rice", "daal", "kapra" so they auto-fill in invoices.
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left py-3 text-gray-500 font-medium">Short Name</th>
                <th className="text-left py-3 text-gray-500 font-medium">Full Name</th>
                <th className="text-left py-3 text-gray-500 font-medium">Unit</th>
                <th className="text-right py-3 text-gray-500 font-medium">Price</th>
                <th className="text-right py-3 text-gray-500 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {products.map(p => (
                <tr key={p.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-3 font-mono text-green-700 font-medium">{p.short_name}</td>
                  <td className="py-3 text-gray-800">{p.name}</td>
                  <td className="py-3 text-gray-500">{p.unit}</td>
                  <td className="py-3 text-right font-semibold">Rs. {p.default_price.toLocaleString()}</td>
                  <td className="py-3 text-right">
                    <button onClick={() => handleDelete(p.id)} className="text-red-400 hover:text-red-600 text-xs">Remove</button>
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
