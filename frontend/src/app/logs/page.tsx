'use client';

import { useEffect, useState } from 'react';
import { fetchLogs, type LogEntry } from '@/lib/api';

type LevelFilter = 'all' | 'info' | 'warning' | 'error';

function logLineColor(level: string): string {
  const l = (level ?? '').toLowerCase();
  if (l === 'error') return 'text-accent-red';
  if (l === 'warning' || l === 'warn') return 'text-accent-amber';
  if (l === 'info') return 'text-accent-blue';
  return 'text-slate-400';
}

export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [level, setLevel] = useState<LevelFilter>('all');

  const load = () => {
    setLoading(true);
    fetchLogs(level === 'all' ? undefined : level, 100)
      .then(setLogs)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load logs'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, [level]);

  const formatLine = (entry: LogEntry): string => {
    const ts = entry.timestamp ?? '';
    const lvl = (entry.level ?? '').toUpperCase();
    const msg = entry.message ?? '';
    const extra = entry.extra != null ? ` ${JSON.stringify(entry.extra)}` : '';
    return `[${ts}] ${lvl} ${msg}${extra}`;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-white">Logs</h1>
        <div className="flex items-center gap-3">
          <label htmlFor="level" className="text-sm text-slate-400">Level</label>
          <select
            id="level"
            value={level}
            onChange={(e) => setLevel(e.target.value as LevelFilter)}
            className="rounded-md border border-border bg-surface-800 px-3 py-2 text-sm text-white focus:border-accent-blue focus:outline-none focus:ring-1 focus:ring-accent-blue"
          >
            <option value="all">All</option>
            <option value="info">Info</option>
            <option value="warning">Warning</option>
            <option value="error">Error</option>
          </select>
          <span className="text-xs text-slate-500">Auto-refresh every 5s</span>
        </div>
      </div>

      {error && <p className="text-accent-red">{error}</p>}

      <div className="rounded-lg border border-border bg-surface-900 p-4 font-mono text-sm">
        {loading && logs.length === 0 ? (
          <p className="text-slate-500">Loading…</p>
        ) : logs.length === 0 ? (
          <p className="text-slate-500">No logs</p>
        ) : (
          <div className="max-h-[70vh] overflow-y-auto">
            {logs.map((entry, i) => (
              <div
                key={i}
                className={`border-b border-border/50 py-1 ${logLineColor(entry.level)}`}
              >
                {formatLine(entry)}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
