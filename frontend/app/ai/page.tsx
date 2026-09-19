"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ArrowUpRight, Bot, Check, Clock3, Play, ShieldAlert, Sparkles, X } from "lucide-react";
import { api, Incident } from "@/lib/api";
import { Shell } from "@/components/Shell";

type AiAction = {
  _id: string;
  incident_id: string;
  tool: string;
  args: Record<string, unknown>;
  status: string;
};

type AiRun = {
  _id: string;
  incident_id: string;
  status: string;
  output?: {
    summary?: string;
    likely_cause?: string;
    severity_suggestion?: string;
  };
};

type AiIncident = Incident & {
  ai_runs?: AiRun[];
  pending_actions?: AiAction[];
};

export default function AiOperationsPage() {
  const [incidents, setIncidents] = useState<AiIncident[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<string | null>(null);
  const [message, setMessage] = useState("");

  async function load() {
    setLoading(true);
    try {
      const result = await api<{ items: Incident[] }>("/incidents?limit=50&sort=-updated_at");
      const candidates = result.items.filter((item) => item.status !== "resolved").slice(0, 20);
      const details = await Promise.all(candidates.map((item) => api<AiIncident>(`/incidents/${item._id}`)));
      setIncidents(details);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function runInvestigation(id: string) {
    setRunning(id);
    setMessage("");
    try {
      await api(`/incidents/${id}/ai-investigation`, { method: "POST" });
      setMessage("Investigation queued. The findings will appear here as soon as the worker completes.");
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to queue investigation");
    } finally {
      setRunning(null);
    }
  }

  async function decide(action: AiAction, decision: "approve" | "reject") {
    await api(`/ai-actions/${action._id}/${decision}`, { method: "POST", body: JSON.stringify({ note: "" }) });
    await load();
  }

  const actions = useMemo(() => incidents.flatMap((incident) => (incident.pending_actions || []).map((action) => ({ action, incident }))), [incidents]);
  const runs = incidents.flatMap((incident) => (incident.ai_runs || []).map((run) => ({ run, incident })));
  const completed = runs.filter(({ run }) => run.status === "completed");
  const active = incidents.filter((incident) => incident.status !== "resolved");

  return (
    <Shell>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-2 flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-accent"><Sparkles className="h-4 w-4" /> AI Operations</div>
          <h1 className="text-3xl font-bold tracking-tight">Investigation command center</h1>
          <p className="mt-1 max-w-2xl text-sm text-slate-600">Prioritize noisy incidents, review machine findings, and approve operational actions from one place.</p>
        </div>
        <button className="btn" onClick={load}><Clock3 className="h-4 w-4" /> Refresh queue</button>
      </div>

      {message && <div className="mb-4 rounded-md border border-[#bcebd4] bg-[#effbf5] px-4 py-3 text-sm text-[#24543f]">{message}</div>}

      <div className="mb-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric icon={<ShieldAlert />} label="Active incidents" value={active.length} />
        <Metric icon={<Bot />} label="Investigations" value={runs.length} />
        <Metric icon={<Check />} label="Completed findings" value={completed.length} />
        <Metric icon={<Clock3 />} label="Awaiting approval" value={actions.length} />
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.35fr_1fr]">
        <section className="panel overflow-hidden">
          <div className="flex items-center justify-between border-b border-line px-4 py-3"><div><h2 className="font-bold">Investigation queue</h2><p className="text-xs text-slate-500">Open incidents are ranked by their latest update.</p></div><Bot className="h-5 w-5 text-accent" /></div>
          {loading ? <div className="p-5 text-sm text-slate-500">Loading AI queue...</div> : <div className="divide-y divide-line">{incidents.map((incident) => {
            const latest = incident.ai_runs?.[0];
            const hasPending = (incident.pending_actions?.length || 0) > 0;
            return <div className="flex flex-wrap items-center justify-between gap-3 p-4" key={incident._id}>
              <div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><Link className="font-semibold hover:text-accent" href={`/incidents/${incident._id}`}>{incident.title}</Link><span className="rounded bg-field px-2 py-1 text-xs font-semibold">{incident.severity}</span>{hasPending && <span className="rounded bg-[#fff3d6] px-2 py-1 text-xs font-semibold text-[#795500]">Approval needed</span>}</div><div className="mt-1 text-xs text-slate-500">{incident.service} · {latest ? `Last run ${latest.status}` : "Not investigated yet"}</div></div>
              <button className="btn btn-primary" disabled={running === incident._id || latest?.status === "queued" || latest?.status === "running"} onClick={() => runInvestigation(incident._id)}>{latest?.status === "queued" || latest?.status === "running" ? <Clock3 className="h-4 w-4" /> : <Play className="h-4 w-4" />}{running === incident._id ? "Queueing" : latest?.status === "queued" || latest?.status === "running" ? "Running" : "Investigate"}</button>
            </div>;
          })}</div>}
        </section>

        <section className="panel overflow-hidden"><div className="border-b border-line px-4 py-3"><h2 className="font-bold">Human approval gate</h2><p className="text-xs text-slate-500">AI never executes these changes without an operator.</p></div>{actions.length === 0 ? <div className="p-5 text-sm text-slate-500">No pending actions. Run an investigation to generate recommendations.</div> : <div className="space-y-3 p-4">{actions.map(({ action, incident }) => <div className="rounded-md border border-[#f0d8a2] bg-[#fffaf0] p-3" key={action._id}><div className="flex items-start justify-between gap-2"><div><Link className="text-sm font-bold hover:text-accent" href={`/incidents/${incident._id}`}>{incident.title}</Link><div className="mt-1 text-xs font-semibold uppercase text-[#795500]">{action.tool.replaceAll("_", " ")}</div></div><ArrowUpRight className="h-4 w-4 text-[#795500]" /></div><pre className="my-3 whitespace-pre-wrap rounded bg-white p-2 text-xs">{JSON.stringify(action.args, null, 2)}</pre><div className="flex gap-2"><button className="btn btn-primary" onClick={() => decide(action, "approve")}><Check className="h-4 w-4" /> Approve</button><button className="btn" onClick={() => decide(action, "reject")}><X className="h-4 w-4" /> Reject</button></div></div>)}</div>}</section>
      </div>

      <section className="panel mt-5 overflow-hidden"><div className="border-b border-line px-4 py-3"><h2 className="font-bold">Latest findings</h2></div>{completed.length === 0 ? <div className="p-5 text-sm text-slate-500">Completed investigation summaries will appear here.</div> : <div className="divide-y divide-line">{completed.slice(0, 6).map(({ run, incident }) => <div className="p-4" key={run._id}><div className="mb-1 flex flex-wrap items-center gap-2"><Link className="font-semibold hover:text-accent" href={`/incidents/${incident._id}`}>{incident.title}</Link><span className="text-xs text-slate-500">Suggested severity: {run.output?.severity_suggestion || "unchanged"}</span></div><p className="text-sm text-slate-700">{run.output?.summary}</p><p className="mt-1 text-xs text-slate-500">Likely cause: {run.output?.likely_cause}</p></div>)}</div>}</section>
    </Shell>
  );
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return <div className="panel p-4"><div className="mb-3 flex h-8 w-8 items-center justify-center rounded-md bg-[#effbf5] text-[#2e8060]">{icon}</div><div className="text-2xl font-bold">{value}</div><div className="text-sm text-slate-600">{label}</div></div>;
}
