"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { LayoutGrid, List, Plus, Search } from "lucide-react";
import { api, Incident, wsUrl } from "@/lib/api";
import { Shell } from "@/components/Shell";

const statuses = ["open", "investigating", "mitigated", "resolved"];

export default function IncidentsPage() {
  const [items, setItems] = useState<Incident[]>([]);
  const [q, setQ] = useState("");
  const [view, setView] = useState<"list" | "board">("board");
  const [severity, setSeverity] = useState("");
  async function load() {
    const params = new URLSearchParams({ limit: "50" });
    if (q) params.set("q", q);
    if (severity) params.set("severity", severity);
    const data = await api<{ items: Incident[] }>(`/incidents?${params}`);
    setItems(data.items);
  }
  useEffect(() => { load(); }, [severity]);
  useEffect(() => {
    const ws = new WebSocket(wsUrl(["global"]));
    ws.onmessage = () => load();
    return () => ws.close();
  }, []);
  const columns = useMemo(() => statuses.map((status) => ({ status, items: items.filter((item) => item.status === status) })), [items]);
  return (
    <Shell>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">Incidents</h1>
        <button className="btn btn-primary"><Plus className="h-4 w-4" /> New</button>
      </div>
      <div className="panel mb-4 flex flex-wrap items-center gap-2 p-3">
        <div className="relative min-w-64 flex-1"><Search className="absolute left-2 top-2.5 h-4 w-4 text-slate-500" /><input className="input pl-8" placeholder="Search incidents" value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && load()} /></div>
        <select className="input w-36" value={severity} onChange={(e) => setSeverity(e.target.value)}><option value="">Severity</option><option>sev1</option><option>sev2</option><option>sev3</option><option>sev4</option></select>
        <button className="btn" onClick={() => setView(view === "board" ? "list" : "board")}>{view === "board" ? <List className="h-4 w-4" /> : <LayoutGrid className="h-4 w-4" />} {view}</button>
      </div>
      {view === "board" ? (
        <div className="grid gap-4 xl:grid-cols-4">
          {columns.map((column) => <section key={column.status} className="min-h-96 rounded-md border border-line bg-field p-3"><h2 className="mb-3 text-sm font-bold uppercase tracking-normal">{column.status} ({column.items.length})</h2><div className="space-y-3">{column.items.map((item) => <IncidentCard key={item._id} item={item} />)}</div></section>)}
        </div>
      ) : (
        <div className="panel divide-y divide-line">{items.map((item) => <IncidentRow key={item._id} item={item} />)}</div>
      )}
    </Shell>
  );
}

function IncidentCard({ item }: { item: Incident }) {
  return <Link href={`/incidents/${item._id}`} className="block rounded-md border border-line bg-white p-3 hover:border-accent"><div className="font-semibold">{item.title}</div><div className="mt-2 flex gap-2 text-xs"><span className="rounded bg-field px-2 py-1">{item.severity}</span><span className="rounded bg-field px-2 py-1">{item.service}</span></div></Link>;
}

function IncidentRow({ item }: { item: Incident }) {
  return <Link href={`/incidents/${item._id}`} className="grid gap-2 p-3 text-sm hover:bg-field md:grid-cols-[1fr_100px_130px_120px]"><span className="font-semibold">{item.title}</span><span>{item.severity}</span><span>{item.status}</span><span>{item.service}</span></Link>;
}
