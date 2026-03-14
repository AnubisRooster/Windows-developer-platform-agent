type Status = 'healthy' | 'connected' | 'ok' | 'error' | 'unknown';

interface StatusCardProps {
  name: string;
  status: Status;
  details?: string;
}

function statusDotClass(status: Status): string {
  switch (status?.toLowerCase?.()) {
    case 'healthy':
    case 'connected':
    case 'ok':
      return 'status-dot-healthy';
    case 'error':
      return 'status-dot-error';
    default:
      return 'status-dot-unknown';
  }
}

export default function StatusCard({ name, status, details }: StatusCardProps) {
  const dotClass = statusDotClass(status);

  return (
    <div className="card">
      <div className="flex items-start gap-3">
        <span className={`mt-1.5 ${dotClass}`} aria-hidden />
        <div className="min-w-0 flex-1">
          <h3 className="font-medium text-white">{name}</h3>
          <p className="mt-0.5 text-sm text-slate-400 capitalize">{status}</p>
          {details && (
            <p className="mt-1 text-xs text-slate-500">{details}</p>
          )}
        </div>
      </div>
    </div>
  );
}
