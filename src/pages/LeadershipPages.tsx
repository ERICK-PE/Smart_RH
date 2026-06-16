import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { useState } from 'react';
import { api, extractApiError, listResource } from '../services/api';
import type { ApiRecord } from '../types';
import { PageState } from '../components/PageState';
import { Button, PageHeader, SensitiveValue } from '../components/ui';

/**
 * Lista funcionarios do setor permitido para lideranca.
 */
export function LeadershipTeamPage() {
  const query = useQuery({
    queryKey: ['leadership-team'],
    queryFn: () => listResource<ApiRecord>('/funcionario/funcionarios/lideranca/funcionarios-setor/', {}),
  });

  if (query.isLoading) return <PageState title="Carregando equipe" />;
  if (query.isError) return <PageState title="Não foi possível carregar a equipe" variant="error" />;

  return (
    <section>
      <PageHeader title="Equipe da liderança" description="Funcionários disponíveis conforme escopo do backend." />
      <div className="overflow-hidden rounded-md border border-line bg-white dark:border-slate-700 dark:bg-slate-950">
        <table className="min-w-full divide-y divide-line text-sm">
          <thead className="bg-panel dark:bg-slate-900">
            <tr>
              <th className="px-4 py-3 text-left">Nome</th>
              <th className="px-4 py-3 text-left">Status</th>
              <th className="px-4 py-3 text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line dark:divide-slate-700">
            {query.data?.results.map((item) => (
              <tr key={String(item.id_funcionario)}>
                <td className="px-4 py-3"><SensitiveValue value={item.nome} /></td>
                <td className="px-4 py-3"><SensitiveValue value={item.status} /></td>
                <td className="px-4 py-3 text-right">
                  <Link className="font-semibold text-brand hover:underline" to={`/lideranca/funcionarios/${item.id_funcionario}`}>
                    Abrir
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

/**
 * Permite a lideranca criar planos e avaliacoes dentro do escopo autorizado.
 */
export function LeadershipEmployeeDetailPage() {
  const { id } = useParams();
  const [error, setError] = useState('');
  const [plan, setPlan] = useState({ descricao: '', requisitos: '' });
  const [review, setReview] = useState({ categoria: '', nota: '', comentario: '', data_avaliacao: '' });
  const queryClient = useQueryClient();

  const plans = useQuery({
    queryKey: ['leadership-plans', id],
    queryFn: () => listResource<ApiRecord>(`/funcionario/funcionarios/${id}/lideranca/planos-carreira/`, {}),
  });

  const createPlan = useMutation({
    mutationFn: () => api.post(`/funcionario/funcionarios/${id}/lideranca/criar-plano-carreira/`, plan),
    onSuccess: () => {
      setPlan({ descricao: '', requisitos: '' });
      void queryClient.invalidateQueries({ queryKey: ['leadership-plans', id] });
    },
    onError: (mutationError) => setError(extractApiError(mutationError)),
  });

  const createReview = useMutation({
    mutationFn: () => api.post(`/funcionario/funcionarios/${id}/lideranca/criar-avaliacao-desempenho/`, review),
    onSuccess: () => setReview({ categoria: '', nota: '', comentario: '', data_avaliacao: '' }),
    onError: (mutationError) => setError(extractApiError(mutationError)),
  });

  return (
    <section>
      <PageHeader title="Detalhe para liderança" description="Ações permitidas para funcionário do setor." />
      {error ? <pre className="mb-4 whitespace-pre-wrap rounded-md bg-red-50 p-3 font-sans text-sm text-danger">{error}</pre> : null}
      <div className="grid gap-4 xl:grid-cols-2">
        <section className="rounded-md border border-line bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
          <h2 className="mb-4 font-semibold text-ink dark:text-slate-100">Planos de carreira</h2>
          {plans.isLoading ? <p className="text-sm text-muted">Carregando...</p> : null}
          <div className="mb-4 space-y-2">
            {plans.data?.results.map((item, index) => (
              <pre key={index} className="overflow-auto rounded-md bg-panel p-3 text-xs">{JSON.stringify(item, null, 2)}</pre>
            ))}
          </div>
          <textarea
            className="focus-ring mb-2 min-h-20 w-full rounded-md border border-line p-2 text-sm"
            placeholder="Descrição"
            value={plan.descricao}
            onChange={(event) => setPlan((current) => ({ ...current, descricao: event.target.value }))}
          />
          <textarea
            className="focus-ring mb-3 min-h-20 w-full rounded-md border border-line p-2 text-sm"
            placeholder="Requisitos"
            value={plan.requisitos}
            onChange={(event) => setPlan((current) => ({ ...current, requisitos: event.target.value }))}
          />
          <Button onClick={() => createPlan.mutate()} disabled={createPlan.isPending}>Criar plano</Button>
        </section>
        <section className="rounded-md border border-line bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
          <h2 className="mb-4 font-semibold text-ink dark:text-slate-100">Nova avaliação</h2>
          {(['categoria', 'nota', 'data_avaliacao'] as const).map((field) => (
            <input
              key={field}
              className="focus-ring mb-2 w-full rounded-md border border-line p-2 text-sm"
              placeholder={field.replaceAll('_', ' ')}
              type={field === 'data_avaliacao' ? 'date' : field === 'nota' ? 'number' : 'text'}
              value={review[field]}
              onChange={(event) => setReview((current) => ({ ...current, [field]: event.target.value }))}
            />
          ))}
          <textarea
            className="focus-ring mb-3 min-h-24 w-full rounded-md border border-line p-2 text-sm"
            placeholder="Comentário"
            value={review.comentario}
            onChange={(event) => setReview((current) => ({ ...current, comentario: event.target.value }))}
          />
          <Button onClick={() => createReview.mutate()} disabled={createReview.isPending}>Criar avaliação</Button>
        </section>
      </div>
    </section>
  );
}
