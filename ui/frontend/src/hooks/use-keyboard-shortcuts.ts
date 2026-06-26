'use client';

import { useEffect } from 'react';

type ShortcutHandler = () => void;

interface ShortcutBinding {
  key: string;
  ctrlOrMeta?: boolean;
  handler: ShortcutHandler;
  description: string;
}

const registeredShortcuts: ShortcutBinding[] = [];

export function useKeyboardShortcuts(shortcuts: ShortcutBinding[]) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      // Don't fire when typing in input/textarea/select/rich text
      const tag = target.tagName.toLowerCase();
      if (['input', 'textarea', 'select'].includes(tag) || target.isContentEditable) {
        return;
      }

      for (const shortcut of shortcuts) {
        const metaOk = shortcut.ctrlOrMeta ? (e.metaKey || e.ctrlKey) : true;
        if (e.key.toLowerCase() === shortcut.key.toLowerCase() && metaOk) {
          e.preventDefault();
          shortcut.handler();
          return;
        }
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [shortcuts]);
}

// Commonly used shortcuts reference
export const SHORTCUT_REGISTRY = {
  toggleSidebar: {
    key: 'b',
    ctrlOrMeta: true,
    description: 'Toggle sidebar',
  } as ShortcutBinding,
  toggleDemo: {
    key: 'd',
    ctrlOrMeta: true,
    description: 'Toggle demo mode',
  } as ShortcutBinding,
  focusSearch: {
    key: 'k',
    ctrlOrMeta: true,
    description: 'Open search',
  } as ShortcutBinding,
} as const;
