"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Invoice {
  id: string;
  invoice_number: string;
  contact: string;
  total: number;
  amount_paid: number;
  status: string;
  due_date: string;
}

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const orgId = localStorage.getItem("org_id");
    if (!orgId) { setLoading(false); return; }

    fetch(`${API}/api/invoices/list?org_id=${orgId}`)
      .then(r => r.json())
      .then(setInvoices)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const outstanding = invoices.reduce((s, i) => s + (i.total - i.amount_paid), 0);
  const collected = invoices.reduce((s, i) => s + i.amount_paid, 0);
  const overdue = invoices.filter(i => i.status === "overdue").reduce((s, i) => s + (i.total - i.amount_paid), 0);

  const markPaid = async (id: string) => {
    try {
      const res = await fetch(`${API}/api/invoices/${id}/mark-paid`, { method: "POST" });
      if (res.ok) {
        setInvoices(prev => prev.map(inv =>
          inv.id === id ? { ...inv, status: "paid", amount_paid: inv.total } : inv
        ));
      }
    } catch (e) { console.error(e); }
  };

  const statusColor = (status: string) => {
    if (status === "paid") return "bg-green-100 text-green-700";
    if (status === "overdue") return "bg-red-100 text-red-700";
    if (status === "draft") return "bg-gray-100 text-gray-600";
    return "bg-blue-100 text-blue-700";
  };

  if (loading) return (
    <div className="p-8 flex items-center justify-center h-96">
      <div className="text-gray-400 animate-pulse">Loading invoices...</div>
    </div>
  );

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Invoices</h1>
          <p className="text-sm text-gray-500 mt-1">{invoices.length} invoice(s)</p>
        </div>
        <Link href="/invoices/new" className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">+ New Invoice</Link>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-5 text-center">
          <div className="text-2xl font-bold text-blue-600">Rs. {outstanding.toLocaleString()}</div>
          <div className="text-xs text-gray-500 mt-1">Outstanding</div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5 text-center">
          <div className="text-2xl font-bold text-green-600">Rs. {collected.toLocaleString()}</div>
          <div className="text-xs text-gray-500 mt-1">Collected</div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5 text-center">
          <div className="text-2xl font-bold text-red-500">Rs. {overdue.toLocaleString()}</div>
          <div className="text-xs text-gray-500 mt-1">Overdue</div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-5">
        {invoices.length === 0 ? (
          <div className="text-center py-12 text-gray-400 text-sm">
            No invoices yet. <Link href="/invoices/new" className="text-green-600 font-medium">Create your first one →</Link>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left py-3 text-gray-500 font-medium">Invoice #</th>
                <th className="text-left py-3 text-gray-500 font-medium">Customer</th>
                <th className="text-left py-3 text-gray-500 font-medium">Due Date</th>
                <th className="text-left py-3 text-gray-500 font-medium">Status</th>
                <th className="text-right py-3 text-gray-500 font-medium">Amount</th>
                <th className="text-right py-3 text-gray-500 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map(inv => (
                <tr key={inv.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-3 font-medium text-green-700">{inv.invoice_number}</td>
                  <td className="py-3 text-gray-800">{inv.contact}</td>
                  <td className="py-3 text-gray-500">{inv.due_date}</td>
                  <td className="py-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${statusColor(inv.status)}`}>
                      {inv.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-3 text-right font-semibold">Rs. {inv.total.toLocaleString()}</td>
                  <td className="py-3 text-right flex gap-3 justify-end">
                    <a href={`${API}/api/invoices/${inv.id}/pdf`} target="_blank"
                      className="text-green-600 hover:text-green-700 text-xs font-medium">PDF ↗</a>
                    {inv.status !== "paid" && (
                      <button onClick={() => markPaid(inv.id)}
                        className="text-blue-600 hover:text-blue-700 text-xs font-medium">
                        Mark Paid
                      </button>
                    )}
                    {inv.status === "paid" && (
                      <span className="text-xs text-green-600">✓ Paid</span>
                    )}
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
