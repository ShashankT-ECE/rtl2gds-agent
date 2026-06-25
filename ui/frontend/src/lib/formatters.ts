// ============================================================
// Formatting utilities — dates, durations, numbers
// ============================================================

/**
 * Format a duration in seconds to a human-readable string.
 */
export function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return '--:--';
  if (seconds < 0) return '00:00';

  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);

  if (h > 0) {
    return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

/**
 * Format milliseconds to a concise string.
 */
export function formatMs(ms: number | null | undefined): string {
  if (ms === null || ms === undefined) return '--';
  if (ms < 1000) return `${ms.toFixed(0)}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return formatDuration(ms / 1000);
}

/**
 * Format an ISO 8601 timestamp to relative time (e.g., "2 min ago").
 */
export function formatRelativeTime(isoString: string | null | undefined): string {
  if (!isoString) return '--';
  const now = Date.now();
  const then = new Date(isoString).getTime();
  const diffMs = now - then;

  if (diffMs < 0) return 'just now';
  const seconds = Math.floor(diffMs / 1000);
  if (seconds < 5) return 'just now';
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

/**
 * Format an ISO 8601 timestamp to a time string (HH:MM:SS).
 */
export function formatTime(isoString: string | null | undefined): string {
  if (!isoString) return '--:--:--';
  return new Date(isoString).toLocaleTimeString('en-US', { hour12: false });
}

/**
 * Format a timestamp to HH:MM:SS.mmm for event log display.
 */
export function formatEventTimestamp(isoString: string): string {
  const d = new Date(isoString);
  const h = d.getHours().toString().padStart(2, '0');
  const m = d.getMinutes().toString().padStart(2, '0');
  const s = d.getSeconds().toString().padStart(2, '0');
  const ms = d.getMilliseconds().toString().padStart(3, '0');
  return `${h}:${m}:${s}.${ms}`;
}

/**
 * Format a number with commas.
 */
export function formatNumber(n: number): string {
  return n.toLocaleString('en-US');
}

/**
 * Format a percentage.
 */
export function formatPercent(pct: number): string {
  return `${pct.toFixed(1)}%`;
}

/**
 * Truncate a string to a maximum length with ellipsis.
 */
export function truncate(str: string, maxLen: number): string {
  if (str.length <= maxLen) return str;
  return str.slice(0, maxLen - 1) + '…';
}
