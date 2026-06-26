'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { cn } from '@/lib/utils';
import type { LiveMetrics } from '@/stores/demo-store';

// Animated counter that smoothly transitions between values
function AnimatedCounter({
  value,
  suffix = '',
  prefix = '',
  decimals = 0,
  className,
  large = false,
}: {
  value: number;
  suffix?: string;
  prefix?: string;
  decimals?: number;
  className?: string;
  large?: boolean;
}) {
  const [display, setDisplay] = useState(value);
  const animRef = useRef<number>(0);
  const prevValue = useRef(value);

  useEffect(() => {
    if (prevValue.current === value) {
      setDisplay(value);
      return;
    }

    const startValue = prevValue.current;
    const diff = value - startValue;
    const duration = 600; // ms
    const startTime = performance.now();

    const animate = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(startValue + diff * eased);

      if (progress < 1) {
        animRef.current = requestAnimationFrame(animate);
      }
    };

    animRef.current = requestAnimationFrame(animate);
    prevValue.current = value;

    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, [value]);

  return (
    <span
      className={cn(
        'font-mono tabular-nums transition-colors duration-300',
        large ? 'text-2xl font-bold' : 'text-sm',
        className
      )}
    >
      {prefix}
      {display.toFixed(decimals)}
      {suffix}
    </span>
  );
}

interface MetricCardProps {
  label: string;
  value: number;
  suffix?: string;
  prefix?: string;
  decimals?: number;
  icon: string;
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple' | 'orange';
  large?: boolean;
  subtitle?: string;
  sparkline?: number[];
}

const colorMap = {
  blue: { bg: 'bg-blue-500/10', border: 'border-blue-500/20', text: 'text-blue-400', glow: 'shadow-[0_0_12px_rgba(59,130,246,0.15)]' },
  green: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', text: 'text-emerald-400', glow: 'shadow-[0_0_12px_rgba(16,185,129,0.15)]' },
  yellow: { bg: 'bg-amber-500/10', border: 'border-amber-500/20', text: 'text-amber-400', glow: 'shadow-[0_0_12px_rgba(245,158,11,0.15)]' },
  red: { bg: 'bg-red-500/10', border: 'border-red-500/20', text: 'text-red-400', glow: 'shadow-[0_0_12px_rgba(239,68,68,0.15)]' },
  purple: { bg: 'bg-purple-500/10', border: 'border-purple-500/20', text: 'text-purple-400', glow: 'shadow-[0_0_12px_rgba(168,85,247,0.15)]' },
  orange: { bg: 'bg-orange-500/10', border: 'border-orange-500/20', text: 'text-orange-400', glow: 'shadow-[0_0_12px_rgba(249,115,22,0.15)]' },
};

