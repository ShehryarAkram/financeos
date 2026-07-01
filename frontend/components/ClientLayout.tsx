"use client";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [checked, setChecked] = useState(false);
  const isLoginPage = pathname === "/login";

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token && !isLoginPage) {
      router.replace("/login");
    } else {
      setChecked(true);
    }
  }, [pathname]);

  if (!checked && !isLoginPage) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-gray-400 animate-pulse">Loading...</div>
    </div>
  );

  if (isLoginPage) return <>{children}</>;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
