"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

const links = [
  { href: "/dashboard", label: "Dashboard",   icon: "📊" },
  { href: "/invoices",  label: "Invoices",    icon: "📄" },
  { href: "/contacts",  label: "Contacts",    icon: "👥" },
  { href: "/udhar",     label: "Udhar Book",  icon: "📒" },
  { href: "/products",  label: "Products",    icon: "📦" },
  { href: "/reports",   label: "Reports",     icon: "📈" },
  { href: "/tax",       label: "FBR Tax",     icon: "🧾" },
  { href: "/payroll",   label: "Payroll",     icon: "💼" },
  { href: "/whatsapp",  label: "WA Bot Test", icon: "💬" },
];

export default function Sidebar() {
  const path = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("org_id");
    localStorage.removeItem("phone");
    localStorage.removeItem("org_name");
    localStorage.removeItem("dukandaar_mode");
    router.replace("/login");
  };

  const orgName = typeof window !== "undefined"
    ? (localStorage.getItem("org_name") || "My Store")
    : "My Store";

  const NavLinks = () => (
    <>
      {links.map(l => (
        <Link key={l.href} href={l.href}
          onClick={() => setOpen(false)}
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            path.startsWith(l.href)
              ? "bg-green-50 text-green-700"
              : "text-gray-600 hover:bg-green-50 hover:text-green-700"
          }`}>
          <span>{l.icon}</span><span>{l.label}</span>
        </Link>
      ))}
    </>
  );

  return (
    <>
      {/* ── Mobile top bar ── */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-40 bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-green-600 rounded-lg flex items-center justify-center text-white font-bold text-xs">F</div>
          <span className="text-sm font-bold text-gray-900">FinanceOS</span>
        </div>
        <button onClick={() => setOpen(!open)}
          className="p-2 rounded-lg text-gray-600 hover:bg-gray-100">
          {open ? "✕" : "☰"}
        </button>
      </div>

      {/* ── Mobile overlay ── */}
      {open && (
        <div className="lg:hidden fixed inset-0 z-30 bg-black/30"
          onClick={() => setOpen(false)} />
      )}

      {/* ── Mobile drawer ── */}
      <div className={`lg:hidden fixed top-0 left-0 h-full w-64 z-40 bg-white border-r border-gray-200 transform transition-transform duration-200 ${
        open ? "translate-x-0" : "-translate-x-full"
      }`}>
        <div className="px-5 py-4 border-b border-gray-100 mt-14">
          <div className="text-xs text-gray-700 font-medium truncate">{orgName}</div>
          <div className="text-xs text-green-600">Free Plan</div>
        </div>
        <nav className="px-3 py-4 space-y-0.5">
          <NavLinks />
        </nav>
        <div className="absolute bottom-0 left-0 right-0 px-4 py-4 border-t border-gray-100">
          <button onClick={logout} className="text-xs text-gray-400 hover:text-red-500">Sign out →</button>
        </div>
      </div>

      {/* ── Desktop sidebar ── */}
      <aside className="hidden lg:flex w-56 bg-white border-r border-gray-200 min-h-screen flex-col">
        <div className="px-5 py-5 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">F</div>
            <div>
              <div className="text-sm font-bold text-gray-900">FinanceOS</div>
              <div className="text-xs text-gray-400">Pakistan ka hisaab</div>
            </div>
          </div>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-0.5">
          <NavLinks />
        </nav>
        <div className="px-4 py-4 border-t border-gray-100">
          <div className="text-xs text-gray-700 font-medium truncate mb-1">{orgName}</div>
          <div className="text-xs text-green-600 mb-3">Free Plan</div>
          <button onClick={logout} className="text-xs text-gray-400 hover:text-red-500">Sign out →</button>
        </div>
      </aside>
    </>
  );
}
