'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navItems = [
  { href: '/', label: 'Status', section: 'core' },
  { href: '/logs', label: 'Logs', section: 'core' },
  { href: '/events', label: 'Events', section: 'core' },
  { href: '/workflows', label: 'Workflows', section: 'core' },
  { href: '/workflow-runs', label: 'Runs', section: 'core' },
  { href: '/tools', label: 'Tools', section: 'core' },
  { href: '/conversations', label: 'Conversations', section: 'core' },
  { href: '/chat', label: 'Chat', section: 'core' },
  { href: '/feeds', label: 'Feeds & Email', section: 'integrations' },
  { href: '/markets', label: 'Markets', section: 'markets' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-border bg-surface-800">
      <div className="border-b border-border px-4 py-5">
        <h1 className="text-lg font-semibold text-white">Claw Agent</h1>
      </div>
      <nav className="flex-1 overflow-y-auto p-2">
        {navItems.map((item, idx) => {
          const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
          const prevSection = idx > 0 ? navItems[idx - 1].section : null;
          const showDivider = prevSection && prevSection !== item.section;
          return (
            <div key={item.href}>
              {showDivider && <div className="my-2 border-t border-border" />}
              <Link
                href={item.href}
                className={`block rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-surface-700 text-white'
                    : 'text-slate-400 hover:bg-surface-700/50 hover:text-slate-200'
                }`}
              >
                {item.label}
              </Link>
            </div>
          );
        })}
      </nav>
    </aside>
  );
}
