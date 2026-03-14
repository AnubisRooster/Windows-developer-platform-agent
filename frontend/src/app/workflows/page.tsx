'use client';

import { useEffect, useState } from 'react';
import { fetchWorkflows, type Workflow } from '@/lib/api';

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchWorkflows()
      .then(setWorkflows)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load workflows'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-white">Workflows</h1>
        <p className="text-slate-400">Loading…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-white">Workflows</h1>
        <p className="text-accent-red">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Workflows</h1>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {workflows.length === 0 ? (
          <p className="col-span-full text-slate-500">No workflows</p>
        ) : (
          workflows.map((wf) => (
            <div key={wf.id} className="card flex flex-col gap-2">
              <div className="flex items-start justify-between">
                <h3 className="font-medium text-white">{wf.name}</h3>
                <span
                  className={`badge ${wf.enabled ? 'badge-success' : 'badge-neutral'}`}
                >
                  {wf.enabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
              <p className="text-sm text-slate-400">
                Trigger: <span className="text-slate-300">{wf.trigger}</span>
              </p>
              {wf.description && (
                <p className="text-sm text-slate-500">{wf.description}</p>
              )}
              <p className="mt-auto text-xs text-slate-500">
                {Array.isArray(wf.actions) ? wf.actions.length : 0} action(s)
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
