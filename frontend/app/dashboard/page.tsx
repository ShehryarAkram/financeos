"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function StatCard({ label, value, sub, color }: { label: string; value: string; sub?: string; color: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">{label}</div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [orgName, setOrgName] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const orgId = localStorage.getItem("org_id");
    const phone = localStorage.getItem("phone");

    if (!orgId || !phone) {
      setLoading(false);
      return;
    }

    fetch(`${API}/api/whatsapp/test-full`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone, message: "hisaab" }),
    })
      .then(r => r.json())
      .then(d => { if (d.result) setStats(d.result); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="p-8 flex items-center justify-center h-96">
      <div className="text-gray-400 animate-pulse text-lg">Loading hisaab...</div>
    </div>
  );

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">
          {new Date().toLocaleDateString("en-PK", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
        </p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Aaj Aaya" value={`Rs. ${(stats?.income || 0).toLocaleString()}`} sub="Today's income" color="text-green-600" />
        <StatCard label="Aaj Gaya" value={`Rs. ${(stats?.expense || 0).toLocaleString()}`} sub="Today's expenses" color="text-red-500" />
        <StatCard label="Net Faida" value={`Rs. ${(stats?.profit || 0).toLocaleString()}`} sub="Today's profit" color="text-blue-600" />
        <StatCard label="Total Udhar" value={`Rs. ${(stats?.total_udhar || 0).toLocaleString()}`} sub="Outstanding" color="text-orange-500" />
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4">
        <div className="text-sm font-semibold text-gray-700 mb-4">Quick Actions</div>
        <div className="flex flex-wrap gap-3">
          <a href="/invoices/new" className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">+ New Invoice</a>
          <a href="/whatsapp" className="bg-white hover:bg-gray-50 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg border border-gray-200 transition-colors">💬 Test WA Bot</a>
          <a href="/reports" className="bg-white hover:bg-gray-50 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg border border-gray-200 transition-colors">📈 Reports</a>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <div className="text-sm font-semibold text-gray-700 mb-4">Recent Transactions</div>
        <p className="text-sm text-gray-400">Transaction history view coming next.</p>
      </div>
    </div>
  );
}
