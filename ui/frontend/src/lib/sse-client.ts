// ============================================================
// SSE client — EventSource wrapper with reconnection protocol
// ============================================================

import { API_BASE_URL, SSE_MAX_RECONNECT_ATTEMPTS, SSE_RECONNECT_BACKOFF_MS } from './constants';
import type { PipelineEvent, SSEDoneEvent, SSEHeartbeatEvent } from './types';
import type { EventType } from './types';

export type SSECallback = (event: PipelineEvent) => void;
export type SSEDoneCallback = (data: SSEDoneEvent) => void;
export type SSEErrorCallback = (error: string) => void;
export type SSEStatusCallback = (status: 'connecting' | 'connected' | 'disconnected') => void;

export interface SSEConnectionOptions {
  jobId: string;
  afterSeq?: number;
  onEvent: SSECallback;
  onDone: SSEDoneCallback;
  onError: SSEErrorCallback;
  onStatusChange: SSEStatusCallback;
  heartbeatIntervalMs?: number;
}

export class SSEConnection {
  private eventSource: EventSource | null = null;
  private options: SSEConnectionOptions;
  private reconnectAttempt = 0;
  private lastSequenceNum = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private isDisposed = false;

  constructor(options: SSEConnectionOptions) {
    this.options = options;
    this.lastSequenceNum = options.afterSeq || 0;
  }

  connect(): void {
    if (this.isDisposed) return;
    this.options.onStatusChange('connecting');

    const url = this.buildUrl();
    this.eventSource = new EventSource(url);

    // Handle pipeline events
    this.eventSource.addEventListener('pipeline_event', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data) as PipelineEvent;
        this.lastSequenceNum = Math.max(this.lastSequenceNum, data.sequence_num);
        this.options.onEvent(data);
      } catch {
        console.warn('Failed to parse SSE pipeline_event:', event.data);
      }
    });

    // Handle heartbeat
    this.eventSource.addEventListener('heartbeat', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data) as SSEHeartbeatEvent;
        // Heartbeat received — connection is alive
        if (this.reconnectAttempt > 0) {
          this.reconnectAttempt = 0; // Reset on successful heartbeat
        }
      } catch {
        // ignore malformed heartbeat
      }
    });

    // Handle done
    this.eventSource.addEventListener('done', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data) as SSEDoneEvent;
        this.options.onDone(data);
        this.close();
      } catch {
        console.warn('Failed to parse SSE done event:', event.data);
      }
    });

    // Handle error
    this.eventSource.addEventListener('error', (event: MessageEvent) => {
      if (event.data) {
        try {
          const data = JSON.parse(event.data);
          this.options.onError(data.error || 'Unknown error');
        } catch {
          this.options.onError('Connection error');
        }
      }
    });

    // Connection opened
    this.eventSource.onopen = () => {
      this.options.onStatusChange('connected');
      this.reconnectAttempt = 0;
    };

    // Connection error (lost)
    this.eventSource.onerror = () => {
      this.options.onStatusChange('disconnected');
      this.eventSource?.close();
      this.eventSource = null;
      this.attemptReconnect();
    };
  }

  private buildUrl(): string {
    const params = new URLSearchParams({ job_id: this.options.jobId });
    if (this.lastSequenceNum > 0) {
      params.set('after', String(this.lastSequenceNum));
    }
    return `${API_BASE_URL}/api/run/stream?${params.toString()}`;
  }

  private attemptReconnect(): void {
    if (this.isDisposed) return;

    if (this.reconnectAttempt >= SSE_MAX_RECONNECT_ATTEMPTS) {
      this.options.onError('Connection lost after maximum reconnection attempts');
      return;
    }

    const delay = SSE_RECONNECT_BACKOFF_MS[
      Math.min(this.reconnectAttempt, SSE_RECONNECT_BACKOFF_MS.length - 1)
    ];

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempt++;
      this.connect();
    }, delay);
  }

  close(): void {
    this.isDisposed = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    this.options.onStatusChange('disconnected');
  }

  getLastSequenceNum(): number {
    return this.lastSequenceNum;
  }
}
