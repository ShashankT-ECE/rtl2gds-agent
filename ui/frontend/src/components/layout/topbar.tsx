'use client';

import { Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useSystemStatus } from '@/hooks/use-system-status';
import { useSSEConnection } from '@/hooks/use-sse-connection';
import { useUIStore } from '@/stores/ui-store';
import { useJobStore } from '@/stores/job-store';
import { ModeIndicator } from '@/components/shared/mode-indicator';
import { cn } from '@/lib/utils';

interface TopbarProps {
  onMenuClick: () => void;
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
    <header className="fixed top-0 left-0 right-0 z-40 h-12 bg-silicon-900 border-b border-silicon-700 flex items-center px-4 gap-4">
      {/* Menu toggle (mobile) */}
      {!sidebarExpanded && (
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-silicon-400 hover:text-silicon-200 lg:hidden"
          onClick={onMenuClick}
        >
          <Menu className="h-5 w-5" />
        </Button>
      )}

      {/* Health dot */}
      <div className="flex items-center gap-2 text-xs">
        <span
          className={cn(
            'h-2 w-2 rounded-full',
            healthOk ? 'bg-photo-green animate-pulse' : 'bg-etch-red'
          )}
        />
        <span className="text-silicon-400 hidden sm:inline">
          {healthOk ? 'System Operational' : 'System Degraded'}
        </span>
      </div>

      {/* Version dots */}
      <div className="hidden md:flex items-center gap-2 text-xs">
        <span
          className={cn(
            'h-2 w-2 rounded-full',
            versions?.v1_available !== false ? 'bg-photo-green' : 'bg-silicon-600'
          )}
          title="V1"
        />
        <span className="text-silicon-600">V1</span>
        <span
          className={cn(
            'h-2 w-2 rounded-full',
            versions?.v2_available ? 'bg-photo-green' : 'bg-silicon-600'
          )}
          title="V2"
        />
        <span className="text-silicon-600">V2</span>
        <span
          className={cn(
            'h-2 w-2 rounded-full',
            versions?.v3_available ? 'bg-photo-green' : 'bg-silicon-600'
          )}
          title="V3"
        />
        <span className="text-silicon-600">V3</span>
      </div>

      {/* Mode badge */}
      <ModeIndicator />

      {/* Provider badge */}
      <div className="hidden sm:inline-flex items-center gap-1.5 rounded-full bg-silicon-800 px-2.5 py-0.5 text-xs text-silicon-400">
        {status?.provider || 'deepseek'}
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Job mini-stats */}
      <div className="hidden lg:flex items-center gap-3 text-xs text-silicon-400 font-mono">
        <span title="Active jobs" className="text-plasma-blue">
          ▶ {activeCount}
        </span>
        <span title="Completed jobs" className="text-photo-green">
          ✓ {completedCount}
        </span>
        <span title="Failed jobs" className="text-etch-red">
          ✗ {failedCount}
        </span>
        <span title="Queued jobs" className="text-silicon-500">
          ◼ {queuedCount}
        </span>
      </div>

      {/* SSE indicator */}
      <div className="flex items-center gap-1.5" title={connected ? 'SSE Connected' : 'SSE Idle'}>
        <span
          className={cn(
            'h-2 w-2 rounded-full',
            connected ? 'bg-photo-green animate-pulse' : 'bg-silicon-600'
          )}
        />
        <span className="text-2xs text-silicon-500 hidden sm:inline">SSE</span>
      </div>
    </header>
  );
}
