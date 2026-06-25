'use client';

import { useEffect } from 'react';
import { XCircle, RefreshCw } from 'lucide-react';

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Unhandled error:', error);
  }, [error]);

  return (
    <div className="flex items-center justify-center py-24">
      <div className="text-center max-w-md">
        <div className="mb-6 inline-flex rounded-full bg-etch-red/10 p-6">
          <XCircle className="h-16 w-16 text-etch-red" />
        </div>
        <h1 className="text-2xl font-bold text-silicon-100 mb-2">Something went wrong</h1>
        <p className="text-sm text-silicon-400 mb-2">
          An unexpected error occurred in the application.
        </p>
        {error.digest && (
          <p className="text-xs text-silicon-600 font-mono mb-6">Error ID: {error.digest}</p>
        )}
        <button
          onClick={reset}
          className="inline-flex items-center gap-2 rounded-lg bg-silicon-800 border border-silicon-600 px-5 py-2.5 text-sm font-semibold text-silicon-200 hover:bg-silicon-700 transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          Try Again
        </button>
      </div>
    </div>
  );
}
