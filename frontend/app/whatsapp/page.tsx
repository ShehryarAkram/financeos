"use client";
import { useState } from "react";

const API = "http://localhost:8000";
const PHONE = typeof window !== "undefined" ? localStorage.getItem("phone") || "" : "";
const QUICK = ["500 aaya kapra","bijli ka bill 3500 gaya","Ahmed ka 2000 udhar","Ahmed ne 500 diya","hisaab"];

interface Msg { role: "user"|"bot"; text: string; intent?: string; }

export default function WAPage() {
  const [messages, setMessages] = useState<Msg[]>([
    { role: "bot", text: "Assalam o Alaikum! 👋\nMein FinanceOS bot hoon.\n\nMisaal:\n• 500 aaya kapra\n• Ahmed ka 1000 udhar\n• bijli ka bill 2000 gaya\n• hisaab" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const send = async (msg: string) => {
    if (!msg.trim()) return;
    setMessages(p => [...p, { role: "user", text: msg }]);
    setInput(""); setLoading(true);
    try {
      const res = await fetch(`${API}/api/whatsapp/test-full`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone: PHONE, message: msg }),
      });
      const data = await res.json();
      setMessages(p => [...p, { role: "bot", text: data.reply || "Error", intent: data.intent?.intent }]);
    } catch {
      setMessages(p => [...p, { role: "bot", text: "⚠️ Server se connection nahi." }]);
    } finally { setLoading(false); }
  };

  return (
    <div className="p-8 max-w-2xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">WhatsApp Bot Test</h1>
        <p className="text-sm text-gray-500 mt-1">Type in Urdu/Roman Urdu — hits real database</p>
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        {QUICK.map(t => (
          <button key={t} onClick={() => send(t)}
            className="text-xs bg-green-50 text-green-700 border border-green-200 px-3 py-1.5 rounded-full hover:bg-green-100 transition-colors">
            {t}
          </button>
        ))}
      </div>

      <div className="bg-gray-50 rounded-xl border border-gray-200 h-96 overflow-y-auto flex flex-col gap-3 p-4 mb-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-xs rounded-xl px-4 py-2.5 text-sm whitespace-pre-line ${
              m.role === "user" ? "bg-green-600 text-white rounded-br-none" : "bg-white border border-gray-200 text-gray-800 rounded-bl-none"
            }`}>
              {m.role === "bot" && m.intent && <div className="text-xs text-gray-400 mb-1 font-mono">[{m.intent}]</div>}
              {m.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-xl px-4 py-2.5 text-gray-400 text-sm animate-pulse">Soch raha hoon...</div>
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <input className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          placeholder="Urdu mein likhein... (500 aaya, Ahmed ka 1000 udhar)"
          value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && send(input)} />
        <button onClick={() => send(input)} disabled={loading || !input.trim()}
          className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-5 py-2 rounded-lg disabled:opacity-50">
          Send
        </button>
      </div>
    </div>
  );
}
