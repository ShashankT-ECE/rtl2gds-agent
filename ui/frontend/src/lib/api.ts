// ============================================================
// API client — thin fetch wrapper with error handling
// ============================================================

import { API_BASE_URL } from './constants';
import type { SuccessResponse } from './types';

class ApiError extends Error {
  code: string;
  status: number;
  details?: Record<string, unknown> | null;

  constructor(code: string, message: string, status: number, details?: Record<string, unknown> | null) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

async function handleResponse<T>(response: Response): Promise<SuccessResponse<T>> {
  const json = await response.json();

  if (!response.ok) {
    // Handle both envelope error and raw error formats
    if (json.success === false && json.error) {
      throw new ApiError(
        json.error.code || 'UNKNOWN_ERROR',
        json.error.message || 'An error occurred',
        response.status,
        json.error.details
      );
    }
    throw new ApiError(
      'HTTP_ERROR',
      `Request failed with status ${response.status}`,
      response.status
    );
  }

  return json as SuccessResponse<T>;
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  timeoutMs = 30000
): Promise<SuccessResponse<T>> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
    return handleResponse<T>(response);
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if ((error as Error).name === 'AbortError') {
      throw new ApiError('TIMEOUT', 'Request timed out', 408);
    }
    throw new ApiError(
      'NETWORK_ERROR',
      'Unable to connect to the server. Is the backend running?',
      0
    );
  } finally {
    clearTimeout(timeout);
  }
}

export const api = {
  get: <T>(path: string, timeoutMs?: number) =>
    request<T>('GET', path, undefined, timeoutMs),

  post: <T>(path: string, body?: unknown, timeoutMs?: number) =>
    request<T>('POST', path, body, timeoutMs),
};

export { ApiError };
