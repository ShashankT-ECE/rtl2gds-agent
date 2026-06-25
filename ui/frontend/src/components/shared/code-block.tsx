'use client';

import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CodeBlockProps {
  code: string;
  language?: string;
  maxLines?: number;
  className?: string;
}

export function CodeBlock({ code, language = 'text', maxLines, className }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={cn('relative rounded-lg border border-silicon-700 bg-silicon-950', className)}>
      <div className="flex items-center justify-between px-4 py-1.5 border-b border-silicon-700">
        <span className="text-xs text-silicon-500 font-mono uppercase">{language}</span>
        <button
          onClick={handleCopy}
          className="p-1 rounded text-silicon-500 hover:text-silicon-300 hover:bg-silicon-800 transition-colors"
          title="Copy to clipboard"
        >
          {copied ? <Check className="h-3.5 w-3.5 text-photo-green" /> : <Copy className="h-3.5 w-3.5" />}
        </button>
      </div>
      <pre
        className={cn(
          'overflow-x-auto p-4 text-sm font-mono text-silicon-200 leading-relaxed',
          maxLines && `max-h-[${maxLines * 1.5}rem]`
        )}
        style={maxLines ? { maxHeight: `${maxLines * 1.5}rem` } : undefined}
      >
        <code>{code}</code>
      </pre>
    </div>
  );
}
