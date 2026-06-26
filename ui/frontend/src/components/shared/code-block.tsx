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
    <div className={cn('relative rounded-lg border border-border bg-black', className)}>
      <div className="flex items-center justify-between px-4 py-1.5 border-b border-border">
        <span className="text-xs text-muted-foreground font-mono uppercase">{language}</span>
        <button
          onClick={handleCopy}
          className="p-1 rounded text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
          title="Copy to clipboard"
        >
          {copied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
        </button>
      </div>
      <pre
        className={cn(
          'overflow-x-auto p-4 text-sm font-mono text-foreground/80 leading-relaxed',
          maxLines && `max-h-[${maxLines * 1.5}rem]`
        )}
        style={maxLines ? { maxHeight: `${maxLines * 1.5}rem` } : undefined}
      >
        <code>{code}</code>
      </pre>
    </div>
  );
}
