import { useQueries } from '@tanstack/react-query';
import { Activity, BriefcaseBusiness, ClipboardList, UsersRound } from 'lucide-react';
import { api } from '../services/api';
import { PageHeader, SensitiveValue } from '../components/ui';
import { PageState } from '../components/PageState';

const indicatorEndpoints = [
  ['Organizacao', '/setor/setores/rh/indicadores/'],
  ['Funcionarios', '/funcionario/funcionarios/rh/indicadores/'],
  ['Planos', '/funcionario/planos-carreira/rh/indicadores/'],
  ['Analises', '/avaliacao/analises-comportamentais/rh/indicadores/'],
  ['Avaliacoes', '/avaliacao/avaliacoes-desempenho/rh/indicadores/'],
  ['Recrutamento', '/candidato/vagas/rh/indicadores/'],
] as const;

const icons = [Activity, UsersRound, BriefcaseBusiness, ClipboardList];

function MetricValue({ value }: { value: unknown }) {
  if (value && typeof value === 'object') {
    const entries = Array.isArray(value)
      ? value.map((item, index) => [String(index + 1), item] as const)
      : Object.entries(value as Record<string, unknown>);

    if (!entries.length) return <SensitiveValue value={null} />;

    return (
      <dl className="space-y-1 rounded-md bg-panel p-2 text-left dark:bg-slate-900">
        {entries.map(([key, item]) => (
          <div key={key} className="flex items-start justify-between gap-3">
            <dt className="text-xs font-medium text-muted dark:text-slate-400">{key.replaceAll('_', ' ')}</dt>
            <dd className="text-right text-xs font-semibold text-ink dark:text-slate-100">
              {item && typeof item === 'object' ? <MetricValue value={item} /> : <SensitiveValue value={item} />}
            </dd>
          </div>
        ))}
      </dl>
    );
  }

  return <SensitiveValue value={value} />;
}

/**
 * Painel RH que consolida indicadores administrativos de todos os modulos.
 */
export function DashboardPage() {
  const queries = useQueries({
    queries: indicatorEndpoints.map(([label, endpoint]) => ({
      queryKey: ['indicator', endpoint],
      queryFn: async () => {
        const response = await api.get<Record<string, unknown>>(endpoint);
        return { label, data: response.data };
      },
    })),
  });

  const loading = queries.some((query) => query.isLoading);
  const error = queries.some((query) => query.isError);

  if (loading) return <PageState title="Carregando indicadores" />;
  if (error) return <PageState title="Nao foi possivel carregar o dashboard" variant="error" />;

  return (
    <section>
      <PageHeader title="Dashboard RH" description="Indicadores consolidados dos modulos administrativos." />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {queries.map((query, index) => {
          const Icon = icons[index % icons.length];
          const payload = query.data?.data ?? {};
          return (
            <article key={query.data?.label} className="rounded-md border border-line bg-white p-5 shadow-soft dark:border-slate-700 dark:bg-slate-950">
              <div className="mb-4 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-md bg-panel text-brand dark:bg-slate-900">
                  <Icon className="h-5 w-5" />
                </div>
                <h2 className="font-semibold text-ink dark:text-slate-100">{query.data?.label}</h2>
              </div>
              <dl className="space-y-3">
                {Object.entries(payload).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between gap-4 border-t border-line pt-3 dark:border-slate-700">
                    <dt className="text-sm text-muted dark:text-slate-400">{key.replaceAll('_', ' ')}</dt>
                    <dd className="text-right text-sm font-semibold text-ink dark:text-slate-100">
                      <MetricValue value={value} />
                    </dd>
                  </div>
                ))}
              </dl>
            </article>
          );
        })}
      </div>
    </section>
  );
}
