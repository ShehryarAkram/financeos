const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
async function request(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers: { "Content-Type": "application/json", ...options.headers } });
  if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || `Error ${res.status}`); }
  return res.json();
}
export const api = {
  createInvoice: (d: object) => request("/api/invoices/create", { method: "POST", body: JSON.stringify(d) }),
  testFull: (phone: string, message: string) => request("/api/whatsapp/test-full", { method: "POST", body: JSON.stringify({ phone, message }) }),
};
