"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ReportsPage() {
  const [pl, setPl] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const year = new Date().getFullYear();
  const [from, setFrom] = useState(`${year}-01-01`);
  const [to, setTo] = useState(`${year}-12-31`);

  const load = () => {
    const org = localStorage.getItem("org_id");
    if (!org) return;
    setLoading(true);
    fetch(`${API}/api/reports/pl?org_id=${org}&from_date=${from}&to_date=${to}`)
      .then(r => r.json())
      .then(setPl)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Reports</h1>

      {/* Date filter */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6 flex gap-3 items-end">
        <div>
          <label className="text-xs text-gray-500 mb-1 block">From</label>
          <input type="date" className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
            value={from} onChange={e => setFrom(e.target.value)} />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">To</label>
          <input type="date" className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
            value={to} onChange={e => setTo(e.target.value)} />
        </div>
        <button onClick={load} disabled={loading}
          className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50">
          {loading ? "..." : "Generate"}
        </button>
      </div>

      {pl && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="text-sm font-semibold text-gray-700 mb-4">
            Profit & Loss — {pl.period.from} to {pl.period.to}
          </div>

          {/* Income */}
          <div className="mb-4">
            <div className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">Income</div>
            {pl.income.length === 0
              ? <div className="text-sm text-gray-400 py-2">No income recorded</div>
              : pl.income.map((r: any) => (
                <div key={r.code} className="flex justify-between py-2 border-b border-gray-50 text-sm">
                  <span className="text-gray-700">{r.name}</span>
                  <span className="font-medium text-green-600">Rs. {r.amount.toLocaleString()}</span>
                </div>
              ))
            }
            <div className="flex justify-between py-2 text-sm font-semibold">
              <span>Total Income</span>
              <span className="text-green-600">Rs. {pl.total_income.toLocaleString()}</span>
            </div>
          </div>

          {/* Expenses */}
          <div className="mb-4">
            <div className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">Expenses</div>
            {pl.expenses.length === 0
              ? <div className="text-sm text-gray-400 py-2">No expenses recorded</div>
              : pl.expenses.map((r: any) => (
                <div key={r.code} className="flex justify-between py-2 border-b border-gray-50 text-sm">
                  <span className="text-gray-700">{r.name}</span>
                  <span className="font-medium text-red-500">Rs. {r.amount.toLocaleString()}</span>
                </div>
              ))
            }
            <div className="flex justify-between py-2 text-sm font-semibold">
              <span>Total Expenses</span>
              <span className="text-red-500">Rs. {pl.total_expenses.toLocaleString()}</span>
            </div>
          </div>

          {/* Net */}
          <div className={`flex justify-between py-3 px-4 rounded-lg text-base font-bold ${pl.net_profit >= 0 ? "bg-green-50" : "bg-red-50"}`}>
            <span>Net {pl.net_profit >= 0 ? "Profit" : "Loss"}</span>
            <span className={pl.net_profit >= 0 ? "text-green-600" : "text-red-600"}>
              Rs. {Math.abs(pl.net_profit).toLocaleString()}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
