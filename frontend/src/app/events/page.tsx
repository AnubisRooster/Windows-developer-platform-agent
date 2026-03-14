'use client';

import { useEffect, useState } from 'react';
import { fetchEvents, type Event } from '@/lib/api';

function payloadPreview(payload: unknown): string {
  if (payload == null) return '-';
  try {
    const s = typeof payload === 'string' ? payload : JSON.stringify(payload);
    return s.length > 80 ? `${s.slice(0, 80)}…` : s;
  } catch {
    return '-';
  }
}

export default function EventsPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    fetchEvents(50)
      .then(setEvents)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load events'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  if (loading && events.length === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-white">Events</h1>
        <p className="text-slate-400">Loading…</p>
      </div>
    );
  }

  if (error && events.length === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-white">Events</h1>
        <p className="text-accent-red">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Events</h1>
        <span className="text-xs text-slate-500">Auto-refresh every 5s</span>
      </div>

      <div className="overflow-x-auto rounded-lg border border-border bg-surface-800">
        <table className="min-w-full divide-y divide-border">
          <thead>
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-slate-400">Time</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-slate-400">Source</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-slate-400">Type</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-slate-400">Payload Preview</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {events.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-slate-500">
                  No events
                </td>
              </tr>
            ) : (
              events.map((evt, i) => (
                <tr key={evt.id ?? i} className="hover:bg-surface-700/50">
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-300">{evt.time ?? '-'}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-300">{evt.source ?? '-'}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-300">{evt.type ?? '-'}</td>
                  <td className="max-w-xs truncate px-4 py-3 font-mono text-xs text-slate-400">
                    {payloadPreview(evt.payload)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
