"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { storeToken } from "@/lib/session";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface SeedMember {
  id: string;
  display_name: string;
  is_admin: boolean;
}

interface SeedGroup {
  id: string;
  name: string;
  invite_token: string;
  status: string;
  members: SeedMember[];
}

export function DevSeedLinks() {
  const router = useRouter();
  const [groups, setGroups] = useState<SeedGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [loggingIn, setLoggingIn] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/v1/dev/seed-info`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (Array.isArray(data)) setGroups(data as SeedGroup[]);
      })
      .catch(() => {
        // Dev endpoint not available — that's fine in production
      })
      .finally(() => setLoading(false));
  }, []);

  async function loginAsMember(member: SeedMember, groupId: string) {
    setLoggingIn(member.id);
    try {
      const res = await fetch(`${API_URL}/api/v1/dev/login/${member.id}`, {
        method: "POST",
        credentials: "include",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as { group_id: string; token: string };
      storeToken(data.group_id, data.token);
      router.push(`/groups/${data.group_id}`);
    } catch (err) {
      console.error("[DevSeedLinks] Login failed", err);
    } finally {
      setLoggingIn(null);
    }
  }

  if (loading) {
    return <p className="text-xs text-slate-400">Loading seed data...</p>;
  }

  if (groups.length === 0) {
    return (
      <p className="text-xs text-slate-500">
        No seeded groups found. Run{" "}
        <code className="bg-slate-100 px-1.5 py-0.5 rounded">
          docker compose run --rm -v &quot;$(pwd)/backend/seed.py:/app/seed.py:ro&quot; backend python seed.py
        </code>{" "}
        to populate the database.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-xs text-amber-700">
        Click any name to instantly log in as that member — no join flow needed.
      </p>
      {groups.map((group) => (
        <div key={group.id} className="border border-amber-100 rounded-lg p-3 bg-white">
          <div className="flex items-center gap-2 mb-2.5">
            <p className="text-xs font-semibold text-slate-700">{group.name}</p>
            {group.status === "archived" && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-slate-100 text-slate-500">
                archived
              </span>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {group.members.map((member) => (
              <button
                key={member.id}
                onClick={() => loginAsMember(member, group.id)}
                disabled={loggingIn === member.id}
                className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg bg-amber-50 border border-amber-200 hover:bg-amber-100 text-amber-900 transition-colors disabled:opacity-50 disabled:cursor-wait font-medium"
              >
                {loggingIn === member.id ? (
                  <span className="w-3 h-3 border border-amber-400 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <span className="text-amber-600">{member.is_admin ? "★" : "·"}</span>
                )}
                {member.display_name}
              </button>
            ))}
          </div>
          <p className="text-xs text-slate-400 mt-2">
            or join fresh:{" "}
            <a
              href={`/join/${group.invite_token}`}
              className="underline hover:text-slate-600"
            >
              /join/{group.invite_token.slice(0, 8)}…
            </a>
          </p>
        </div>
      ))}
    </div>
  );
}
