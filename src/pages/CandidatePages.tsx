import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { FileUp, X } from 'lucide-react';
import { useState, type ChangeEvent, type FormEvent } from 'react';
import { useAuth } from '../auth/AuthContext';
import { api, extractApiError, listResource } from '../services/api';
import type { ApiRecord } from '../types';
import { PageState } from '../components/PageState';
import { Button, PageHeader } from '../components/ui';
import { displayValue } from '../utils/formatters';

const MAX_RESUME_FILE_SIZE = 5 * 1024 * 1024;
const RESUME_ACCEPT = '.pdf,.doc,.docx';
const RESUME_ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx'];
const RESUME_ALLOWED_CONTENT_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
];

function formatFileSize(size: number) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function resumeExtension(file: File) {
  const index = file.name.lastIndexOf('.');
  return index >= 0 ? file.name.slice(index).toLowerCase() : '';
}

function resumeDisplayName(path: string) {
  return path.split(/[\\/]/).filter(Boolean).pop() || path;
}

function validateResumeFile(file: File) {
  if (!RESUME_ALLOWED_EXTENSIONS.includes(resumeExtension(file))) {
    return 'Curriculo deve ser PDF, DOC ou DOCX.';
  }
  if (file.type && !RESUME_ALLOWED_CONTENT_TYPES.includes(file.type)) {
    return 'Tipo de arquivo do curriculo nao permitido.';
  }
  if (file.size > MAX_RESUME_FILE_SIZE) {
    return 'Curriculo deve ter no maximo 5MB.';
  }
  return '';
}

/**
 * Converte valores relacionais da API para objeto quando possivel.
 */
function asRecord(value: unknown): ApiRecord | null {
  return value && typeof value === 'object' ? (value as ApiRecord) : null;
}

/**
 * Normaliza o status exibido em candidaturas.
 */
function statusLabel(value: unknown) {
  return displayValue(value || 'candidatado');
}

function summarizeText(value: unknown, maxLength = 180) {
  const text = displayValue(value);
  if (text === 'Nao informado' || text.length <= maxLength) return text;
  return `${text.slice(0, maxLength).trimEnd()}...`;
}

/**
 * Extrai a vaga aninhada no retorno de candidatura.
 */
function jobFromApplication(application: ApiRecord) {
  return asRecord(application.id_vaga);
}

/**
 * Exibe e atualiza dados editaveis do candidato autenticado.
 */
