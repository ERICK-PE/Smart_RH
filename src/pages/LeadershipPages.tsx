import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Pencil, X } from 'lucide-react';
import { useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { PageState } from '../components/PageState';
import { Button, PageHeader, SensitiveValue } from '../components/ui';
import { api, extractApiError, listResource } from '../services/api';
import type { ApiRecord } from '../types';

type DisplayField = {
  key: string;
  label: string;
};

const leadershipPlanFields: DisplayField[] = [
  { key: 'fk_id_cargo', label: 'Cargo vinculado' },
  { key: 'descricao', label: 'Descricao' },
  { key: 'requisitos', label: 'Requisitos' },
];

const leadershipReviewFields: DisplayField[] = [
  { key: 'fk_id_avaliador', label: 'Avaliador' },
  { key: 'categoria', label: 'Categoria' },
  { key: 'nota', label: 'Nota' },
  { key: 'data_avaliacao', label: 'Data da avaliacao' },
  { key: 'comentario', label: 'Comentario' },
];

const avaliacaoCategoriaOptions = ['90º', '180º', '360º'];

function asText(value: unknown) {
  if (value === null || value === undefined || value === '') return 'Nao informado';
  if (typeof value === 'object') {
    const record = value as ApiRecord;
    return String(record.nome ?? record.name ?? 'Relacionado');
  }
  return String(value);
}

function asNumber(value: unknown) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatChartDate(value: unknown) {
  const text = asText(value);
  if (text === 'Nao informado') return text;
  const [year, month, day] = text.split('-');
  return year && month && day ? `${day}/${month}/${year}` : text;
}

function FieldGrid({ record, fields }: { record: ApiRecord; fields: DisplayField[] }) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      {fields.map((field) => (
        <div key={field.key}>
          <p className="text-xs font-semibold uppercase text-muted dark:text-slate-400">{field.label}</p>
          <p className="mt-1 text-sm text-ink dark:text-slate-100">
            <SensitiveValue value={asText(record[field.key])} />
          </p>
        </div>
      ))}
    </div>
  );
}

/**
 * Lista funcionarios do setor permitido para lideranca.
 */
