import { AlertTriangle, Loader2 } from 'lucide-react';

type PageStateProps = {
  title: string;
  description?: string;
  variant?: 'loading' | 'empty' | 'error';
};

/**
 * Estado visual reutilizado para carregamento, vazio e erro.
 */
export function PageState({ title, description, variant = 'loading' }: PageStateProps) {
  return (
    <div className="flex min-h-[320px] items-center justify-center px-6">
      <div className="max-w-md text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-white shadow-soft dark:bg-slate-900">
          {variant === 'loading' ? (
            <Loader2 className="h-5 w-5 animate-spin text-brand" />
          ) : (
            <AlertTriangle className="h-5 w-5 text-warning" />
          )}
        </div>
        <h2 className="text-lg font-semibold text-ink dark:text-slate-100">{title}</h2>
        {description ? <p className="mt-2 text-sm text-muted dark:text-slate-400">{description}</p> : null}
      </div>
    </div>
  );
}
