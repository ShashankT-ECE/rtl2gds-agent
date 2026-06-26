import { cn } from '@/lib/utils';

interface PageContainerProps {
  children: React.ReactNode;
  title?: React.ReactNode;
  description?: string;
  className?: string;
  actions?: React.ReactNode;
}

export function PageContainer({ children, title, description, className, actions }: PageContainerProps) {
  return (
    <div className={cn('space-y-6', className)}>
      {(title || actions) && (
        <div className="flex items-end justify-between">
          <div>
            {title && (
              <h1 className="text-2xl font-semibold text-foreground tracking-tight">
                {title}
              </h1>
            )}
            {description && (
              <p className="text-[13px] text-muted-foreground mt-1">
                {description}
              </p>
            )}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      {children}
    </div>
  );
}
