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
        <div className="flex items-start justify-between">
          <div>
            {title && (
              <h1 className="text-2xl font-semibold text-silicon-100">{title}</h1>
            )}
            {description && (
              <p className="mt-1 text-sm text-silicon-400">{description}</p>
            )}
          </div>
          {actions && <div className="flex items-center gap-3">{actions}</div>}
        </div>
      )}
      {children}
    </div>
  );
}
