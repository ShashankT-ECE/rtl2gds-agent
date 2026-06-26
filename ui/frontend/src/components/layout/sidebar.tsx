'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ExternalLink, BookOpen, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useUIStore } from '@/stores/ui-store';
import { cn } from '@/lib/utils';

interface NavItem {
  href: string;
  label: string;
  icon: string; // Material Symbols icon name
  exact?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: 'dashboard', exact: true },
  { href: '/benchmarks', label: 'Projects', icon: 'inventory_2' },
  { href: '/skills', label: 'Agents', icon: 'memory' },
  { href: '/jobs', label: 'Workflow', icon: 'account_tree' },
  { href: '/status', label: 'Status', icon: 'monitoring' },
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
        'fixed top-14 left-0 bottom-0 z-30 bg-sidebar border-r border-sidebar-border flex flex-col transition-all duration-300',
        sidebarExpanded && !sidebarCollapsed ? 'w-[280px]' : 'w-16'
      )}
    >
      {/* Close button (mobile overlay) */}
      {onClose && (
        <div className="absolute top-2 right-2 lg:hidden">
          <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Logo / Brand */}
      <Link href="/dashboard" className="flex items-center gap-3 px-4 h-14 border-b border-sidebar-border shrink-0">
        <div className="h-8 w-8 rounded bg-primary flex items-center justify-center shrink-0">
          <span className="material-symbols-outlined text-white text-[20px] icon-fill">memory</span>
        </div>
        {(sidebarExpanded && !sidebarCollapsed) && (
          <div className="flex flex-col">
            <span className="text-sm font-bold text-sidebar-foreground tracking-tight leading-tight">
              Core Engine
            </span>
            <span className="text-[10px] text-muted-foreground font-mono">v2.4.1-stable</span>
          </div>
        )}
      </Link>

      {/* New Project button */}
      {(sidebarExpanded && !sidebarCollapsed) && (
        <div className="px-3 py-3">
          <Link
            href="/projects/new"
            className="flex items-center justify-center gap-2 w-full bg-primary text-primary-foreground py-2 rounded text-[11px] font-bold tracking-wider uppercase hover:opacity-90 transition-opacity"
          >
            <span className="material-symbols-outlined text-[16px]">add</span>
            New Project
          </Link>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 py-2 px-2 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const active = isActive(item);
          const showLabel = sidebarExpanded && !sidebarCollapsed;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-sm text-sm transition-all duration-200 group',
                active
                  ? 'bg-primary/10 text-primary border-r-2 border-primary'
                  : 'text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-accent border-r-2 border-transparent'
              )}
              title={!showLabel ? item.label : undefined}
            >
              <span
                className={cn(
                  'material-symbols-outlined text-[20px] shrink-0 group-hover:scale-110 transition-transform',
                  active ? 'icon-fill' : ''
                )}
              >
                {item.icon}
              </span>
              {showLabel && <span className="text-[13px]">{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className={cn(
        'border-t border-sidebar-border py-3',
        sidebarExpanded && !sidebarCollapsed ? 'px-4' : 'px-2'
      )}>
        {(sidebarExpanded && !sidebarCollapsed) ? (
          <div className="space-y-1">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-7 h-7 rounded-full bg-accent border border-border flex items-center justify-center">
                <span className="material-symbols-outlined text-muted-foreground text-[14px]">person</span>
              </div>
              <div className="flex flex-col">
                <span className="text-[13px] font-semibold text-sidebar-foreground">Engineer Workspace</span>
                <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">admin</span>
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <a
                href="https://github.com/ShashankT-ECE/rtl-to-gds-agent"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 hover:text-foreground transition-colors"
              >
                <ExternalLink className="h-3 w-3" />
                GitHub
              </a>
              <span>·</span>
              <a
                href="/docs"
                className="flex items-center gap-1.5 hover:text-foreground transition-colors"
              >
                <BookOpen className="h-3 w-3" />
                Docs
              </a>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <a
              href="https://github.com/ShashankT-ECE/rtl-to-gds-agent"
              target="_blank"
              rel="noopener noreferrer"
              className="text-muted-foreground hover:text-foreground transition-colors"
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