export function CandidateProfilePage() {
  const { user } = useAuth();
  const cpf = user?.candidato_cpf;
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [resumeError, setResumeError] = useState('');
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ['candidate-profile', cpf],
    queryFn: async () => {
      const response = await api.get<ApiRecord>(`/candidato/candidatos/${cpf}/`);
      return response.data;
    },
    enabled: Boolean(cpf),
  });

  const update = useMutation({
    mutationFn: async (payload: ApiRecord) => api.patch(`/candidato/candidatos/${cpf}/`, payload),
    onSuccess: () => {
      setError('');
      void queryClient.invalidateQueries({ queryKey: ['candidate-profile', cpf] });
    },
    onError: (mutationError) => setError(extractApiError(mutationError)),
  });

  const updateResume = useMutation({
    mutationFn: () => {
      if (!resumeFile) {
        return Promise.reject(new Error('Selecione um arquivo PDF, DOC ou DOCX.'));
      }
      const formData = new FormData();
      formData.append('curriculo', resumeFile);
      return api.patch(`/candidato/candidatos/${cpf}/curriculo/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    onSuccess: () => {
      setResumeError('');
      setResumeFile(null);
      void queryClient.invalidateQueries({ queryKey: ['candidate-profile', cpf] });
    },
    onError: (mutationError) => setResumeError(extractApiError(mutationError)),
  });

  if (!cpf) return <PageState title="Usuario sem vinculo de candidato" variant="error" />;
  if (query.isLoading) return <PageState title="Carregando perfil" />;
  if (query.isError || !query.data) return <PageState title="Nao foi possivel carregar o perfil" variant="error" />;

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    update.mutate({
      nome: formData.get('nome'),
      email: formData.get('email'),
      telefone: formData.get('telefone'),
    });
  }

  function handleResumeFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    setResumeError('');

    if (!file) {
      setResumeFile(null);
      return;
    }

    const validationError = validateResumeFile(file);
    if (validationError) {
      setResumeFile(null);
      setResumeError(validationError);
      event.target.value = '';
      return;
    }

    setResumeFile(file);
  }

  function removeResumeFile() {
    setResumeFile(null);
  }

  const currentResume = query.data?.curriculo ? String(query.data.curriculo) : '';
  const currentResumeName = currentResume ? resumeDisplayName(currentResume) : '';

  return (
    <section>
      <PageHeader title="Perfil do candidato" description="Dados pessoais e curriculo do seu cadastro." />
      {error ? (
        <pre className="mb-4 whitespace-pre-wrap rounded-md border border-danger/30 bg-red-50 p-3 font-sans text-sm text-danger dark:bg-red-950/30">
          {error}
        </pre>
      ) : null}
      <form
        onSubmit={submit}
        className="grid gap-4 rounded-md border border-line bg-white p-4 md:grid-cols-4 dark:border-slate-700 dark:bg-slate-950"
      >
        <label>
          <span className="mb-1 block text-sm font-medium text-ink dark:text-slate-100">CPF</span>
          <input
            className="w-full rounded-md border border-line bg-panel p-2 text-sm text-ink dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            value={String(query.data?.cpf_candidato ?? '')}
            readOnly
          />
        </label>
        {(['nome', 'email', 'telefone'] as const).map((field) => (
          <label key={field}>
            <span className="mb-1 block text-sm font-medium text-ink dark:text-slate-100">
              {field === 'nome' ? 'Nome' : field === 'email' ? 'E-mail' : 'Telefone'}
            </span>
            <input
              className="focus-ring w-full rounded-md border border-line bg-white p-2 text-sm text-ink dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              name={field}
              defaultValue={String(query.data?.[field] ?? '')}
            />
          </label>
        ))}
        <div className="md:col-span-4">
          <Button type="submit" disabled={update.isPending}>
            Salvar perfil
          </Button>
        </div>
      </form>

      {resumeError ? (
        <pre className="mt-4 whitespace-pre-wrap rounded-md border border-danger/30 bg-red-50 p-3 font-sans text-sm text-danger dark:bg-red-950/30">
          {resumeError}
        </pre>
      ) : null}
      <div className="mt-4 rounded-md border border-line bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
        <h2 className="text-base font-semibold text-ink dark:text-slate-100">Curriculo</h2>
        <p className="mt-1 text-sm text-muted dark:text-slate-400">Arquivo usado nos processos seletivos.</p>
        <div className="mt-4 rounded-md border border-line bg-panel p-4 dark:border-slate-700 dark:bg-slate-900">
          <p className="text-xs font-semibold uppercase text-muted dark:text-slate-400">Curriculo atual</p>
          <p className="mt-1 text-sm text-ink dark:text-slate-100">
            {currentResumeName || 'Nenhum curriculo cadastrado.'}
          </p>
        </div>
        <div className="mt-4 rounded-md border border-line bg-panel p-4 dark:border-slate-700 dark:bg-slate-900">
          <label className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <span className="flex items-center gap-2 text-sm font-medium text-ink dark:text-slate-100">
              <FileUp className="h-4 w-4 text-brand" />
              Enviar novo curriculo PDF ou Word
            </span>
            <input
              type="file"
              accept={RESUME_ACCEPT}
              onChange={handleResumeFile}
              className="max-w-full text-sm"
            />
          </label>
          {resumeFile ? (
            <span className="mt-3 inline-flex items-center gap-2 rounded-md border border-line bg-white px-3 py-2 text-xs font-medium text-ink dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100">
              {resumeFile.name} ({formatFileSize(resumeFile.size)})
              <button
                type="button"
                onClick={removeResumeFile}
                className="rounded-sm text-muted hover:text-danger dark:text-slate-400"
                aria-label={`Remover ${resumeFile.name}`}
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </span>
          ) : null}
        </div>
        <div className="mt-4">
          <Button onClick={() => updateResume.mutate()} disabled={updateResume.isPending || !resumeFile}>
            Salvar curriculo
          </Button>
        </div>
      </div>
    </section>
  );
}

/**
 * Lista vagas disponiveis e cria candidaturas para o candidato autenticado.
 */
export function CandidateJobsPage() {
  const { user } = useAuth();
  const cpf = user?.candidato_cpf;
  const [error, setError] = useState('');
  const queryClient = useQueryClient();
  const jobs = useQuery({
    queryKey: ['candidate-jobs', cpf],
    queryFn: () => listResource<ApiRecord>(`/candidato/candidatos/${cpf}/vagas-disponiveis/`, {}),
    enabled: Boolean(cpf),
  });
  const apply = useMutation({
    mutationFn: (id_vaga: unknown) => api.post(`/candidato/candidatos/${cpf}/candidatar-se/`, { id_vaga }),
    onSuccess: () => {
      setError('');
      void queryClient.invalidateQueries({ queryKey: ['candidate-jobs', cpf] });
    },
    onError: (mutationError) => setError(extractApiError(mutationError)),
  });

  if (!cpf) return <PageState title="Usuario sem vinculo de candidato" variant="error" />;
  if (jobs.isLoading) return <PageState title="Carregando vagas" />;

  return (
    <section>
      <PageHeader title="Vagas disponiveis" description="Vagas em que voce ainda nao se candidatou." />
      {error ? (
        <pre className="mb-4 whitespace-pre-wrap rounded-md border border-danger/30 bg-red-50 p-3 font-sans text-sm text-danger dark:bg-red-950/30">
          {error}
        </pre>
      ) : null}
      <div className="grid gap-4 md:grid-cols-2">
        {jobs.data?.results.map((job) => (
          <article
            key={String(job.id_vaga)}
            className="rounded-md border border-line bg-white p-4 shadow-soft dark:border-slate-700 dark:bg-slate-950"
          >
            <h2 className="font-semibold text-ink dark:text-slate-100">{String(job.titulo ?? 'Vaga')}</h2>
            <div className="mt-3 flex flex-wrap gap-2 text-xs font-semibold uppercase">
              <span className="rounded-md bg-success/15 px-2 py-1 text-success dark:bg-success/20">
                {displayValue(job.status)}
              </span>
            </div>
            <dl className="mt-4 grid gap-3 text-sm">
              <div>
                <dt className="text-xs font-semibold uppercase text-muted dark:text-slate-400">Descricao</dt>
                <dd className="mt-1 text-ink dark:text-slate-100">{summarizeText(job.descricao)}</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase text-muted dark:text-slate-400">Requisitos da triagem</dt>
                <dd className="mt-1 text-ink dark:text-slate-100">{summarizeText(job.requisitos)}</dd>
              </div>
            </dl>
            <div className="mt-5">
              <Button onClick={() => apply.mutate(job.id_vaga)} disabled={apply.isPending}>
                Candidatar-se
              </Button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

/**
 * Exibe candidaturas e status retornados pela API.
 */
export function CandidateApplicationsPage() {
  const { user } = useAuth();
  const cpf = user?.candidato_cpf;
  const query = useQuery({
    queryKey: ['candidate-applications', cpf],
    queryFn: () => listResource<ApiRecord>(`/candidato/candidatos/${cpf}/vagas-candidatadas/`, {}),
    enabled: Boolean(cpf),
  });

  if (!cpf) return <PageState title="Usuario sem vinculo de candidato" variant="error" />;
  if (query.isLoading) return <PageState title="Carregando candidaturas" />;

  const applications = query.data?.results ?? [];

  return (
    <section>
      <PageHeader title="Minhas candidaturas" description="Acompanhe o status dos seus processos." />
      {applications.length === 0 ? (
        <PageState title="Nenhuma candidatura encontrada" variant="empty" />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {applications.map((application, index) => {
            const job = jobFromApplication(application);
            const sector = asRecord(job?.fk_id_setor);
            const title = displayValue(job?.titulo || `Vaga ${displayValue(application.id_vaga)}`);
            const description = displayValue(job?.descricao || 'Sem descricao cadastrada.');
            const publicationDate = displayValue(job?.data_publicacao);

            return (
              <article
                key={`${String(application.id_vaga)}-${index}`}
                className="rounded-md border border-line bg-white p-4 shadow-soft dark:border-slate-700 dark:bg-slate-950"
              >
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h2 className="text-base font-semibold text-ink dark:text-slate-100">{title}</h2>
                    <p className="mt-1 text-sm text-muted dark:text-slate-400">{description}</p>
                  </div>
                  <span className="inline-flex w-fit rounded-md bg-success/15 px-2 py-1 text-xs font-semibold uppercase text-success dark:bg-success/20">
                    {statusLabel(application.status_processo)}
                  </span>
                </div>
                <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
                  <div>
                    <dt className="text-xs font-semibold uppercase text-muted dark:text-slate-400">Setor</dt>
                    <dd className="mt-1 text-ink dark:text-slate-100">{displayValue(sector?.nome || job?.fk_id_setor)}</dd>
                  </div>
                  <div>
                    <dt className="text-xs font-semibold uppercase text-muted dark:text-slate-400">Publicacao</dt>
                    <dd className="mt-1 text-ink dark:text-slate-100">{publicationDate}</dd>
                  </div>
                </dl>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
