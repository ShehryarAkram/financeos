"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Contact {
  id: string;
  name: string;
  phone: string | null;
  whatsapp: string | null;
  udhar_balance: number;
}

export default function UdharPage() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [sendingId, setSendingId] = useState<string | null>(null);
  const [sentIds, setSentIds] = useState<Set<string>>(new Set());
  const [orgId, setOrgId] = useState("");

  useEffect(() => {
    const org = localStorage.getItem("org_id");
    if (!org) { setLoading(false); return; }
    setOrgId(org);

    fetch(`${API}/api/contacts/udhar/list?org_id=${org}`)
      .then(r => r.json())
      .then(d => { setContacts(d.contacts); setTotal(d.total_udhar); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const sendReminder = async (contact: Contact) => {
    if (!contact.whatsapp) {
      alert(`${contact.name} ka WhatsApp number nahi hai. Pehle Contacts mein add karein.`);
      return;
    }
    setSendingId(contact.id);
    try {
      const res = await fetch(`${API}/api/contacts/${contact.id}/send-reminder`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ org_id: orgId }),
      });
      const data = await res.json();
      if (res.ok && data.status === "sent") {
        setSentIds(prev => new Set(prev).add(contact.id));
      } else {
        alert("Reminder send nahi ho saka. Dobara koshish karein.");
      }
    } catch {
      alert("Connection error.");
    } finally {
      setSendingId(null);
    }
  };

  if (loading) return (
    <div className="p-8 flex items-center justify-center h-96">
      <div className="text-gray-400 animate-pulse">Loading udhar book...</div>
    </div>
  );

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Udhar Book 📒</h1>
        <p className="text-sm text-gray-500 mt-1">{contacts.length} customer(s) with outstanding balance</p>
      </div>

      {/* Total banner */}
      <div className="bg-orange-50 border border-orange-200 rounded-xl p-5 mb-6 flex items-center justify-between">
        <div>
          <div className="text-xs font-medium text-orange-600 uppercase tracking-wide mb-1">Total Udhar Outstanding</div>
          <div className="text-3xl font-bold text-orange-700">Rs. {total.toLocaleString()}</div>
        </div>
        <div className="text-5xl opacity-20">💰</div>
      </div>

      {/* List */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        {contacts.length === 0 ? (
          <div className="text-center py-12 text-gray-400 text-sm">
            🎉 Koi udhar baqi nahi hai. Sab clear hai!
          </div>
        ) : (
          <div className="divide-y divide-gray-50">
            {contacts.map(c => (
              <div key={c.id} className="flex items-center justify-between py-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-orange-100 text-orange-700 flex items-center justify-center font-semibold text-sm">
                    {c.name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div className="font-medium text-gray-800">{c.name}</div>
                    <div className="text-xs text-gray-400">{c.phone || c.whatsapp || "No phone on file"}</div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="font-bold text-orange-600">Rs. {c.udhar_balance.toLocaleString()}</div>
                  </div>
                  <button
                    onClick={() => sendReminder(c)}
                    disabled={sendingId === c.id || sentIds.has(c.id)}
                    className={`text-xs font-medium px-3 py-1.5 rounded-lg transition-colors ${
                      sentIds.has(c.id)
                        ? "bg-green-50 text-green-600 cursor-default"
                        : "bg-white border border-gray-200 text-gray-600 hover:bg-gray-50"
                    }`}>
                    {sendingId === c.id ? "Sending..." : sentIds.has(c.id) ? "✓ Sent" : "📱 Send Reminder"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
