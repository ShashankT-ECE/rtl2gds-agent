'use client';

import { useState, useCallback, useEffect } from 'react';
import { Topbar } from './topbar';
import { Sidebar } from './sidebar';
import { useUIStore } from '@/stores/ui-store';
import { cn } from '@/lib/utils';

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const sidebarExpanded = useUIStore((s) => s.sidebarExpanded);
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed);

  const sidebarWidth = sidebarExpanded && !sidebarCollapsed ? 'ml-[280px]' : 'ml-16';

  // Close mobile menu on larger screens
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) {
        setMobileMenuOpen(false);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleMobileClose = useCallback(() => {
    setMobileMenuOpen(false);
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <Topbar onMenuClick={() => setMobileMenuOpen((v) => !v)} />

      {/* Desktop sidebar */}
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      {/* Mobile sidebar overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-black/60"
            onClick={handleMobileClose}
          />
          <Sidebar onClose={handleMobileClose} />
        </div>
      )}

      {/* Main content */}
      <main
        className={cn(
          'pt-14 transition-all duration-300',
          sidebarWidth
        )}
      >
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  );
}
