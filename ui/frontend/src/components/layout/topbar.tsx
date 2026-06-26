'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, ExternalLink, BookOpen, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useSystemStatus } from '@/hooks/use-system-status';
import { useSSEConnection } from '@/hooks/use-sse-connection';
import { useUIStore } from '@/stores/ui-store';
import { useJobStore } from '@/stores/job-store';
import { useDemoStore } from '@/stores/demo-store';
import { ModeIndicator } from '@/components/shared/mode-indicator';
import { cn } from '@/lib/utils';

interface TopbarProps {
  onMenuClick: () => void;
}

function DemoToggle() {
  const demoEnabled = useDemoStore((s) => s.demoEnabled);
  const toggleDemo = useDemoStore((s) => s.toggleDemo);
  const isSimulating = useDemoStore((s) => s.isSimulating);

  return (
    <button
      onClick={toggleDemo}
      className={cn(
        'flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-semibold uppercase tracking-wider transition-all duration-300 border',
        demoEnabled
          ? 'bg-blue-500/10 border-blue-500/30 text-blue-400 shadow-[0_0_8px_rgba(59,130,246,0.15)]'
          : 'bg-transparent border-transparent text-muted-foreground hover:text-foreground hover:border-border'
      )}
      title={demoEnabled ? 'Disable Demo Mode' : 'Enable Demo Mode (⌘D)'}
    >
      <span className="relative flex h-1.5 w-1.5">
        {isSimulating ? (
          <>
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500" />
          </>
        ) : (
          <span className={cn('inline-flex rounded-full h-1.5 w-1.5', demoEnabled ? 'bg-blue-400' : 'bg-slate-600')} />
        )}
      </span>
      <span className="hidden md:inline">{demoEnabled ? 'Demo' : 'Live'}</span>
    </button>
  );
}

export function Topbar({ onMenuClick }: TopbarProps) {
  const { data: status } = useSystemStatus();
  const { connected } = useSSEConnection();
  const sidebarExpanded = useUIStore((s) => s.sidebarExpanded);
  const jobs = useJobStore((s) => s.jobs);

  const activeCount = Object.values(jobs).filter((j) => j.status === 'running').length;
  const completedCount = Object.values(jobs).filter((j) => j.status === 'completed').length;
  const failedCount = Object.values(jobs).filter((j) => j.status === 'failed').length;
  const queuedCount = Object.values(jobs).filter((j) => j.status === 'queued').length;

  const healthOk = status !== undefined;
  const versions = status?.versions;

  return (
    <header className="fixed top-0 left-0 right-0 z-40 h-14 bg-card border-b border-border flex items-center px-4 gap-4">
      {/* Menu toggle */}
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8 text-muted-foreground hover:text-foreground lg:hidden"
        onClick={onMenuClick}
      >
        <Menu className="h-5 w-5" />
      </Button>

      {/* Health dot */}
      <div className="flex items-center gap-2 text-xs">
        <span
          className={cn(
            'h-2 w-2 rounded-full',
            healthOk ? 'bg-emerald-500 animate-pulse-green' : 'bg-destructive'
          )}
        />
        <span className="text-muted-foreground hidden sm:inline">
          {healthOk ? 'System Operational' : 'System Degraded'}
        </span>
      </div>

      {/* Version dots */}
      <div className="hidden md:flex items-center gap-2 text-xs">
        <span
          className={cn(
            'h-2 w-2 rounded-full',
            versions?.v1_available !== false ? 'bg-emerald-500' : 'bg-[#434656]'
          )}
          title="V1"
        />
        <span className="text-muted-foreground">V1</span>
        <span
          className={cn(
            'h-2 w-2 rounded-full',
            versions?.v2_available ? 'bg-emerald-500' : 'bg-[#434656]'
          )}
          title="V2"
        />
        <span className="text-muted-foreground">V2</span>
        <span
          className={cn(
            'h-2 w-2 rounded-full',
            versions?.v3_available ? 'bg-emerald-500' : 'bg-[#434656]'
          )}
          title="V3"
        />
        <span className="text-muted-foreground">V3</span>
      </div>

      {/* Mode badge */}
      <ModeIndicator />

      {/* Provider badge */}
      <div className="hidden sm:inline-flex items-center gap-1.5 rounded-full bg-accent px-2.5 py-0.5 text-xs text-muted-foreground">
        {status?.provider || 'deepseek'}
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Search input (Stitch pattern) */}
      <div className="relative hidden lg:block">
        <span className="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground text-[18px]">
          search
        </span>
        <input
          className="bg-surface-container-lowest border border-border rounded py-1 pl-9 pr-16 text-xs text-foreground focus:outline-none focus:border-primary focus:ring-0 w-64 transition-colors placeholder:text-muted-foreground/50"
          placeholder="Search resources..."
          type="text"
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          <kbd className="font-mono text-[10px] text-muted-foreground border border-border rounded px-1">⌘</kbd>
          <kbd className="font-mono text-[10px] text-muted-foreground border border-border rounded px-1">K</kbd>
        </div>
      </div>

      {/* Nav links */}
      <nav className="hidden md:flex items-center gap-4">
        <Link href="/docs" className="text-muted-foreground hover:text-foreground transition-colors text-xs py-1 px-2 rounded cursor-pointer">
          Docs
        </Link>
        <Link href="/support" className="text-muted-foreground hover:text-foreground transition-colors text-xs py-1 px-2 rounded cursor-pointer">
          Support
        </Link>
      </nav>

      <div className="h-6 w-px bg-border hidden md:block" />

      {/* Actions */}
      <div className="flex items-center gap-3">
        <button className="text-muted-foreground hover:text-foreground transition-colors relative" title="Notifications">
          <span className="material-symbols-outlined text-[20px]">notifications</span>
          <span className="absolute top-0 right-0 w-2 h-2 bg-primary rounded-full" />
        </button>
        <button className="text-muted-foreground hover:text-foreground transition-colors" title="Settings">
          <span className="material-symbols-outlined text-[20px]">settings</span>
        </button>
      </div>

      {/* Job mini-stats */}
      <div className="hidden xl:flex items-center gap-3 text-xs text-muted-foreground font-mono">
        <span title="Active jobs" className="text-primary">
          ▶ {activeCount}
        </span>
        <span title="Completed jobs" className="text-emerald-500">
          ✓ {completedCount}
        </span>
        <span title="Failed jobs" className="text-destructive">
          ✗ {failedCount}
        </span>
        <span title="Queued jobs" className="text-muted-foreground/50">
          ◼ {queuedCount}
        </span>
      </div>

      {/* Demo mode toggle */}
      <DemoToggle />

      {/* SSE indicator */}
      <div className="flex items-center gap-1.5" title={connected ? 'SSE Connected' : 'SSE Idle'}>
        <span
          className={cn(
            'h-2 w-2 rounded-full',
            connected ? 'bg-emerald-500 animate-pulse-green' : 'bg-[#434656]'
          )}
        />
        <span className="text-[10px] text-muted-foreground hidden sm:inline">SSE</span>
      </div>

      {/* User avatar */}
      <div className="w-8 h-8 rounded-full bg-accent border border-border overflow-hidden flex items-center justify-center cursor-pointer ml-1">
        <span className="material-symbols-outlined text-muted-foreground text-[18px]">person</span>
      </div>
    </header>
  );
}
