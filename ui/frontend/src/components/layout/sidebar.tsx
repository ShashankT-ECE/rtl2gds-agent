'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Layout,
  Cpu,
  Brain,
  History,
  Activity,
  ExternalLink,
  BookOpen,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useUIStore } from '@/stores/ui-store';
import { cn } from '@/lib/utils';

interface NavItem {
  href: string;
  label: string;
  icon: typeof Layout;
  exact?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: Layout, exact: true },
  { href: '/benchmarks', label: 'Benchmarks', icon: Cpu },
  { href: '/skills', label: 'Skills', icon: Brain },
  { href: '/jobs', label: 'Jobs', icon: History },
  { href: '/status', label: 'Status', icon: Activity },
];

interface SidebarProps {
  onClose?: () => void;
}

export function Sidebar({ onClose }: SidebarProps) {
  const pathname = usePathname();
  const sidebarExpanded = useUIStore((s) => s.sidebarExpanded);
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed);

  const isActive = (item: NavItem) => {
    if (item.exact) return pathname === item.href;
    return pathname.startsWith(item.href);
  };

  return (
    <aside
      className={cn(
        'fixed top-12 left-0 bottom-0 z-30 bg-silicon-900 border-r border-silicon-700 flex flex-col transition-all duration-300',
        sidebarExpanded && !sidebarCollapsed ? 'w-56' : 'w-16'
      )}
    >
      {/* Close button (mobile overlay) */}
      {onClose && (
        <div className="absolute top-2 right-2 lg:hidden">
          <Button variant="ghost" size="icon" className="h-8 w-8 text-silicon-400" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Logo */}
      <Link href="/dashboard" className="flex items-center gap-3 px-4 h-14 border-b border-silicon-700 shrink-0">
        <div className="h-8 w-8 rounded bg-copper-500/10 border border-copper-500/30 flex items-center justify-center shrink-0">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-copper-500">
            <rect x="2" y="2" width="20" height="20" rx="2" />
            <path d="M7 7h10M7 12h10M7 17h6" />
          </svg>
        </div>
        {(sidebarExpanded && !sidebarCollapsed) && (
          <span className="text-sm font-bold text-silicon-100 tracking-tight">
            RTL2GDS
          </span>
        )}
      </Link>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-2 space-y-1">
        {NAV_ITEMS.map((item) => {
          const active = isActive(item);
          const Icon = item.icon;
          const showLabel = sidebarExpanded && !sidebarCollapsed;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-all duration-200 group',
                active
                  ? 'bg-copper-500/10 text-copper-500 border-l-[3px] border-copper-500'
                  : 'text-silicon-400 hover:text-silicon-200 hover:bg-silicon-800 border-l-[3px] border-transparent'
              )}
              title={!showLabel ? item.label : undefined}
            >
              <Icon className={cn('h-5 w-5 shrink-0', active ? 'text-copper-500' : 'text-silicon-500 group-hover:text-silicon-300')} />
              {showLabel && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className={cn(
        'border-t border-silicon-700 py-3',
        sidebarExpanded && !sidebarCollapsed ? 'px-4' : 'px-2'
      )}>
        {(sidebarExpanded && !sidebarCollapsed) ? (
          <div className="space-y-1">
            <div className="text-2xs text-silicon-600 mb-2">v0.3.0</div>
            <a
              href="https://github.com/ShashankT-ECE/rtl-to-gds-agent"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-xs text-silicon-500 hover:text-silicon-300 transition-colors"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              GitHub
            </a>
            <a
              href="/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-xs text-silicon-500 hover:text-silicon-300 transition-colors"
            >
              <BookOpen className="h-3.5 w-3.5" />
              API Docs
            </a>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <a
              href="https://github.com/ShashankT-ECE/rtl-to-gds-agent"
              target="_blank"
              rel="noopener noreferrer"
              className="text-silicon-500 hover:text-silicon-300 transition-colors"
              title="GitHub"
            >
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>
        )}
      </div>
    </aside>
  );
}
