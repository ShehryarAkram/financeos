"use client";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const CATEGORIES = [
  "salary","utilities","mobile","rent","transport",
  "tax","bank_charge","transfer","miscellaneous"
];

const CAT_COLORS: Record<string,string> = {
  salary: "bg-green-100 text-green-700",
  utilities: "bg-yellow-100 text-yellow-700",
  mobile: "bg-blue-100 text-blue-700",
  rent: "bg-purple-100 text-purple-700",
  transport: "bg-orange-100 text-orange-700",
  tax: "bg-red-100 text-red-700",
  bank_charge: "bg-gray-100 text-gray-600",
  transfer: "bg-cyan-100 text-cyan-700",
  miscellaneous: "bg-gray-100 text-gray-500",
};

interface Transaction {
  date: string; description: string; debit: number;
  credit: number; balance: number; category: string;
  type: string; import?: boolean;
}

export default function BankImportPage() {
  const [step, setStep] = useState<"upload"|"review"|"done">("upload");
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  const orgId = typeof window !== "undefined" ? localStorage.getItem("org_id") || "" : "";

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(""); setLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("org_id", orgId);
      const res = await fetch(`${API}/api/bank/parse`, { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Parse failed");
      setTransactions(data.transactions.map((t: Transaction) => ({ ...t, import: true })));
      setSummary(data);
      setStep("review");
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const toggleAll = (val: boolean) => {
    setTransactions(prev => prev.map(t => ({ ...t, import: val })));
  };

  const toggleOne = (i: number) => {
    setTransactions(prev => prev.map((t, idx) => idx === i ? { ...t, import: !t.import } : t));
  };

  const updateCategory = (i: number, cat: string) => {
    setTransactions(prev => prev.map((t, idx) => idx === i ? { ...t, category: cat } : t));
  };

  const handleImport = async () => {
    setImporting(true);
    try {
      const res = await fetch(`${API}/api/bank/confirm`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ org_id: orgId, transactions }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Import failed");
      setResult(data);
      setStep("done");
    } catch (e: any) { setError((e as any).message); }
    finally { setImporting(false); }
  };

  const selectedCount = transactions.filter(t => t.import !== false).length;

  return (
    <div className="p-4 lg:p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Bank Statement Import</h1>
        <p className="text-sm text-gray-500 mt-1">Upload HBL, MCB, or UBL CSV statement — auto-creates journal entries</p>
      </div>

      {/* Steps indicator */}
      <div className="flex items-center gap-2 mb-6 text-sm">
        {["upload","review","done"].map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
              step === s ? "bg-green-600 text-white" :
              ["upload","review","done"].indexOf(step) > i ? "bg-green-100 text-green-700" :
              "bg-gray-100 text-gray-400"
            }`}>{i+1}</div>
            <span className={step === s ? "text-gray-900 font-medium" : "text-gray-400"}>
              {s === "upload" ? "Upload CSV" : s === "review" ? "Review" : "Done"}
            </span>
            {i < 2 && <div className="w-8 h-px bg-gray-200" />}
          </div>
        ))}
      </div>

      {error && <div className="bg-red-50 text-red-600 text-sm px-4 py-3 rounded-lg mb-4">{error}</div>}

      {/* Upload step */}
      {step === "upload" && (
        <div className="max-w-lg">
          <div className="bg-white rounded-xl border border-gray-200 p-6 mb-4">
            <div className="text-sm font-semibold mb-3">Upload Bank Statement</div>
            <div className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center hover:border-green-400 transition-colors">
              <div className="text-3xl mb-2">🏦</div>
              <div className="text-sm font-medium text-gray-700 mb-1">
                {loading ? "Parsing..." : "Choose CSV file"}
              </div>
              <div className="text-xs text-gray-400 mb-4">HBL · MCB · UBL · Generic CSV</div>
              <label className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg cursor-pointer transition-colors">
                {loading ? "Processing..." : "Select File"}
                <input type="file" accept=".csv" className="hidden" onChange={handleUpload} disabled={loading} />
              </label>
            </div>
          </div>

          <div className="bg-blue-50 rounded-xl p-4 text-xs text-blue-700">
            <div className="font-medium mb-2">How to get your bank statement CSV:</div>
            <div className="space-y-1">
              <div>🏦 <strong>HBL:</strong> Internet Banking → Accounts → Statement → Download CSV</div>
              <div>🏦 <strong>MCB:</strong> MCB Internet Banking → My Accounts → Account Statement → Export</div>
              <div>🏦 <strong>UBL:</strong> UBL Digital → Account → Mini Statement → Download</div>
            </div>
          </div>
        </div>
      )}

      {/* Review step */}
      {step === "review" && (
        <div>
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
              <div className="text-xl font-bold text-gray-800">{summary?.count}</div>
              <div className="text-xs text-gray-500">Transactions found</div>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
              <div className="text-xl font-bold text-red-600">Rs. {summary?.total_debits?.toLocaleString()}</div>
              <div className="text-xs text-gray-500">Total withdrawals</div>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
              <div className="text-xl font-bold text-green-600">Rs. {summary?.total_credits?.toLocaleString()}</div>
              <div className="text-xs text-gray-500">Total deposits</div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm font-semibold">{selectedCount} of {transactions.length} selected</div>
              <div className="flex gap-2">
                <button onClick={() => toggleAll(true)} className="text-xs text-green-600 hover:text-green-700 font-medium">Select all</button>
                <span className="text-gray-300">|</span>
                <button onClick={() => toggleAll(false)} className="text-xs text-gray-500 hover:text-gray-700">Deselect all</button>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="text-left py-2 text-gray-400 font-medium w-8"></th>
                    <th className="text-left py-2 text-gray-400 font-medium">Date</th>
                    <th className="text-left py-2 text-gray-400 font-medium">Description</th>
                    <th className="text-left py-2 text-gray-400 font-medium">Category</th>
                    <th className="text-right py-2 text-gray-400 font-medium">Debit</th>
                    <th className="text-right py-2 text-gray-400 font-medium">Credit</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((t, i) => (
                    <tr key={i} className={`border-b border-gray-50 ${t.import === false ? "opacity-40" : ""}`}>
                      <td className="py-2">
                        <input type="checkbox" checked={t.import !== false}
                          onChange={() => toggleOne(i)}
                          className="rounded border-gray-300 text-green-600" />
                      </td>
                      <td className="py-2 text-gray-600 whitespace-nowrap">{t.date}</td>
                      <td className="py-2 text-gray-800 max-w-xs truncate">{t.description}</td>
                      <td className="py-2">
                        <select value={t.category}
                          onChange={e => updateCategory(i, e.target.value)}
                          className={`text-xs px-2 py-0.5 rounded-full border-0 font-medium ${CAT_COLORS[t.category] || "bg-gray-100 text-gray-600"}`}>
                          {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                      </td>
                      <td className="py-2 text-right text-red-600 font-medium">
                        {t.debit > 0 ? `Rs. ${t.debit.toLocaleString()}` : "—"}
                      </td>
                      <td className="py-2 text-right text-green-600 font-medium">
                        {t.credit > 0 ? `Rs. ${t.credit.toLocaleString()}` : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex gap-3">
            <button onClick={() => { setStep("upload"); setTransactions([]); }}
              className="bg-white border border-gray-200 text-gray-700 text-sm font-medium px-4 py-2.5 rounded-lg">
              ← Back
            </button>
            <button onClick={handleImport} disabled={importing || selectedCount === 0}
              className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-6 py-2.5 rounded-lg disabled:opacity-50">
              {importing ? "Importing..." : `Import ${selectedCount} Transactions`}
            </button>
          </div>
        </div>
      )}

      {/* Done step */}
      {step === "done" && result && (
        <div className="max-w-md">
          <div className="bg-white rounded-xl border border-green-200 p-8 text-center">
            <div className="text-5xl mb-4">✅</div>
            <h2 className="text-xl font-bold mb-2">Import Complete!</h2>
            <div className="text-3xl font-bold text-green-600 my-3">{result.imported}</div>
            <div className="text-sm text-gray-500 mb-1">transactions imported as journal entries</div>
            {result.skipped > 0 && (
              <div className="text-xs text-gray-400 mb-4">{result.skipped} skipped</div>
            )}
            <div className="text-xs text-gray-400 mb-6 bg-gray-50 rounded-lg p-3">
              All transactions are now visible in your Reports and Dashboard.
              Go to Reports → P&L to see the updated figures.
            </div>
            <div className="flex gap-3 justify-center">
              <a href="/reports" className="bg-green-600 text-white text-sm font-medium px-4 py-2 rounded-lg">
                View Reports →
              </a>
              <button onClick={() => { setStep("upload"); setTransactions([]); setResult(null); }}
                className="bg-white border border-gray-200 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg">
                Import Another
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
