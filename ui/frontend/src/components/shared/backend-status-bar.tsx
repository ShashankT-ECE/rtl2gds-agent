'use client';

import { useState, useEffect, useCallback } from 'react';
import { Wifi, WifiOff, AlertTriangle, RefreshCw, Server } from 'lucide-react';
import { API_BASE_URL, POLLING_INTERVAL_MS } from '@/lib/constants';
import { cn } from '@/lib/utils';

type BackendStatus = 'connected' | 'connecting' | 'disconnected' | 'retrying';

interface BackendStatusBarProps {
  className?: string;
}

export function BackendStatusBar({ className }: BackendStatusBarProps) {
  const [status, setStatus] = useState<BackendStatus>('connecting');
  const [retryCount, setRetryCount] = useState(0);
  const [expanded, setExpanded] = useState(false);

  const checkBackend = useCallback(async () => {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);

      const response = await fetch(`${API_BASE_URL}/health`, {
        signal: controller.signal,
        cache: 'no-store',
      });

      clearTimeout(timeout);

      if (response.ok) {
        setStatus('connected');
        setRetryCount(0);
      } else {
        setStatus('disconnected');
      }
    } catch {
      setStatus((prev) => {
        if (prev === 'connected') return 'disconnected';
        if (prev === 'retrying') setRetryCount((c) => c + 1);
        return 'disconnected';
      });
    }
  }, []);

  useEffect(() => {
    checkBackend();
    const interval = setInterval(checkBackend, POLLING_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [checkBackend]);

  const handleRetry = () => {
    setStatus('retrying');
    setRetryCount(0);
    checkBackend();
  };

  const statusConfig = {
    connected: {
      icon: <Wifi className="h-3.5 w-3.5" />,
      label: 'Backend Connected',
      bg: 'bg-emerald-500/10 border-emerald-500/20',
      text: 'text-emerald-400',
      dot: 'bg-emerald-500',
    },
    connecting: {
      icon: <Server className="h-3.5 w-3.5 animate-pulse" />,
      label: 'Connecting to backend...',
      bg: 'bg-amber-500/10 border-amber-500/20',
      text: 'text-amber-400',
      dot: 'bg-amber-500 animate-pulse',
    },
    disconnected: {
      icon: <WifiOff className="h-3.5 w-3.5" />,
      label: 'Backend Disconnected',
      bg: 'bg-red-500/10 border-red-500/20',
      text: 'text-red-400',
      dot: 'bg-red-500',
    },
    retrying: {
      icon: <RefreshCw className="h-3.5 w-3.5 animate-spin" />,
      label: `Retrying... (attempt ${retryCount + 1})`,
      bg: 'bg-amber-500/10 border-amber-500/20',
      text: 'text-amber-400',
      dot: 'bg-amber-500 animate-pulse',
    },
  };

  const config = statusConfig[status];

  return (
    <div
      className={cn(
        'rounded-lg border px-4 py-2 transition-all duration-500',
        config.bg,
        status === 'connected' ? 'opacity-60 hover:opacity-100' : '',
        className
      )}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className={cn('relative flex h-2 w-2')}>
            {status === 'connecting' || status === 'retrying' ? (
              <>
                <span className={cn('animate-ping absolute inline-flex h-full w-full rounded-full opacity-75', config.dot)} />
                <span className={cn('relative inline-flex rounded-full h-2 w-2', config.dot)} />
              </>
            ) : (
              <span className={cn('inline-flex rounded-full h-2 w-2', config.dot)} />
            )}
          </span>
          <span className={cn('text-xs font-semibold', config.text)}>
            {config.icon}
          </span>
          <span className={cn('text-xs font-medium', config.text)}>
            {config.label}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {status !== 'connected' && status !== 'connecting' && (
            <button
              onClick={handleRetry}
              className="text-xs font-semibold text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
            >
              <RefreshCw className={cn('h-3 w-3', status === 'retrying' && 'animate-spin')} />
              Reconnect
            </button>
          )}
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {expanded ? 'Less' : 'More'}
          </button>
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className={cn(
          'mt-2 pt-2 border-t text-xs space-y-1 animate-[fade-in_0.15s_ease-out]',
          status === 'connected' ? 'border-emerald-500/20 text-emerald-400/60' :
          status === 'disconnected' ? 'border-red-500/20 text-red-400/60' :
          'border-amber-500/20 text-amber-400/60'
        )}>
          <div className="flex justify-between">
            <span>API Endpoint</span>
            <span className="font-mono">{API_BASE_URL}</span>
          </div>
          <div className="flex justify-between">
            <span>Status</span>
            <span className="font-mono uppercase">{status}</span>
          </div>
          <div className="flex justify-between">
            <span>Reconnect Policy</span>
            <span className="font-mono">Exponential backoff, max 10 retries</span>
          </div>
          {status === 'disconnected' && (
            <p className="flex items-center gap-1.5 text-xs mt-1">
              <AlertTriangle className="h-3 w-3" />
              Demo mode is available for offline presentations
            </p>
          )}
        </div>
      )}
    </div>
  );
}
