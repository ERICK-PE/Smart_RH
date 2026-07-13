import { Bell, Check, Send, X } from 'lucide-react';
import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth/AuthContext';
import { api, extractApiError } from '../services/api';

type BehavioralQuestion = {
  id: string;
  titulo: string;
  pergunta: string;
  tipo: 'select' | 'textarea';
  opcoes?: string[];
  obrigatoria?: boolean;
};

type BehavioralPendingForm = {
  id_resposta: number;
  titulo: string;
  perguntas: BehavioralQuestion[];
  criado_em: string;
};

function emptyAnswers(form?: BehavioralPendingForm) {
  return Object.fromEntries((form?.perguntas ?? []).map((question) => [question.id, '']));
}

export function BehavioralAnalysisNotifications() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const canReceive = Boolean(user && user.profile !== 'candidato');

  const query = useQuery({
    queryKey: ['behavioral-analysis-pending'],
    queryFn: async () => {
      const response = await api.get<BehavioralPendingForm[]>('/avaliacao/analises-comportamentais/pendentes/');
      return response.data;
    },
    enabled: canReceive,
    refetchInterval: 30000,
  });

  const pending = query.data ?? [];
  const selected = useMemo(() => {
    if (!pending.length) return undefined;
    return pending.find((form) => form.id_resposta === selectedId) ?? pending[0];
  }, [pending, selectedId]);

  useEffect(() => {
    if (!selected) {
      setSelectedId(null);
      setAnswers({});
      return;
    }
    setSelectedId(selected.id_resposta);
    setAnswers(emptyAnswers(selected));
    setError(null);
  }, [selected?.id_resposta]);

  useEffect(() => {
    if (!open) return;

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setOpen(false);
      }
    }

    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [open]);

  const submitMutation = useMutation({
    mutationFn: async () => {
      if (!selected) return null;
      return api.post(
        `/avaliacao/analises-comportamentais/respostas/${selected.id_resposta}/responder/`,
        { respostas: answers },
      );
    },
    onSuccess: () => {
      setError(null);
      void queryClient.invalidateQueries({ queryKey: ['behavioral-analysis-pending'] });
    },
    onError: (mutationError) => setError(extractApiError(mutationError)),
  });

  if (!canReceive) return null;

  function updateAnswer(questionId: string, value: string) {
    setAnswers((current) => ({ ...current, [questionId]: value }));
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    submitMutation.mutate();
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={`focus-ring relative inline-flex h-10 w-10 items-center justify-center rounded-md border transition-colors ${
          pending.length
            ? 'border-brand bg-brand text-white hover:bg-[#2f90c8]'
            : 'border-line bg-white text-ink hover:bg-panel dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800'
        }`}
        aria-label="Analises comportamentais pendentes"
        title="Analises comportamentais pendentes"
      >
        <Bell className="h-4 w-4" />
        {pending.length ? (
          <span className="absolute -right-1.5 -top-1.5 min-w-5 rounded-full bg-red-600 px-1.5 py-0.5 text-center text-[11px] font-bold text-white">
            {pending.length}
          </span>
        ) : null}
      </button>

      {open ? (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center bg-ink/35 px-4 pb-4 pt-[6.25rem]"
          onMouseDown={() => setOpen(false)}
        >
          <div
            className="relative max-h-[calc(100vh-7.5rem)] w-full max-w-3xl overflow-auto rounded-md bg-white shadow-soft dark:bg-slate-950"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="focus-ring absolute right-3 top-3 z-10 rounded-md p-2 text-muted hover:bg-panel dark:text-slate-400 dark:hover:bg-slate-800"
              aria-label="Fechar"
              title="Fechar"
            >
              <X className="h-4 w-4" />
            </button>
            <div className="flex items-center justify-between border-b border-line px-5 py-4 pr-14 dark:border-slate-700">
              <div>
                <h2 className="text-base font-semibold text-ink dark:text-slate-100">Analise comportamental</h2>
                <p className="text-sm text-muted dark:text-slate-400">
                  {pending.length ? `${pending.length} formulario(s) pendente(s).` : 'Nenhum formulario pendente.'}
                </p>
              </div>
            </div>

            <div className="p-5">
              {pending.length > 1 ? (
                <div className="mb-4 flex flex-wrap gap-2">
                  {pending.map((form) => (
                    <button
                      key={form.id_resposta}
                      type="button"
                      onClick={() => setSelectedId(form.id_resposta)}
                      className={`focus-ring rounded-md px-3 py-2 text-sm font-semibold ${
                        selected?.id_resposta === form.id_resposta
                          ? 'bg-brand text-white'
                          : 'border border-line bg-white text-ink hover:bg-panel dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800'
                      }`}
                    >
                      Formulario {form.id_resposta}
                    </button>
                  ))}
                </div>
              ) : null}

              {selected ? (
                <form onSubmit={submit} className="space-y-4">
                  {selected.perguntas.map((question) => (
                    <label key={question.id} className="block">
                      <span className="mb-1 block text-xs font-semibold uppercase text-muted dark:text-slate-400">
                        {question.titulo}
                      </span>
                      <span className="mb-2 block text-sm font-medium text-ink dark:text-slate-100">
                        {question.pergunta}
                      </span>
                      {question.tipo === 'textarea' ? (
                        <textarea
                          className="focus-ring min-h-24 w-full rounded-md border border-line bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                          value={answers[question.id] ?? ''}
                          required={question.obrigatoria !== false}
                          onChange={(event) => updateAnswer(question.id, event.target.value)}
                        />
                      ) : (
                        <select
                          className="focus-ring w-full rounded-md border border-line bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                          value={answers[question.id] ?? ''}
                          required={question.obrigatoria !== false}
                          onChange={(event) => updateAnswer(question.id, event.target.value)}
                        >
                          <option value="">Selecione</option>
                          {question.opcoes?.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </select>
                      )}
                    </label>
                  ))}

                  {error ? (
                    <div className="rounded-md border border-danger/30 bg-red-50 p-3 text-sm text-danger">
                      {error}
                    </div>
                  ) : null}

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={submitMutation.isPending}
                      className="focus-ring inline-flex items-center gap-2 rounded-md bg-brand px-3 py-2 text-sm font-semibold text-white hover:bg-[#2f90c8] disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {submitMutation.isPending ? <Check className="h-4 w-4" /> : <Send className="h-4 w-4" />}
                      Enviar respostas
                    </button>
                  </div>
                </form>
              ) : (
                <div className="rounded-md border border-line bg-panel p-4 text-sm text-muted dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
                  Sem formulario para responder agora.
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
