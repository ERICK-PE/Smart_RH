import { useQueries } from '@tanstack/react-query';
import { Activity, BriefcaseBusiness, ClipboardList, UsersRound } from 'lucide-react';
import { api } from '../services/api';
import { PageHeader } from '../components/ui';
import { PageState } from '../components/PageState';

const indicatorEndpoints = [
  ['Organização', '/setor/setores/rh/indicadores/'],
  ['Funcionários', '/funcionario/funcionarios/rh/indicadores/'],
  ['Planos', '/funcionario/planos-carreira/rh/indicadores/'],
  ['Análises', '/avaliacao/analises-comportamentais/rh/indicadores/'],
  ['Avaliações', '/avaliacao/avaliacoes-desempenho/rh/indicadores/'],
  ['Recrutamento', '/candidato/vagas/rh/indicadores/'],
] as const;

const icons = [Activity, UsersRound, BriefcaseBusiness, ClipboardList];

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
  if (error) return <PageState title="Não foi possível carregar o dashboard" variant="error" />;

  return (
    <section>
      <PageHeader title="Dashboard RH" description="Indicadores consolidados dos módulos administrativos." />
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
                      {typeof value === 'object' ? JSON.stringify(value) : String(value ?? 'Não informado')}
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
