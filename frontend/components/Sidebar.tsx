"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

const links = [
  { href: "/dashboard", label: "Dashboard",   icon: "📊" },
  { href: "/invoices",  label: "Invoices",    icon: "📄" },
  { href: "/contacts",  label: "Contacts",    icon: "👥" },
  { href: "/udhar",     label: "Udhar Book",  icon: "📒" },
  { href: "/reports",   label: "Reports",     icon: "📈" },
  { href: "/whatsapp",  label: "WA Bot Test", icon: "💬" },
];

export default function Sidebar() {
  const path = usePathname();
  const router = useRouter();

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("org_id");
    localStorage.removeItem("dukandaar_mode");
    router.replace("/login");
  };

  const orgName = typeof window !== "undefined"
    ? (localStorage.getItem("org_name") || "Ahmed General Store")
    : "Ahmed General Store";

  return (
    <aside className="w-56 bg-white border-r border-gray-200 min-h-screen flex flex-col">
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
        {links.map(l => (
          <Link key={l.href} href={l.href}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              path.startsWith(l.href)
                ? "bg-green-50 text-green-700"
                : "text-gray-600 hover:bg-green-50 hover:text-green-700"
            }`}>
            <span>{l.icon}</span><span>{l.label}</span>
          </Link>
        ))}
      </nav>

      <div className="px-4 py-4 border-t border-gray-100">
        <div className="text-xs text-gray-700 font-medium truncate mb-1">{orgName}</div>
        <div className="text-xs text-green-600 mb-3">Free Plan</div>
        <button onClick={logout}
          className="w-full text-left text-xs text-gray-400 hover:text-red-500 transition-colors">
          Sign out →
        </button>
      </div>
    </aside>
  );
}