function MetricCard({
  label,
  value,
  suffix = '',
  prefix = '',
  decimals = 0,
  icon,
  color = 'blue',
  large = false,
  subtitle,
}: MetricCardProps) {
  const colors = colorMap[color];

  return (
    <div
      className={cn(
        'relative rounded-lg border p-4 transition-all duration-300 group',
        colors.bg,
        colors.border,
        'hover:scale-[1.02] hover:shadow-lg',
        colors.glow,
      )}
    >
      {/* Icon and label */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-lg">{icon}</span>
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {label}
          </span>
        </div>
        {/* Status dot */}
        {value > 0 && (
          <span
            className={cn(
              'h-2 w-2 rounded-full animate-pulse',
              color === 'green' ? 'bg-emerald-500' :
              color === 'red' ? 'bg-red-500' :
              color === 'yellow' ? 'bg-amber-500' :
              'bg-blue-500'
            )}
          />
        )}
      </div>

      {/* Value */}
      <AnimatedCounter
        value={value}
        suffix={suffix}
        prefix={prefix}
        decimals={decimals}
        large={large}
        className={cn(colors.text, 'block')}
      />

      {/* Subtitle */}
      {subtitle && (
        <p className="text-2xs text-muted-foreground mt-1 font-mono">{subtitle}</p>
      )}

      {/* Progress shimmer for active metrics */}
      {value > 0 && (
        <div
          className={cn(
            'absolute bottom-0 left-0 right-0 h-0.5 rounded-b-lg overflow-hidden',
            color === 'green' ? 'bg-emerald-500/20' :
            color === 'red' ? 'bg-red-500/20' :
            color === 'yellow' ? 'bg-amber-500/20' :
            'bg-blue-500/20'
          )}
        >
          <div
            className={cn(
              'h-full animate-[progress-indeterminate_1.5s_ease-in-out_infinite]',
              color === 'green' ? 'bg-emerald-500' :
              color === 'red' ? 'bg-red-500' :
              color === 'yellow' ? 'bg-amber-500' :
              'bg-blue-500'
            )}
            style={{ width: '30%' }}
          />
        </div>
      )}
    </div>
  );
}

interface MetricsDashboardProps {
  metrics: LiveMetrics;
  isLive?: boolean;
  className?: string;
}

export function MetricsDashboard({ metrics, isLive = false, className }: MetricsDashboardProps) {
  const hasData = metrics.runtime > 0;

  return (
    <div className={cn('rounded-lg border border-border bg-card overflow-hidden', className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-border bg-surface-container-highest">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[16px] text-muted-foreground">monitoring</span>
          <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">
            Live Metrics
          </h3>
        </div>
        {isLive && (
          <span className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-emerald-500">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            Stream Active
          </span>
        )}
        {!isLive && !hasData && (
          <span className="text-2xs text-muted-foreground">Waiting for pipeline...</span>
        )}
      </div>

      {/* Metrics grid */}
      <div className="p-4">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {/* Area */}
          <MetricCard
            label="Area"
            value={metrics.area}
            suffix=" μm²"
            decimals={0}
            icon="📐"
            color="purple"
            subtitle={metrics.area > 0 ? `${(metrics.area / 1000000).toFixed(4)} mm²` : undefined}
          />

          {/* Power */}
          <MetricCard
            label="Power"
            value={metrics.power}
            suffix=" mW"
            decimals={1}
            icon="⚡"
            color="yellow"
            subtitle={metrics.power > 0 ? `Est. dynamic` : undefined}
          />

          {/* Timing Slack */}
          <MetricCard
            label="Timing Slack"
            value={metrics.timingSlack}
            suffix=" ns"
            decimals={2}
            icon="⏱️"
            color={metrics.timingSlack >= 0 ? 'green' : 'red'}
            subtitle={metrics.timingSlack > 0 ? 'MET' : metrics.timingSlack < 0 ? 'VIOLATED' : undefined}
          />

          {/* Violations */}
          <MetricCard
            label="DRC Violations"
            value={metrics.violations}
            decimals={0}
            icon="🛡️"
            color={metrics.violations === 0 ? 'green' : 'red'}
            subtitle={metrics.violations === 0 && hasData ? 'CLEAN' : undefined}
          />

          {/* Runtime */}
          <MetricCard
            label="Runtime"
            value={metrics.runtime}
            suffix="s"
            decimals={0}
            icon="🕐"
            color="blue"
            subtitle={
              metrics.runtime > 60
                ? `${Math.floor(metrics.runtime / 60)}m ${metrics.runtime % 60}s`
                : undefined
            }
          />

          {/* Tokens */}
          <MetricCard
            label="Tokens"
            value={metrics.tokensConsumed}
            decimals={0}
            icon="🧠"
            color="purple"
            subtitle={metrics.tokensConsumed > 1000 ? `${(metrics.tokensConsumed / 1000).toFixed(1)}k` : undefined}
          />

          {/* Iterations */}
          <MetricCard
            label="Fix Iterations"
            value={metrics.iterations}
            decimals={0}
            icon="🔄"
            color={metrics.iterations > 2 ? 'yellow' : 'green'}
            subtitle={metrics.iterations > 0 ? `${metrics.iterations}/5 max` : undefined}
          />

          {/* Memory */}
          <MetricCard
            label="Memory"
            value={metrics.memoryUsage}
            suffix=" MB"
            decimals={0}
            icon="💾"
            color="orange"
            subtitle={metrics.memoryUsage > 0 ? `Peak RSS` : undefined}
          />

          {/* Cell Count */}
          <MetricCard
            label="Cells"
            value={metrics.cellCount}
            decimals={0}
            icon="🔲"
            color="blue"
            subtitle={metrics.cellCount > 0 ? 'Std cells' : undefined}
          />

          {/* Frequency */}
          <MetricCard
            label="Frequency"
            value={metrics.frequency}
            suffix=" MHz"
            decimals={0}
            icon="📡"
            color="green"
            subtitle={metrics.frequency > 0 ? `Target` : undefined}
          />

          {/* Success probability */}
          <MetricCard
            label="Success Prob."
            value={metrics.successProbability}
            suffix="%"
            decimals={0}
            icon="🎯"
            color={metrics.successProbability >= 90 ? 'green' : metrics.successProbability >= 50 ? 'yellow' : 'red'}
            large
            subtitle={metrics.successProbability === 100 ? 'Ready for signoff' : metrics.successProbability > 0 ? 'Estimated' : undefined}
          />
        </div>
      </div>
    </div>
  );
}