export function LeadershipTeamPage() {
  const query = useQuery({
    queryKey: ['leadership-team'],
    queryFn: () => listResource<ApiRecord>('/funcionario/funcionarios/lideranca/funcionarios-setor/', {}),
  });

  if (query.isLoading) return <PageState title="Carregando equipe" />;
  if (query.isError) return <PageState title="Nao foi possivel carregar a equipe" variant="error" />;

  const sectorName = asText(query.data?.results?.[0]?.fk_id_setor);
  const pageTitle = sectorName === 'Nao informado' ? 'Setor' : sectorName;

  return (
    <section>
      <PageHeader title={pageTitle} description="Funcionarios disponiveis conforme escopo do backend." />
      <div className="overflow-hidden rounded-md border border-line bg-white dark:border-slate-700 dark:bg-slate-950">
        <table className="min-w-full divide-y divide-line text-sm">
          <thead className="bg-panel dark:bg-slate-900">
            <tr>
              <th className="px-4 py-3 text-left">Nome</th>
              <th className="px-4 py-3 text-left">Status</th>
              <th className="px-4 py-3 text-left">Plano de carreira</th>
              <th className="px-4 py-3 text-left">Avaliacao de desempenho</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line dark:divide-slate-700">
            {query.data?.results.map((item) => (
              <tr key={String(item.id_funcionario)}>
                <td className="px-4 py-3"><SensitiveValue value={item.nome} /></td>
                <td className="px-4 py-3"><SensitiveValue value={item.status} /></td>
                <td className="px-4 py-3">
                  <Link className="font-semibold text-brand hover:underline" to={`/lideranca/funcionarios/${item.id_funcionario}?aba=plano`}>
                    Abrir plano
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <Link className="font-semibold text-brand hover:underline" to={`/lideranca/funcionarios/${item.id_funcionario}?aba=avaliacao`}>
                    Abrir avaliacao
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
 * Permite a lideranca criar/editar planos e criar avaliacoes dentro do escopo autorizado.
 */
export function LeadershipEmployeeDetailPage() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const activeTab = searchParams.get('aba') === 'avaliacao' ? 'avaliacao' : 'plano';
  const [error, setError] = useState('');
  const [plan, setPlan] = useState({ descricao: '', requisitos: '' });
  const [isCreatingPlan, setIsCreatingPlan] = useState(false);
  const [planEdits, setPlanEdits] = useState<Record<string, { descricao: string; requisitos: string }>>({});
  const [editingPlanId, setEditingPlanId] = useState<string | null>(null);
  const [review, setReview] = useState({ categoria: '', nota: '', comentario: '', data_avaliacao: '' });
  const [isCreatingReview, setIsCreatingReview] = useState(false);
  const queryClient = useQueryClient();

  const plans = useQuery({
    queryKey: ['leadership-plans', id],
    queryFn: () => listResource<ApiRecord>(`/funcionario/funcionarios/${id}/lideranca/planos-carreira/`, {}),
  });

  const reviews = useQuery({
    queryKey: ['leadership-reviews', id],
    queryFn: () => listResource<ApiRecord>(`/funcionario/funcionarios/${id}/lideranca/avaliacoes-desempenho/`, {}),
    enabled: Boolean(id) && activeTab === 'avaliacao',
  });

  const createPlan = useMutation({
    mutationFn: () => api.post(`/funcionario/funcionarios/${id}/lideranca/criar-plano-carreira/`, plan),
    onSuccess: () => {
      setPlan({ descricao: '', requisitos: '' });
      setIsCreatingPlan(false);
      void queryClient.invalidateQueries({ queryKey: ['leadership-plans', id] });
    },
    onError: (mutationError) => setError(extractApiError(mutationError)),
  });

  const updatePlan = useMutation({
    mutationFn: ({ planId, payload }: { planId: string; payload: { descricao: string; requisitos: string } }) =>
      api.patch(`/funcionario/funcionarios/${id}/lideranca/planos-carreira/${planId}/editar/`, payload),
    onSuccess: () => {
      setEditingPlanId(null);
      setPlanEdits({});
      void queryClient.invalidateQueries({ queryKey: ['leadership-plans', id] });
    },
    onError: (mutationError) => setError(extractApiError(mutationError)),
  });

  const createReview = useMutation({
    mutationFn: () => api.post(`/funcionario/funcionarios/${id}/lideranca/criar-avaliacao-desempenho/`, review),
    onSuccess: () => {
      setReview({ categoria: '', nota: '', comentario: '', data_avaliacao: '' });
      setIsCreatingReview(false);
      void queryClient.invalidateQueries({ queryKey: ['leadership-reviews', id] });
    },
    onError: (mutationError) => setError(extractApiError(mutationError)),
  });

  const reviewItems = reviews.data?.results ?? [];
  const reviewScores = reviewItems.map((item) => asNumber(item.nota)).filter((score): score is number => score !== null);
  const reviewAverage = reviewScores.length
    ? reviewScores.reduce((total, score) => total + score, 0) / reviewScores.length
    : null;
  const chartItems = reviewItems
    .map((item, index) => ({
      key: String(item.id_avaliacao ?? index),
      date: asText(item.data_avaliacao),
      label: formatChartDate(item.data_avaliacao),
      score: asNumber(item.nota),
    }))
    .filter((item): item is { key: string; date: string; label: string; score: number } => item.score !== null)
    .sort((a, b) => a.date.localeCompare(b.date));
  const chartWidth = 760;
  const chartHeight = 280;
  const chartPadding = { top: 20, right: 28, bottom: 58, left: 52 };
  const chartInnerWidth = chartWidth - chartPadding.left - chartPadding.right;
  const chartInnerHeight = chartHeight - chartPadding.top - chartPadding.bottom;
  const chartPoints = chartItems.map((item, index) => {
    const x = chartItems.length === 1
      ? chartPadding.left + chartInnerWidth / 2
      : chartPadding.left + (index * chartInnerWidth) / (chartItems.length - 1);
    const y = chartPadding.top + ((10 - item.score) / 10) * chartInnerHeight;
    return { ...item, x, y };
  });
  const chartLinePoints = chartPoints.map((point) => `${point.x},${point.y}`).join(' ');

  return (
    <section>
      <PageHeader title="Detalhe para lideranca" description="Acoes permitidas para funcionario do setor." />
      {error ? <pre className="mb-4 whitespace-pre-wrap rounded-md bg-red-50 p-3 font-sans text-sm text-danger">{error}</pre> : null}

      <div className="mb-4 flex flex-wrap gap-2">
        <Link
          to={`/lideranca/funcionarios/${id}?aba=plano`}
          className={`rounded-md border px-3 py-2 text-sm font-semibold ${
            activeTab === 'plano'
              ? 'border-brand bg-brand text-white'
              : 'border-line bg-white text-ink hover:bg-panel dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100'
          }`}
        >
          Plano de carreira
        </Link>
        <Link
          to={`/lideranca/funcionarios/${id}?aba=avaliacao`}
          className={`rounded-md border px-3 py-2 text-sm font-semibold ${
            activeTab === 'avaliacao'
              ? 'border-brand bg-brand text-white'
              : 'border-line bg-white text-ink hover:bg-panel dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100'
          }`}
        >
          Avaliacao de desempenho
        </Link>
      </div>

      {activeTab === 'plano' ? (
        <section className="rounded-md border border-line bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
          <h2 className="mb-4 font-semibold text-ink dark:text-slate-100">Planos de carreira</h2>
          {plans.isLoading ? <p className="text-sm text-muted">Carregando...</p> : null}
          <div className="mb-4 space-y-2">
            {plans.data?.results.map((item, index) => {
              const planId = String(item.id_plano ?? index);
              const edit = planEdits[planId] ?? {
                descricao: String(item.descricao ?? ''),
                requisitos: String(item.requisitos ?? ''),
              };
              const canEdit = item.pode_editar === true;
              const isEditing = editingPlanId === planId;

              return (
                <article
                  key={planId}
                  className="rounded-md border border-line bg-panel p-3 dark:border-slate-700 dark:bg-slate-900"
                >
                  <div className="flex items-start gap-3">
                    <div className="min-w-0 flex-1">
                      <FieldGrid record={item} fields={leadershipPlanFields} />
                    </div>
                    {canEdit ? (
                      isEditing ? (
                        <button
                          type="button"
                          onClick={() => setEditingPlanId(null)}
                          className="focus-ring inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-brand bg-brand text-white shadow-sm hover:bg-brand/90"
                          aria-label="Cancelar edicao do plano"
                          title="Cancelar edicao"
                        >
                          <X className="h-5 w-5" />
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => {
                            setPlanEdits((current) => ({
                              ...current,
                              [planId]: edit,
                            }));
                            setEditingPlanId(planId);
                          }}
                          className="focus-ring inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-brand bg-brand text-white shadow-sm hover:bg-brand/90"
                          aria-label="Editar plano de carreira"
                          title="Editar plano"
                        >
                          <Pencil className="h-5 w-5" />
                        </button>
                      )
                    ) : null}
                  </div>
                  {canEdit && isEditing ? (
                    <div className="mt-4 space-y-2">
                      <textarea
                        className="focus-ring min-h-20 w-full rounded-md border border-line bg-white p-2 text-sm text-ink dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
                        value={edit.descricao}
                        onChange={(event) =>
                          setPlanEdits((current) => ({
                            ...current,
                            [planId]: { ...edit, descricao: event.target.value },
                          }))
                        }
                        placeholder="Descricao"
                      />
                      <textarea
                        className="focus-ring min-h-20 w-full rounded-md border border-line bg-white p-2 text-sm text-ink dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
                        value={edit.requisitos}
                        onChange={(event) =>
                          setPlanEdits((current) => ({
                            ...current,
                            [planId]: { ...edit, requisitos: event.target.value },
                          }))
                        }
                        placeholder="Requisitos"
                      />
                      <Button
                        onClick={() => updatePlan.mutate({ planId, payload: edit })}
                        disabled={updatePlan.isPending}
                      >
                        Salvar plano
                      </Button>
                    </div>
                  ) : null}
                </article>
              );
            })}
          </div>
          {!isCreatingPlan ? (
            <Button onClick={() => setIsCreatingPlan(true)}>Criar plano</Button>
          ) : (
            <div className="space-y-2">
              <textarea
                className="focus-ring min-h-20 w-full rounded-md border border-line p-2 text-sm"
                placeholder="Descricao"
                value={plan.descricao}
                onChange={(event) => setPlan((current) => ({ ...current, descricao: event.target.value }))}
              />
              <textarea
                className="focus-ring min-h-20 w-full rounded-md border border-line p-2 text-sm"
                placeholder="Requisitos"
                value={plan.requisitos}
                onChange={(event) => setPlan((current) => ({ ...current, requisitos: event.target.value }))}
              />
              <Button onClick={() => createPlan.mutate()} disabled={createPlan.isPending}>Salvar plano</Button>
              <button
                type="button"
                onClick={() => {
                  setPlan({ descricao: '', requisitos: '' });
                  setIsCreatingPlan(false);
                }}
                className="focus-ring ml-2 inline-flex h-9 w-9 items-center justify-center rounded-md border border-line text-muted hover:bg-panel hover:text-ink dark:border-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
                aria-label="Cancelar criacao do plano"
                title="Cancelar criacao"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}
        </section>
      ) : null}

      {activeTab === 'avaliacao' ? (
        <section className="rounded-md border border-line bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-semibold text-ink dark:text-slate-100">Avaliacoes de desempenho</h2>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <div className="rounded-md border border-line bg-panel px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900">
                <span className="text-muted dark:text-slate-400">Media</span>
                <strong className="ml-2 text-ink dark:text-slate-100">
                  {reviewAverage === null ? 'Sem notas' : reviewAverage.toFixed(2)}
                </strong>
              </div>
              {!isCreatingReview ? (
                <Button onClick={() => setIsCreatingReview(true)}>Criar avaliacao</Button>
              ) : null}
            </div>
          </div>

          {reviews.isLoading ? <p className="text-sm text-muted">Carregando avaliacoes...</p> : null}

          <div className="mb-3 grid gap-3 xl:grid-cols-2">
            {reviewItems.map((item, index) => (
              <article
                key={String(item.id_avaliacao ?? index)}
                className="rounded-md border border-line bg-panel p-3 dark:border-slate-700 dark:bg-slate-900"
              >
                <FieldGrid record={item} fields={leadershipReviewFields} />
              </article>
            ))}
            {!reviews.isLoading && reviewItems.length === 0 ? (
              <p className="rounded-md border border-line bg-panel p-3 text-sm text-muted dark:border-slate-700 dark:bg-slate-900">
                Nenhuma avaliacao cadastrada.
              </p>
            ) : null}
          </div>

          {isCreatingReview ? (
            <div className="rounded-md border border-line bg-panel p-3 dark:border-slate-700 dark:bg-slate-900">
              <div className="mb-3 flex items-start justify-between gap-3">
                <h3 className="font-semibold text-ink dark:text-slate-100">Nova avaliacao</h3>
                <button
                  type="button"
                  onClick={() => {
                    setReview({ categoria: '', nota: '', comentario: '', data_avaliacao: '' });
                    setIsCreatingReview(false);
                  }}
                  className="focus-ring inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-brand bg-brand text-white shadow-sm hover:bg-brand/90"
                  aria-label="Cancelar criacao da avaliacao"
                  title="Cancelar criacao"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <select
                className="focus-ring mb-2 w-full rounded-md border border-line bg-white p-2 text-sm text-ink dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
                value={review.categoria}
                onChange={(event) => setReview((current) => ({ ...current, categoria: event.target.value }))}
              >
                <option value="">Selecione a categoria</option>
                {avaliacaoCategoriaOptions.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
              {(['nota', 'data_avaliacao'] as const).map((field) => (
                <input
                  key={field}
                  className="focus-ring mb-2 w-full rounded-md border border-line bg-white p-2 text-sm text-ink dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
                  placeholder={field.replaceAll('_', ' ')}
                  type={field === 'data_avaliacao' ? 'date' : field === 'nota' ? 'number' : 'text'}
                  min={field === 'nota' ? 0 : undefined}
                  max={field === 'nota' ? 10 : undefined}
                  step={field === 'nota' ? '0.01' : undefined}
                  value={review[field]}
                  onChange={(event) => {
                    const value = event.target.value;
                    const parsedValue = Number(value);
                    const nextValue = field === 'nota' && value !== '' && Number.isFinite(parsedValue)
                      ? String(Math.min(10, Math.max(0, parsedValue)))
                      : value;
                    setReview((current) => ({ ...current, [field]: nextValue }));
                  }}
                />
              ))}
              <textarea
                className="focus-ring mb-3 min-h-24 w-full rounded-md border border-line bg-white p-2 text-sm text-ink dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
                placeholder="Comentario"
                value={review.comentario}
                onChange={(event) => setReview((current) => ({ ...current, comentario: event.target.value }))}
              />
              <Button onClick={() => createReview.mutate()} disabled={createReview.isPending}>Salvar avaliacao</Button>
            </div>
          ) : null}

          <div className="mt-3 rounded-md border border-line bg-panel p-3 dark:border-slate-700 dark:bg-slate-900">
            <h3 className="mb-3 font-semibold text-ink dark:text-slate-100">Grafico de notas</h3>
            {chartPoints.length ? (
              <div className="overflow-x-auto">
                <svg
                  className="h-72 min-w-[640px] text-ink dark:text-slate-100"
                  viewBox={`0 0 ${chartWidth} ${chartHeight}`}
                  role="img"
                  aria-label="Grafico de linha das notas por data de avaliacao"
                >
                  {[0, 2, 4, 6, 8, 10].map((label) => {
                    const y = chartPadding.top + ((10 - label) / 10) * chartInnerHeight;
                    return (
                      <g key={label}>
                        <line
                          x1={chartPadding.left}
                          x2={chartWidth - chartPadding.right}
                          y1={y}
                          y2={y}
                          stroke="currentColor"
                          strokeOpacity="0.16"
                        />
                        <text
                          x={chartPadding.left - 12}
                          y={y + 4}
                          textAnchor="end"
                          className="fill-current text-[11px] font-semibold"
                        >
                          {label}
                        </text>
                      </g>
                    );
                  })}
                  <line
                    x1={chartPadding.left}
                    x2={chartPadding.left}
                    y1={chartPadding.top}
                    y2={chartHeight - chartPadding.bottom}
                    stroke="currentColor"
                    strokeOpacity="0.35"
                  />
                  <line
                    x1={chartPadding.left}
                    x2={chartWidth - chartPadding.right}
                    y1={chartHeight - chartPadding.bottom}
                    y2={chartHeight - chartPadding.bottom}
                    stroke="currentColor"
                    strokeOpacity="0.35"
                  />
                  {chartPoints.length > 1 ? (
                    <polyline
                      points={chartLinePoints}
                      fill="none"
                      stroke="rgb(56 169 219)"
                      strokeWidth="4"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  ) : null}
                  {chartPoints.map((point) => (
                    <g key={point.key}>
                      <circle cx={point.x} cy={point.y} r="6" fill="rgb(56 169 219)" />
                      <text
                        x={point.x}
                        y={point.y - 12}
                        textAnchor="middle"
                        className="fill-current text-[11px] font-semibold"
                      >
                        {point.score.toFixed(1)}
                      </text>
                      <text
                        x={point.x}
                        y={chartHeight - 22}
                        textAnchor="middle"
                        className="fill-current text-[11px] font-semibold"
                      >
                        {point.label}
                      </text>
                    </g>
                  ))}
                </svg>
              </div>
            ) : (
              <p className="text-sm text-muted">Sem notas para gerar grafico.</p>
            )}
          </div>
        </section>
      ) : null}
    </section>
  );
}
