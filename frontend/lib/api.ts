export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Incident = {
  _id: string;
  title: string;
  summary: string;
  service: string;
  status: string;
  severity: string;
  team_id?: string;
  assignee_id?: string;
  updated_at: string;
  comments?: any[];
  tasks?: any[];
  activities?: any[];
  ai_runs?: any[];
  pending_actions?: any[];
};

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers || {})
    },
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export function wsUrl(rooms: string[]) {
  const base = API_URL.replace(/^http/, "ws");
  return `${base}/ws?rooms=${encodeURIComponent(rooms.join(","))}`;
}
