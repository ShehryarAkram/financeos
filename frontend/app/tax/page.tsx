"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const WHT_SECTIONS = [
  { value: "153a", label: "153A — Goods (4.5% filer / 9% non-filer)" },
  { value: "153b", label: "153B — Services (8% filer / 16% non-filer)" },
  { value: "236g", label: "236G — Advance on distributor sales (0.1% / 0.2%)" },
];

const SALES_TAX_RATES = [
  { value: 0,  label: "Exempt (0%)" },
  { value: 5,  label: "Reduced (5%)" },
  { value: 10, label: "Reduced (10%)" },
  { value: 12, label: "Reduced (12%)" },
  { value: 17, label: "Standard GST (17%)" },
];

export default function TaxPage() {
  const [tab, setTab] = useState<"settings"|"wht"|"gst"|"summary">("settings");
  const [orgId, setOrgId] = useState("");

  // Settings state
  const [settings, setSettings] = useState<any>(null);
  const [ntn, setNtn] = useState("");
  const [strn, setStrn] = useState("");
  const [isFiler, setIsFiler] = useState(false);
  const [stRegistered, setStRegistered] = useState(false);
  const [stRate, setStRate] = useState(17);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // WHT calculator state
  const [whtAmount, setWhtAmount] = useState("");
  const [whtSection, setWhtSection] = useState("153a");
  const [supplierFiler, setSupplierFiler] = useState(false);
  const [whtResult, setWhtResult] = useState<any>(null);

  // GST calculator state
  const [gstAmount, setGstAmount] = useState("");
  const [gstRate, setGstRate] = useState(17);
  const [gstResult, setGstResult] = useState<any>(null);

  // Monthly summary state
  const [summYear, setSummYear] = useState(new Date().getFullYear());
  const [summMonth, setSummMonth] = useState(new Date().getMonth() + 1);
  const [summary, setSummary] = useState<any>(null);
  const [loadingSumm, setLoadingSumm] = useState(false);

  useEffect(() => {
    const org = localStorage.getItem("org_id") || "";
    setOrgId(org);
    if (org) {
      fetch(`${API}/api/tax/settings/${org}`)
        .then(r => r.json())
        .then(d => {
          setSettings(d);
          setNtn(d.ntn || "");
          setStrn(d.strn || "");
          setIsFiler(d.is_tax_filer || false);
          setStRegistered(d.sales_tax_registered || false);
          setStRate(d.sales_tax_rate || 17);
        }).catch(console.error);
    }
  }, []);

  const saveSettings = async () => {
    setSaving(true);
    try {
      await fetch(`${API}/api/tax/settings/${orgId}`, {
        method: "PATCH", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ntn: ntn || null, strn: strn || null,
          is_tax_filer: isFiler, sales_tax_registered: stRegistered,
          sales_tax_rate: stRate,
        }),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) { console.error(e); }
    finally { setSaving(false); }
  };

  const calcWHT = async () => {
    if (!whtAmount) return;
    const res = await fetch(`${API}/api/tax/calculate-wht`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount: parseFloat(whtAmount), section: whtSection, supplier_is_filer: supplierFiler }),
    });
    setWhtResult(await res.json());
  };

  const calcGST = async () => {
    if (!gstAmount) return;
    const res = await fetch(`${API}/api/tax/calculate-sales-tax`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount: parseFloat(gstAmount), rate: gstRate }),
    });
    setGstResult(await res.json());
  };

  const loadSummary = async () => {
    setLoadingSumm(true);
    try {
      const res = await fetch(`${API}/api/tax/monthly-summary/${orgId}?year=${summYear}&month=${summMonth}`);
      setSummary(await res.json());
    } catch (e) { console.error(e); }
    finally { setLoadingSumm(false); }
  };

  const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

  return (
    <div className="p-4 lg:p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">FBR Tax Module</h1>
        <p className="text-sm text-gray-500 mt-1">WHT calculator, GST, monthly summaries — Pakistan tax compliance</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1 mb-6 overflow-x-auto">
        {[
          { id: "settings", label: "⚙️ Tax Settings" },
          { id: "wht",      label: "🧮 WHT Calculator" },
          { id: "gst",      label: "💰 GST Calculator" },
          { id: "summary",  label: "📋 Monthly Summary" },
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id as any)}
            className={`flex-shrink-0 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              tab === t.id ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Settings */}
      {tab === "settings" && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 max-w-lg">
          <div className="text-sm font-semibold mb-4">Business Tax Profile</div>
          <div className="space-y-4">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">NTN (National Tax Number)</label>
              <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder="1234567-8" value={ntn} onChange={e => setNtn(e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">STRN (Sales Tax Reg. Number)</label>
              <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder="12-34-5678-001-23" value={strn} onChange={e => setStrn(e.target.value)} />
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <div className="text-sm font-medium text-gray-800">FBR Active Taxpayer (Filer)</div>
                <div className="text-xs text-gray-500">Affects WHT rates on payments</div>
              </div>
              <button onClick={() => setIsFiler(!isFiler)}
                className={`w-10 h-6 rounded-full transition-colors ${isFiler ? "bg-green-500" : "bg-gray-300"}`}>
                <div className={`w-4 h-4 bg-white rounded-full mx-1 transition-transform ${isFiler ? "translate-x-4" : ""}`} />
              </button>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <div className="text-sm font-medium text-gray-800">Sales Tax Registered</div>
                <div className="text-xs text-gray-500">Required to charge GST on invoices</div>
              </div>
              <button onClick={() => setStRegistered(!stRegistered)}
                className={`w-10 h-6 rounded-full transition-colors ${stRegistered ? "bg-green-500" : "bg-gray-300"}`}>
                <div className={`w-4 h-4 bg-white rounded-full mx-1 transition-transform ${stRegistered ? "translate-x-4" : ""}`} />
              </button>
            </div>
            {stRegistered && (
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Your Sales Tax Rate</label>
                <select className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                  value={stRate} onChange={e => setStRate(parseFloat(e.target.value))}>
                  {SALES_TAX_RATES.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
                </select>
              </div>
            )}
            <button onClick={saveSettings} disabled={saving}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2.5 rounded-lg transition-colors disabled:opacity-50">
              {saving ? "Saving..." : saved ? "✓ Saved!" : "Save Tax Settings"}
            </button>
          </div>
        </div>
      )}

      {/* WHT Calculator */}
      {tab === "wht" && (
        <div className="max-w-lg">
          <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4">
            <div className="text-sm font-semibold mb-4">Withholding Tax Calculator</div>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Payment Amount (Rs.)</label>
                <input type="number" className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="100000" value={whtAmount} onChange={e => setWhtAmount(e.target.value)} />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">WHT Section</label>
                <select className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                  value={whtSection} onChange={e => setWhtSection(e.target.value)}>
                  {WHT_SECTIONS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                </select>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <div className="text-sm font-medium text-gray-800">Supplier is FBR Filer?</div>
                  <div className="text-xs text-gray-500">Filers get lower WHT rates</div>
                </div>
                <button onClick={() => setSupplierFiler(!supplierFiler)}
                  className={`w-10 h-6 rounded-full transition-colors ${supplierFiler ? "bg-green-500" : "bg-gray-300"}`}>
                  <div className={`w-4 h-4 bg-white rounded-full mx-1 transition-transform ${supplierFiler ? "translate-x-4" : ""}`} />
                </button>
              </div>
              <button onClick={calcWHT}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2.5 rounded-lg">
                Calculate WHT
              </button>
            </div>
          </div>

          {whtResult && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <div className="text-sm font-semibold mb-3">Calculation Result</div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between py-2 border-b border-gray-50">
                  <span className="text-gray-500">Gross Amount</span>
                  <span className="font-medium">Rs. {whtResult.gross_amount?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-gray-50">
                  <span className="text-gray-500">WHT Section</span>
                  <span className="font-medium">Sec. {whtResult.section?.toUpperCase()}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-gray-50">
                  <span className="text-gray-500">Supplier Status</span>
                  <span className={`font-medium ${supplierFiler ? "text-green-600" : "text-orange-600"}`}>
                    {whtResult.supplier_status}
                  </span>
                </div>
                <div className="flex justify-between py-2 border-b border-gray-50">
                  <span className="text-gray-500">WHT Rate</span>
                  <span className="font-medium text-red-500">{whtResult.wht_rate}%</span>
                </div>
                <div className="flex justify-between py-2 border-b border-gray-50">
                  <span className="text-gray-500">WHT to Deduct</span>
                  <span className="font-medium text-red-500">Rs. {whtResult.wht_amount?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between py-2 font-bold text-base">
                  <span>Net Payable to Supplier</span>
                  <span className="text-green-600">Rs. {whtResult.net_payable?.toLocaleString()}</span>
                </div>
              </div>
              <div className="mt-3 p-3 bg-blue-50 rounded-lg text-xs text-blue-700">
                💡 Deduct Rs. {whtResult.wht_amount?.toLocaleString()} from payment and deposit to FBR by 15th of next month.
              </div>
            </div>
          )}
        </div>
      )}

      {/* GST Calculator */}
      {tab === "gst" && (
        <div className="max-w-lg">
          <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4">
            <div className="text-sm font-semibold mb-4">Sales Tax (GST) Calculator</div>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Amount before tax (Rs.)</label>
                <input type="number" className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="50000" value={gstAmount} onChange={e => setGstAmount(e.target.value)} />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Tax Rate</label>
                <select className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                  value={gstRate} onChange={e => setGstRate(parseFloat(e.target.value))}>
                  {SALES_TAX_RATES.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
                </select>
              </div>
              <button onClick={calcGST}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2.5 rounded-lg">
                Calculate GST
              </button>
            </div>
          </div>

          {gstResult && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <div className="text-sm font-semibold mb-3">GST Breakdown</div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between py-2 border-b border-gray-50">
                  <span className="text-gray-500">Subtotal</span>
                  <span className="font-medium">Rs. {gstResult.subtotal?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-gray-50">
                  <span className="text-gray-500">GST ({gstResult.tax_rate}%)</span>
                  <span className="font-medium text-orange-600">+ Rs. {gstResult.tax_amount?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between py-2 font-bold text-base">
                  <span>Total Payable</span>
                  <span className="text-green-600">Rs. {gstResult.total_with_tax?.toLocaleString()}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Monthly Summary */}
      {tab === "summary" && (
        <div className="max-w-2xl">
          <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4">
            <div className="text-sm font-semibold mb-3">Monthly Tax Summary</div>
            <div className="flex gap-3 items-end">
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Year</label>
                <input type="number" className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-24 focus:outline-none focus:ring-2 focus:ring-green-500"
                  value={summYear} onChange={e => setSummYear(parseInt(e.target.value))} />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Month</label>
                <select className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                  value={summMonth} onChange={e => setSummMonth(parseInt(e.target.value))}>
                  {MONTHS.map((m, i) => <option key={i+1} value={i+1}>{m}</option>)}
                </select>
              </div>
              <button onClick={loadSummary} disabled={loadingSumm}
                className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50">
                {loadingSumm ? "Loading..." : "Generate"}
              </button>
            </div>
          </div>

          {summary && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <div className="text-sm font-semibold">Tax Summary — {summary.period}</div>
                  <div className="text-xs text-gray-400">{summary.from_date} to {summary.to_date}</div>
                </div>
                <span className="text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded-full">{summary.invoice_count} invoices</span>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between py-2 border-b border-gray-50">
                  <span className="text-gray-500">Total Sales</span>
                  <span className="font-medium text-green-600">Rs. {summary.total_sales?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-gray-50">
                  <span className="text-gray-500">Total Purchases</span>
                  <span className="font-medium text-red-500">Rs. {summary.total_purchases?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-gray-50">
                  <span className="text-gray-500">Output Tax (GST Collected)</span>
                  <span className="font-medium">Rs. {summary.sales_tax_collected?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-gray-50">
                  <span className="text-gray-500">WHT Deducted</span>
                  <span className="font-medium">Rs. {summary.wht_deducted?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between py-2 font-bold text-base">
                  <span>Net Tax Payable to FBR</span>
                  <span className={summary.net_tax_payable > 0 ? "text-red-600" : "text-green-600"}>
                    Rs. {summary.net_tax_payable?.toLocaleString()}
                  </span>
                </div>
              </div>

              <div className="mt-4 p-3 bg-amber-50 rounded-lg text-xs text-amber-700">
                ⚠️ {summary.note}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
