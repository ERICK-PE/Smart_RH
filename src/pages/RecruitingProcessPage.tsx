import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Mail, RefreshCw } from 'lucide-react';
import { useMemo, useState, type FormEvent } from 'react';
import { useParams } from 'react-router-dom';
import { api, extractApiError, listResource } from '../services/api';
import type { ApiRecord } from '../types';
import { displayValue } from '../utils/formatters';
import { PageState } from '../components/PageState';
import { Button, PageHeader, SensitiveValue } from '../components/ui';

type EmailTarget = 'aprovados' | 'reprovados' | 'selecionados';

const processStatusOptions = [
  'andamento',
  'em_analise_rh',
  'entrevista',
  'aprovado',
  'reprovado',
];
const PAGE_SIZE = 50;

function asCpf(item: ApiRecord) {
  return String(item.cpf_candidato ?? '');
}

function getCandidateKey(item: ApiRecord, index: number) {
  return `${asCpf(item)}-${String(item.id_vaga ?? 'vaga')}-${index}`;
}

function CandidateProcessTable({
  title,
  description,
  rows,
  total,
  hasMore,
  loadingMore,
  onLoadMore,
  showUpdate,
  statuses,
  onStatusChange,
  onSaveStatus,
}: {
  title: string;
  description: string;
  rows: ApiRecord[];
  total?: number;
  hasMore?: boolean;
  loadingMore?: boolean;
  onLoadMore?: () => void;
  showUpdate?: boolean;
  statuses?: Record<string, string>;
  onStatusChange?: (cpf: string, status: string) => void;
  onSaveStatus?: (cpf: string, status: string) => void;
}) {
  return (
    <section className="rounded-md border border-line bg-white dark:border-slate-700 dark:bg-slate-950">
      <div className="border-b border-line px-4 py-3 dark:border-slate-700">
        <h2 className="text-base font-semibold text-ink dark:text-slate-100">{title}</h2>
        <p className="mt-1 text-sm text-muted dark:text-slate-400">{description}</p>
        {typeof total === 'number' ? (
          <p className="mt-2 text-xs font-semibold uppercase text-muted dark:text-slate-400">
            {rows.length} de {total} carregados
          </p>
        ) : null}
      </div>
      {rows.length === 0 ? (
        <div className="p-4 text-sm text-muted dark:text-slate-400">Nenhum candidato nesta lista.</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-line text-sm dark:divide-slate-700">
            <thead className="bg-panel dark:bg-slate-900">
              <tr>
                <th className="px-4 py-3 text-left">CPF</th>
                <th className="px-4 py-3 text-left">Status processo</th>
                <th className="px-4 py-3 text-left">Classificacao</th>
                <th className="px-4 py-3 text-left">Pontuacao</th>
                <th className="px-4 py-3 text-left">Motivo triagem</th>
                {showUpdate ? <th className="px-4 py-3 text-right">Atualizar</th> : null}
              </tr>
            </thead>
            <tbody className="divide-y divide-line dark:divide-slate-700">
              {rows.map((item, index) => {
                const cpf = asCpf(item);
                const currentStatus = statuses?.[cpf] ?? String(item.status_processo ?? '');
                return (
                  <tr key={getCandidateKey(item, index)} className="align-top">
                    <td className="px-4 py-3"><SensitiveValue value={item.cpf_candidato} /></td>
                    <td className="px-4 py-3"><SensitiveValue value={item.status_processo} /></td>
                    <td className="px-4 py-3"><SensitiveValue value={item.triagem_automatica_classificacao} /></td>
                    <td className="px-4 py-3"><SensitiveValue value={item.triagem_automatica_pontuacao} /></td>
                    <td className="max-w-md px-4 py-3">
                      <SensitiveValue value={item.triagem_automatica_motivo} />
                    </td>
                    {showUpdate ? (
                      <td className="px-4 py-3">
                        <div className="flex justify-end gap-2">
                          <select
                            className="focus-ring w-44 rounded-md border border-line bg-white px-2 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                            value={currentStatus}
                            onChange={(event) => onStatusChange?.(cpf, event.target.value)}
                          >
                            <option value="">Selecione</option>
                            {processStatusOptions.map((status) => (
                              <option key={status} value={status}>
                                {status.replaceAll('_', ' ')}
                              </option>
                            ))}
                          </select>
                          <Button onClick={() => onSaveStatus?.(cpf, currentStatus)}>Salvar</Button>
                        </div>
                      </td>
                    ) : null}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      {hasMore ? (
        <div className="flex justify-end border-t border-line px-4 py-3 dark:border-slate-700">
          <Button variant="secondary" disabled={loadingMore} onClick={onLoadMore}>
            Carregar mais {PAGE_SIZE}
          </Button>
        </div>
      ) : null}
    </section>
  );
}

function flattenPages(query: { data?: { pages: Array<{ results: ApiRecord[] }> } }) {
  return query.data?.pages.flatMap((page) => page.results) ?? [];
}

function totalFromPages(query: { data?: { pages: Array<{ count: number }> } }) {
  return query.data?.pages[0]?.count ?? 0;
}

function filterCandidateRows(rows: ApiRecord[], filter: string) {
  const normalized = filter.trim().toLowerCase();
  if (!normalized) return rows;
  return rows.filter((item) => [
    item.cpf_candidato,
    item.status_processo,
    item.triagem_automatica_classificacao,
    item.triagem_automatica_pontuacao,
  ].some((value) => displayValue(value).toLowerCase().includes(normalized)));
}

/**
 * Tela RH para acompanhar triagem, ranking e comunicacao por vaga.
 */
export function RecruitingProcessPage() {
  const { id } = useParams();
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [statuses, setStatuses] = useState<Record<string, string>>({});
  const [selectedCpfs, setSelectedCpfs] = useState<Record<string, boolean>>({});
  const [manualFilter, setManualFilter] = useState('');
  const [emailTarget, setEmailTarget] = useState<EmailTarget>('aprovados');
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const queryClient = useQueryClient();

  const approvedQuery = useInfiniteQuery({
    queryKey: ['recruiting-approved', id],
    queryFn: ({ pageParam }) => listResource<ApiRecord>(`/candidato/vagas/${id}/rh/candidatos/`, {
      page: pageParam,
      page_size: PAGE_SIZE,
    }),
    initialPageParam: 1,
    getNextPageParam: (lastPage, pages) => (lastPage.next ? pages.length + 1 : undefined),
    enabled: Boolean(id),
  });
  const reviewQuery = useInfiniteQuery({
    queryKey: ['recruiting-review', id],
    queryFn: ({ pageParam }) => listResource<ApiRecord>(`/candidato/vagas/${id}/rh/triagem-revisao/`, {
      page: pageParam,
      page_size: PAGE_SIZE,
    }),
    initialPageParam: 1,
    getNextPageParam: (lastPage, pages) => (lastPage.next ? pages.length + 1 : undefined),
    enabled: Boolean(id),
  });
  const processesQuery = useInfiniteQuery({
    queryKey: ['recruiting-process', id],
    queryFn: ({ pageParam }) => listResource<ApiRecord>(`/candidato/vagas/${id}/rh/processos/`, {
      page: pageParam,
      page_size: PAGE_SIZE,
    }),
    initialPageParam: 1,
    getNextPageParam: (lastPage, pages) => (lastPage.next ? pages.length + 1 : undefined),
    enabled: Boolean(id),
  });

  const approvedRows = flattenPages(approvedQuery);
  const reviewRows = flattenPages(reviewQuery);
  const allRows = flattenPages(processesQuery);
  const filteredManualRows = useMemo(() => filterCandidateRows(allRows, manualFilter), [allRows, manualFilter]);
  const selectedCpfList = useMemo(
    () => Object.entries(selectedCpfs).filter(([, selected]) => selected).map(([cpf]) => cpf),
    [selectedCpfs],
  );

  const update = useMutation({
    mutationFn: ({ cpf, status }: { cpf: string; status: string }) =>
      api.patch(`/candidato/vagas/${id}/rh/processos/${cpf}/`, { status_processo: status }),
    onSuccess: () => {
      setError('');
      setSuccess('Status atualizado.');
      void queryClient.invalidateQueries({ queryKey: ['recruiting-process', id] });
      void queryClient.invalidateQueries({ queryKey: ['recruiting-approved', id] });
      void queryClient.invalidateQueries({ queryKey: ['recruiting-review', id] });
    },
    onError: (mutationError) => setError(extractApiError(mutationError)),
  });

  const sendEmail = useMutation({
    mutationFn: () => api.post(`/candidato/vagas/${id}/rh/enviar-email-candidatos/`, {
      tipo_destinatarios: emailTarget,
      assunto: subject,
      mensagem: message,
      ...(emailTarget === 'selecionados' ? { cpf_candidatos: selectedCpfList } : {}),
    }),
    onSuccess: (response) => {
      setError('');
      const data = response.data as ApiRecord;
      setSuccess(
        `E-mail enviado. Candidaturas: ${displayValue(data.total_candidaturas)}. Enviados: ${displayValue(data.total_enviados)}. Sem e-mail: ${displayValue(data.total_sem_email)}.`,
      );
    },
    onError: (mutationError) => setError(extractApiError(mutationError)),
  });

  function submitEmail(event: FormEvent) {
    event.preventDefault();
    setSuccess('');
    setError('');
    if (emailTarget === 'selecionados' && selectedCpfList.length === 0) {
      setError('Selecione ao menos um candidato para envio especifico.');
      return;
    }
    sendEmail.mutate();
  }

  const loading = approvedQuery.isLoading || reviewQuery.isLoading || processesQuery.isLoading;
  const failed = approvedQuery.isError || reviewQuery.isError || processesQuery.isError;
  if (loading) return <PageState title="Carregando triagem" />;
  if (failed) return <PageState title="Nao foi possivel carregar triagem" variant="error" />;

  return (
    <section>
      <PageHeader
        title="Triagem e processos da vaga"
        description="Ranking de aprovados, revisao de falsos negativos, status do processo e envio de e-mail pelo RH."
        action={
          <Button
            variant="secondary"
            onClick={() => {
              void approvedQuery.refetch();
              void reviewQuery.refetch();
              void processesQuery.refetch();
            }}
          >
            <RefreshCw className="h-4 w-4" />
            Atualizar
          </Button>
        }
      />

      {error ? <pre className="mb-4 whitespace-pre-wrap rounded-md bg-red-50 p-3 font-sans text-sm text-danger dark:bg-red-950/30">{error}</pre> : null}
      {success ? <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-200">{success}</div> : null}

      <div className="mb-6 grid gap-4 xl:grid-cols-3">
        <div className="rounded-md border border-line bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
          <p className="text-xs font-semibold uppercase text-muted">Aprovados triagem</p>
          <p className="mt-2 text-3xl font-semibold text-ink dark:text-slate-100">{totalFromPages(approvedQuery)}</p>
        </div>
        <div className="rounded-md border border-line bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
          <p className="text-xs font-semibold uppercase text-muted">Revisao RH</p>
          <p className="mt-2 text-3xl font-semibold text-ink dark:text-slate-100">{totalFromPages(reviewQuery)}</p>
        </div>
        <div className="rounded-md border border-line bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
          <p className="text-xs font-semibold uppercase text-muted">Total processos</p>
          <p className="mt-2 text-3xl font-semibold text-ink dark:text-slate-100">{totalFromPages(processesQuery)}</p>
        </div>
      </div>

      <div className="grid gap-6">
        <CandidateProcessTable
          title="Candidatos aprovados"
          description="Lista principal para analise RH, ordenada pelo melhor score da triagem."
          rows={approvedRows}
          total={totalFromPages(approvedQuery)}
          hasMore={approvedQuery.hasNextPage}
          loadingMore={approvedQuery.isFetchingNextPage}
          onLoadMore={() => void approvedQuery.fetchNextPage()}
        />
        <CandidateProcessTable
          title="Revisao de triagem"
          description="Pendentes e reprovados tecnicos ficam aqui para revisao manual do RH."
          rows={reviewRows}
          total={totalFromPages(reviewQuery)}
          hasMore={reviewQuery.hasNextPage}
          loadingMore={reviewQuery.isFetchingNextPage}
          onLoadMore={() => void reviewQuery.fetchNextPage()}
        />
        <CandidateProcessTable
          title="Todos os processos"
          description="Atualize status visivel do processo seletivo sem alterar score interno da triagem."
          rows={allRows}
          total={totalFromPages(processesQuery)}
          hasMore={processesQuery.hasNextPage}
          loadingMore={processesQuery.isFetchingNextPage}
          onLoadMore={() => void processesQuery.fetchNextPage()}
          showUpdate
          statuses={statuses}
          onStatusChange={(cpf, status) => setStatuses((current) => ({ ...current, [cpf]: status }))}
          onSaveStatus={(cpf, status) => update.mutate({ cpf, status })}
        />

        <section className="rounded-md border border-line bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
          <h2 className="text-base font-semibold text-ink dark:text-slate-100">Envio de e-mail</h2>
          <p className="mt-1 text-sm text-muted dark:text-slate-400">
            Destinatarios saem das candidaturas da vaga. Backend nao aceita e-mail externo no payload.
          </p>
          <form onSubmit={submitEmail} className="mt-4 grid gap-4">
            <label>
              <span className="mb-1 block text-sm font-medium text-ink dark:text-slate-100">Destinatarios</span>
              <select
                className="focus-ring w-full rounded-md border border-line bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                value={emailTarget}
                onChange={(event) => setEmailTarget(event.target.value as EmailTarget)}
              >
                <option value="aprovados">Todos aprovados</option>
                <option value="reprovados">Todos reprovados tecnicos</option>
                <option value="selecionados">Selecao manual</option>
              </select>
            </label>

            {emailTarget === 'selecionados' ? (
              <div className="rounded-md border border-line bg-panel p-3 dark:border-slate-700 dark:bg-slate-900">
                <div className="mb-3 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
                  <label className="flex-1">
                    <span className="mb-1 block text-sm font-medium text-ink dark:text-slate-100">Filtrar candidatos carregados</span>
                    <input
                      className="focus-ring w-full rounded-md border border-line bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                      placeholder="CPF, status, classificacao ou pontuacao"
                      value={manualFilter}
                      onChange={(event) => setManualFilter(event.target.value)}
                    />
                  </label>
                  {processesQuery.hasNextPage ? (
                    <Button variant="secondary" disabled={processesQuery.isFetchingNextPage} onClick={() => void processesQuery.fetchNextPage()}>
                      Carregar mais {PAGE_SIZE}
                    </Button>
                  ) : null}
                </div>
                <p className="mb-2 text-sm text-muted dark:text-slate-400">
                  {filteredManualRows.length} candidatos visiveis de {allRows.length} carregados. Total da vaga: {totalFromPages(processesQuery)}.
                </p>
                <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
                  {filteredManualRows.map((item, index) => {
                    const cpf = asCpf(item);
                    return (
                      <label key={getCandidateKey(item, index)} className="flex items-center gap-2 text-sm text-ink dark:text-slate-100">
                        <input
                          type="checkbox"
                          checked={Boolean(selectedCpfs[cpf])}
                          onChange={(event) => setSelectedCpfs((current) => ({ ...current, [cpf]: event.target.checked }))}
                        />
                        {cpf} - {displayValue(item.status_processo)}
                      </label>
                    );
                  })}
                </div>
              </div>
            ) : null}

            <label>
              <span className="mb-1 block text-sm font-medium text-ink dark:text-slate-100">Assunto</span>
              <input
                className="focus-ring w-full rounded-md border border-line bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                value={subject}
                onChange={(event) => setSubject(event.target.value)}
                maxLength={120}
                required
              />
            </label>
            <label>
              <span className="mb-1 block text-sm font-medium text-ink dark:text-slate-100">Mensagem</span>
              <textarea
                className="focus-ring min-h-36 w-full rounded-md border border-line bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                maxLength={5000}
                required
              />
            </label>
            <div className="flex justify-end">
              <Button type="submit" disabled={sendEmail.isPending}>
                <Mail className="h-4 w-4" />
                Enviar e-mail
              </Button>
            </div>
          </form>
        </section>
      </div>
    </section>
  );
}
