"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/dashboard", label: "Dashboard",  icon: "📊" },
  { href: "/invoices",  label: "Invoices",   icon: "📄" },
  { href: "/contacts",  label: "Contacts",   icon: "👥" },
  { href: "/udhar",     label: "Udhar Book", icon: "📒" },
  { href: "/reports",   label: "Reports",    icon: "📈" },
  { href: "/whatsapp",  label: "WA Bot Test",icon: "💬" },
];

export default function Sidebar() {
  const path = usePathname();
  return (
    <aside className="w-56 bg-white border-r border-gray-200 min-h-screen flex flex-col">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">F</div>
          <div>
            <div className="text-sm font-bold text-gray-900">FinanceOS</div>
            <div className="text-xs text-gray-400">Pakistan ka hisaab</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {links.map(l => (
          <Link key={l.href} href={l.href}
            className={`sidebar-link ${path.startsWith(l.href) ? "active" : ""}`}>
            <span>{l.icon}</span>
            <span>{l.label}</span>
          </Link>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-gray-100">
        <div className="text-xs text-gray-400">Ahmed General Store</div>
        <div className="text-xs text-green-600 font-medium">Free Plan</div>
      </div>
    </aside>
  );
}
