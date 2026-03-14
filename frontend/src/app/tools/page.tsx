'use client';

import { useEffect, useState } from 'react';
import { fetchTools, type Tool } from '@/lib/api';

export default function ToolsPage() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTools()
      .then(setTools)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load tools'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-white">Tools</h1>
        <p className="text-slate-400">Loading…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-white">Tools</h1>
        <p className="text-accent-red">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Tools</h1>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tools.length === 0 ? (
          <p className="col-span-full text-slate-500">No tools</p>
        ) : (
          tools.map((tool) => (
            <div key={tool.id} className="card flex flex-col gap-3">
              <h3 className="font-medium text-white">{tool.name}</h3>
              {tool.description && (
                <p className="text-sm text-slate-400">{tool.description}</p>
              )}
              {Array.isArray(tool.parameters) && tool.parameters.length > 0 && (
                <div className="mt-auto">
                  <p className="text-xs font-medium text-slate-500">Parameters</p>
                  <ul className="mt-1 space-y-1">
                    {tool.parameters.map((p) => (
                      <li key={p.name} className="flex items-baseline gap-2 text-xs">
                        <code className="rounded bg-surface-700 px-1.5 py-0.5 text-slate-300">
                          {p.name}
                        </code>
                        {p.type && (
                          <span className="text-slate-500">({p.type})</span>
                        )}
                        {p.description && (
                          <span className="text-slate-500">— {p.description}</span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
