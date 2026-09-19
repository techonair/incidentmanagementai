"use client";

import { useEffect, useState } from "react";
import { Shell } from "@/components/Shell";
import { api } from "@/lib/api";

export default function AdminPage() {
  const [refs, setRefs] = useState<any>({ teams: [], users: [] });
  const [workload, setWorkload] = useState<any[]>([]);
  useEffect(() => { api<any>("/admin/refs").then(setRefs); api<any[]>("/admin/workload").then(setWorkload); }, []);
  const countFor = (id: string) => workload.find((x) => x._id === id)?.count || 0;
  return (
    <Shell>
      <h1 className="mb-4 text-2xl font-bold">Users & Teams</h1>
      <div className="grid gap-4 lg:grid-cols-2">
        <section className="panel p-4"><h2 className="mb-3 font-bold">Teams</h2><div className="divide-y divide-line">{refs.teams.map((t: any) => <div className="grid grid-cols-[1fr_90px] py-2 text-sm" key={t._id}><span>{t.name}</span><span>{countFor(t._id)} open</span></div>)}</div></section>
        <section className="panel p-4"><h2 className="mb-3 font-bold">Users</h2><div className="divide-y divide-line">{refs.users.map((u: any) => <div className="grid grid-cols-[1fr_90px] py-2 text-sm" key={u._id}><span>{u.email}</span><span>{u.role}</span></div>)}</div></section>
      </div>
    </Shell>
  );
}
