"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Activity, Bot, LayoutDashboard, ListChecks, LogOut, Users } from "lucide-react";
import { api } from "@/lib/api";

const nav = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/incidents", label: "Incidents", icon: ListChecks },
  { href: "/ai", label: "AI Operations", icon: Bot },
  { href: "/admin", label: "Users & Teams", icon: Users }
];

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  async function logout() {
    await api("/auth/logout", { method: "POST" });
    router.refresh();
  }
  return (
    <div className="min-h-screen lg:flex">
      <aside className="border-b border-line bg-ink text-white lg:min-h-screen lg:w-64 lg:border-b-0 lg:border-r">
        <div className="flex h-16 items-center gap-2 px-5 text-lg font-bold">
          <Activity className="h-5 w-5 text-[#8fd6b5]" /> MonkLens
        </div>
        <nav className="flex gap-1 overflow-x-auto px-3 pb-3 lg:block">
          {nav.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link key={item.href} href={item.href} className={`mb-1 flex items-center gap-2 rounded-md px-3 py-2 text-sm font-semibold ${active ? "bg-white text-ink" : item.href === "/ai" ? "text-[#bcebd4] hover:bg-slate-700" : "text-slate-200 hover:bg-slate-700"}`}>
                <Icon className="h-4 w-4" /> {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <main className="min-w-0 flex-1">
        <header className="flex h-16 items-center justify-between border-b border-line bg-white px-5">
          <div className="text-sm font-semibold text-slate-600">admin@monklens.dev</div>
          <button className="btn" onClick={logout} title="Log out"><LogOut className="h-4 w-4" /> Logout</button>
        </header>
        <div className="p-4 lg:p-6">{children}</div>
      </main>
    </div>
  );
}
