import Link from 'next/link';
import { Cpu } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="flex items-center justify-center py-24">
      <div className="text-center">
        <div className="mb-6 inline-flex rounded-full bg-accent p-6">
          <Cpu className="h-16 w-16 text-muted-foreground" />
        </div>
        <h1 className="text-4xl font-bold text-foreground mb-2">404</h1>
        <p className="text-lg text-muted-foreground mb-6">This page does not exist in the design hierarchy.</p>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 rounded bg-primary px-6 py-2.5 text-sm font-semibold text-white hover:bg-primary/90 transition-colors"
        >
          Return to Dashboard
        </Link>
      </div>
    </div>
  );
}
