'use client';

import { useEffect, useState } from 'react';
import { fetchWorkflowRuns, type WorkflowRun } from '@/lib/api';

function statusBadge(status: string) {
  const s = (status ?? '').toLowerCase();
  if (s === 'success') return <span className="badge-success">Success</span>;
  if (s === 'failed') return <span className="badge-error">Failed</span>;
  if (s === 'running') return <span className="badge-info">Running</span>;
  return <span className="badge-neutral">{status ?? 'Unknown'}</span>;
}

function formatDuration(ms: number | undefined): string {
  if (ms == null) return '-';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

export default function WorkflowRunsPage() {
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchWorkflowRuns(50)
      .then(setRuns)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load runs'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-white">Workflow Runs</h1>
        <p className="text-slate-400">Loading…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-white">Workflow Runs</h1>
        <p className="text-accent-red">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Workflow Runs</h1>

      <div className="overflow-x-auto rounded-lg border border-border bg-surface-800">
        <table className="min-w-full divide-y divide-border">
          <thead>
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-slate-400">Run ID</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-slate-400">Workflow</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-slate-400">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-slate-400">Started</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-slate-400">Duration</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {runs.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                  No runs
                </td>
              </tr>
            ) : (
              runs.map((run) => (
                <tr key={run.id} className="hover:bg-surface-700/50">
                  <td className="whitespace-nowrap px-4 py-3 font-mono text-sm text-slate-300">{run.id}</td>
                  <td className="px-4 py-3 text-sm text-slate-300">{run.workflow_name ?? run.workflow_id ?? '-'}</td>
                  <td className="whitespace-nowrap px-4 py-3">{statusBadge(run.status)}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-300">{run.started_at ?? '-'}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-300">
                    {formatDuration(run.duration_ms)}
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
