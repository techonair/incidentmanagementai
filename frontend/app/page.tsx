"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Brain, CheckCircle2, Flame } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "@/lib/api";
import { Shell } from "@/components/Shell";

function Login({ onDone }: { onDone: () => void }) {
  const [email, setEmail] = useState("admin@purplelens.dev");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
      onDone();
    } catch (err: any) {
      setError(err.message);
    }
  }
  return (
    <main className="grid min-h-screen place-items-center bg-[#eef2f6] p-4">
      <form onSubmit={submit} className="panel w-full max-w-sm p-5">
        <div className="mb-5 flex items-center gap-2 text-xl font-bold"><Flame className="h-5 w-5 text-accent" /> PurpleLens</div>
        <label className="mb-3 block text-sm font-semibold">Email<input className="input mt-1" value={email} onChange={(e) => setEmail(e.target.value)} /></label>
        <label className="mb-4 block text-sm font-semibold">Password<input className="input mt-1" type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></label>
        {error && <p className="mb-3 text-sm text-danger">{error}</p>}
        <button className="btn btn-primary w-full justify-center">Login</button>
      </form>
    </main>
  );
}

export default function OverviewPage() {
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [data, setData] = useState<any>(null);
  async function load() {
    try {
      await api("/auth/me");
      setAuthed(true);
      setData(await api("/dashboard/overview"));
    } catch {
      setAuthed(false);
    }
  }
  useEffect(() => { load(); }, []);
  if (authed === null) return <div className="p-6">Loading...</div>;
  if (!authed) return <Login onDone={load} />;
  const statusRows = (data?.by_status || []).map((x: any) => ({ name: x._id, count: x.count }));
  const severityRows = (data?.by_severity || []).map((x: any) => ({ name: x._id, count: x.count }));
  return (
    <Shell>
      <div className="mb-5 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Operations Overview</h1>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Stat icon={<AlertTriangle />} label="Open incidents" value={data?.open} />
        <Stat icon={<Flame />} label="Sev1 / Sev2" value={data?.sev1_2} />
        <Stat icon={<CheckCircle2 />} label="Aging over 24h" value={data?.aging} />
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Chart title="By Status" rows={statusRows} />
        <Chart title="By Severity" rows={severityRows} />
      </div>
      <section className="panel mt-4 p-4">
        <div className="mb-3 flex items-center gap-2 font-bold"><Brain className="h-4 w-4" /> Recent Activity</div>
        <div className="space-y-2">
          {(data?.recent_activity || []).map((item: any) => <div key={item._id} className="border-t border-line pt-2 text-sm">{item.message}</div>)}
        </div>
      </section>
    </Shell>
  );
}

function Stat({ icon, label, value }: { icon: React.ReactNode; label: string; value: any }) {
  return <div className="panel p-4"><div className="mb-2 flex h-8 w-8 items-center justify-center rounded-md bg-field text-accent">{icon}</div><div className="text-2xl font-bold">{value ?? "-"}</div><div className="text-sm text-slate-600">{label}</div></div>;
}

function Chart({ title, rows }: { title: string; rows: any[] }) {
  return <section className="panel h-72 p-4"><h2 className="mb-2 font-bold">{title}</h2><ResponsiveContainer width="100%" height="85%"><BarChart data={rows}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis allowDecimals={false} /><Tooltip /><Bar dataKey="count" fill="#6750a4" /></BarChart></ResponsiveContainer></section>;
}
