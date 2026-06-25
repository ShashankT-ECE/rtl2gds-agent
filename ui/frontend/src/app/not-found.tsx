import Link from 'next/link';
import { Cpu } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="flex items-center justify-center py-24">
      <div className="text-center">
        <div className="mb-6 inline-flex rounded-full bg-silicon-800 p-6">
          <Cpu className="h-16 w-16 text-silicon-600" />
        </div>
        <h1 className="text-4xl font-bold text-silicon-100 mb-2">404</h1>
        <p className="text-lg text-silicon-400 mb-6">This page does not exist in the design hierarchy.</p>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 rounded-lg bg-copper-500 px-6 py-2.5 text-sm font-semibold text-silicon-950 hover:bg-copper-400 transition-colors"
        >
          Return to Dashboard
        </Link>
      </div>
    </div>
  );
}
