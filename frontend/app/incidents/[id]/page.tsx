"use client";

import { useEffect, useState } from "react";
import { Bot, Check, MessageSquare, Play, Plus, X } from "lucide-react";
import { api, Incident, wsUrl } from "@/lib/api";
import { Shell } from "@/components/Shell";

export default function IncidentDetail({ params }: { params: { id: string } }) {
  const [incident, setIncident] = useState<Incident | null>(null);
  const [comment, setComment] = useState("");
  const [task, setTask] = useState("");
  async function load() { setIncident(await api<Incident>(`/incidents/${params.id}`)); }
  useEffect(() => { load(); }, [params.id]);
  useEffect(() => {
    const ws = new WebSocket(wsUrl([`incident:${params.id}`]));
    ws.onmessage = () => load();
    return () => ws.close();
  }, [params.id]);
  if (!incident) return <Shell><div>Loading...</div></Shell>;
  async function patch(update: any) { await api(`/incidents/${params.id}`, { method: "PATCH", body: JSON.stringify(update) }); await load(); }
  async function addComment(e: React.FormEvent) { e.preventDefault(); await api(`/incidents/${params.id}/comments`, { method: "POST", body: JSON.stringify({ body: comment }) }); setComment(""); await load(); }
  async function addTask(e: React.FormEvent) { e.preventDefault(); await api(`/incidents/${params.id}/tasks`, { method: "POST", body: JSON.stringify({ title: task }) }); setTask(""); await load(); }
  async function runAi() { await api(`/incidents/${params.id}/ai-investigation`, { method: "POST" }); await load(); }
  async function decide(id: string, decision: "approve" | "reject") { await api(`/ai-actions/${id}/${decision}`, { method: "POST", body: JSON.stringify({ note: "" }) }); await load(); }
  const latestRun = incident.ai_runs?.[0];
  return (
    <Shell>
      <div className="grid gap-4 xl:grid-cols-[280px_1fr_330px]">
        <aside className="panel p-4">
          <h1 className="mb-3 text-xl font-bold">{incident.title}</h1>
          <label className="mb-3 block text-sm font-semibold">Status<select className="input mt-1" value={incident.status} onChange={(e) => patch({ status: e.target.value })}>{["open", "investigating", "mitigated", "resolved"].map((x) => <option key={x}>{x}</option>)}</select></label>
          <label className="mb-3 block text-sm font-semibold">Severity<select className="input mt-1" value={incident.severity} onChange={(e) => patch({ severity: e.target.value })}>{["sev1", "sev2", "sev3", "sev4"].map((x) => <option key={x}>{x}</option>)}</select></label>
          <label className="block text-sm font-semibold">Summary<textarea className="input mt-1 min-h-36" value={incident.summary} onChange={(e) => setIncident({ ...incident, summary: e.target.value })} onBlur={(e) => patch({ summary: e.target.value })} /></label>
        </aside>
        <section className="space-y-4">
          <form onSubmit={addComment} className="panel p-4">
            <div className="mb-2 flex items-center gap-2 font-bold"><MessageSquare className="h-4 w-4" /> Comments</div>
            <textarea className="input min-h-20" value={comment} onChange={(e) => setComment(e.target.value)} />
            <button className="btn mt-2"><Plus className="h-4 w-4" /> Add comment</button>
          </form>
          <form onSubmit={addTask} className="panel p-4">
            <div className="mb-2 font-bold">Tasks</div>
            <div className="flex gap-2"><input className="input" value={task} onChange={(e) => setTask(e.target.value)} /><button className="btn"><Plus className="h-4 w-4" /></button></div>
            <div className="mt-3 space-y-2">{incident.tasks?.map((t) => <div className="rounded border border-line p-2 text-sm" key={t._id}>{t.title} <span className="text-slate-500">({t.status})</span></div>)}</div>
          </form>
          <section className="panel p-4"><div className="mb-2 font-bold">Timeline</div><div className="space-y-2">{incident.activities?.map((a) => <div className="border-t border-line pt-2 text-sm" key={a._id}>{a.message}</div>)}</div></section>
        </section>
        <aside className="panel p-4">
          <div className="mb-3 flex items-center justify-between"><div className="flex items-center gap-2 font-bold"><Bot className="h-4 w-4" /> AI Investigation</div><button className="btn btn-primary" onClick={runAi}><Play className="h-4 w-4" /> Run</button></div>
          {latestRun && <div className="rounded border border-line bg-field p-3 text-sm"><div className="font-semibold">Status: {latestRun.status}</div><p className="mt-2">{latestRun.output?.summary}</p><p className="mt-2 text-slate-700">{latestRun.output?.likely_cause}</p></div>}
          <div className="mt-4 space-y-2">
            {incident.pending_actions?.map((a) => <div key={a._id} className="rounded border border-line p-3 text-sm"><div className="font-semibold">{a.tool}</div><pre className="my-2 whitespace-pre-wrap rounded bg-field p-2 text-xs">{JSON.stringify(a.args, null, 2)}</pre><div className="flex gap-2"><button className="btn btn-primary" onClick={() => decide(a._id, "approve")}><Check className="h-4 w-4" /> Approve</button><button className="btn" onClick={() => decide(a._id, "reject")}><X className="h-4 w-4" /> Reject</button></div></div>)}
          </div>
        </aside>
      </div>
    </Shell>
  );
}
