"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Contact {
  id: string;
  name: string;
  contact_type: string;
  phone: string | null;
  whatsapp: string | null;
  email: string | null;
  udhar_balance: number;
}

export default function ContactsPage() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [orgId, setOrgId] = useState("");

  // form state
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [type, setType] = useState("customer");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const loadContacts = (org: string) => {
    fetch(`${API}/api/contacts/list?org_id=${org}`)
      .then(r => r.json())
      .then(setContacts)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    const org = localStorage.getItem("org_id");
    if (!org) { setLoading(false); return; }
    setOrgId(org);
    loadContacts(org);
  }, []);

  const handleCreate = async () => {
    if (!name.trim()) { setError("Name is required"); return; }
    setError(""); setSaving(true);
    try {
      const res = await fetch(`${API}/api/contacts/create`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ org_id: orgId, name, phone: phone || null, contact_type: type }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to create contact");
      setName(""); setPhone(""); setType("customer");
      setShowForm(false);
      loadContacts(orgId);
    } catch (e: any) { setError(e.message); }
    finally { setSaving(false); }
  };

  const typeColor = (t: string) => {
    if (t === "supplier") return "bg-orange-100 text-orange-700";
    if (t === "both") return "bg-purple-100 text-purple-700";
    return "bg-blue-100 text-blue-700";
  };

  if (loading) return (
    <div className="p-8 flex items-center justify-center h-96">
      <div className="text-gray-400 animate-pulse">Loading contacts...</div>
    </div>
  );

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Contacts</h1>
          <p className="text-sm text-gray-500 mt-1">{contacts.length} contact(s)</p>
        </div>
        <button onClick={() => setShowForm(!showForm)}
          className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">
          {showForm ? "Cancel" : "+ Add Contact"}
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
          {error && <div className="bg-red-50 text-red-600 text-sm px-4 py-2.5 rounded-lg mb-4">{error}</div>}
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Name *</label>
              <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder="Bilal Traders" value={name} onChange={e => setName(e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Phone / WhatsApp</label>
              <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder="03001234567" value={phone} onChange={e => setPhone(e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Type</label>
              <select className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                value={type} onChange={e => setType(e.target.value)}>
                <option value="customer">Customer</option>
                <option value="supplier">Supplier</option>
                <option value="both">Both</option>
              </select>
            </div>
          </div>
          <button onClick={handleCreate} disabled={saving}
            className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors disabled:opacity-50">
            {saving ? "Saving..." : "Save Contact"}
          </button>
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 p-5">
        {contacts.length === 0 ? (
          <div className="text-center py-12 text-gray-400 text-sm">
            No contacts yet. Add your first customer or supplier.
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left py-3 text-gray-500 font-medium">Name</th>
                <th className="text-left py-3 text-gray-500 font-medium">Type</th>
                <th className="text-left py-3 text-gray-500 font-medium">Phone</th>
                <th className="text-right py-3 text-gray-500 font-medium">Udhar Balance</th>
              </tr>
            </thead>
            <tbody>
              {contacts.map(c => (
                <tr key={c.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-3 font-medium text-gray-800">{c.name}</td>
                  <td className="py-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${typeColor(c.contact_type)}`}>
                      {c.contact_type}
                    </span>
                  </td>
                  <td className="py-3 text-gray-500">{c.phone || "—"}</td>
                  <td className={`py-3 text-right font-semibold ${c.udhar_balance > 0 ? "text-orange-600" : "text-gray-400"}`}>
                    {c.udhar_balance > 0 ? `Rs. ${c.udhar_balance.toLocaleString()}` : "—"}
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
