'use client';

import { useEffect, useState } from 'react';
import { fetchStatus, type StatusResponse } from '@/lib/api';
import StatusCard from '@/components/StatusCard';
import ModelSelector from '@/components/ModelSelector';

type StatusValue = 'healthy' | 'connected' | 'ok' | 'error' | 'unknown';

function toStatus(v: string | undefined): StatusValue {
  const s = (v ?? '').toLowerCase();
  if (['healthy', 'connected', 'ok'].includes(s)) return s as 'healthy' | 'connected' | 'ok';
  if (s === 'error') return 'error';
  return 'unknown';
}

const integrationNames: Record<string, string> = {
  slack: 'Slack',
  github: 'GitHub',
  jira: 'Jira',
  jenkins: 'Jenkins',
  confluence: 'Confluence',
  gmail: 'Gmail',
  outlook: 'Outlook',
  zoho_mail: 'Zoho Mail',
  x: 'X (Twitter)',
  linkedin: 'LinkedIn',
};

export default function StatusPage() {
  const [data, setData] = useState<StatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStatus()
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load status'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-white">Status</h1>
        <p className="text-slate-400">Loading…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-white">Status</h1>
        <p className="text-accent-red">{error}</p>
      </div>
    );
  }

  const integrations = data?.integrations ?? {};
  const integrationOrder = ['Slack', 'GitHub', 'Jira', 'Jenkins', 'Confluence', 'Gmail', 'Outlook', 'Zoho Mail', 'X (Twitter)', 'LinkedIn'];
  const sortedIntegrations = Object.entries(integrations).sort(
    (a, b) => integrationOrder.indexOf(integrationNames[a[0]] ?? a[0]) - integrationOrder.indexOf(integrationNames[b[0]] ?? b[0])
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Status</h1>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {data?.ironclaw && (
          <StatusCard
            name="IronClaw"
            status={toStatus(data.ironclaw.status)}
            details={data.ironclaw.details}
          />
        )}
        {data?.database && (
          <StatusCard
            name="Database"
            status={toStatus(data.database.status)}
            details={data.database.details}
          />
        )}
        {sortedIntegrations.map(([key, val]) => (
          <StatusCard
            key={key}
            name={integrationNames[key] ?? key}
            status={toStatus(val.status)}
            details={val.details}
          />
        ))}
      </div>

      {(!data?.ironclaw && !data?.database && Object.keys(integrations).length === 0) && (
        <p className="text-slate-500">No status data available.</p>
      )}

      <section>
        <h2 className="mb-3 text-lg font-semibold text-white">Model Configuration</h2>
        <ModelSelector />
      </section>
    </div>
  );
}
