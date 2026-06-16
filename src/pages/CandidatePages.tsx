import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { FileUp, X } from 'lucide-react';
import { useState, type ChangeEvent, type FormEvent } from 'react';
import { useAuth } from '../auth/AuthContext';
import { api, extractApiError, listResource } from '../services/api';
import type { ApiRecord } from '../types';
import { PageState } from '../components/PageState';
import { Button, PageHeader, SensitiveValue } from '../components/ui';
import { displayValue } from '../utils/formatters';

const MAX_FILE_SIZE = 2 * 1024 * 1024;
const ATTACHMENTS_START = '[ANEXOS_CURRICULO_JSON]';
const ATTACHMENTS_END = '[/ANEXOS_CURRICULO_JSON]';

type ResumeAttachment = {
  name: string;
  type: string;
  size: number;
  dataUrl: string;
};

/**
 * Separa texto do curriculo e anexos serializados no campo legado.
 */
function parseCurriculoPayload(value: unknown) {
  const raw = String(value ?? '');
  const start = raw.indexOf(ATTACHMENTS_START);
  const end = raw.indexOf(ATTACHMENTS_END);

  if (start === -1 || end === -1 || end <= start) {
    return { text: raw, attachments: [] as ResumeAttachment[] };
  }

  const text = raw.slice(0, start).trim();
  const json = raw.slice(start + ATTACHMENTS_START.length, end).trim();

  try {
    const parsed = JSON.parse(json);
    const attachments = Array.isArray(parsed)
      ? parsed.filter((file): file is ResumeAttachment => (
          file
          && typeof file.name === 'string'
          && typeof file.type === 'string'
          && typeof file.size === 'number'
          && typeof file.dataUrl === 'string'
        ))
      : [];
    return { text, attachments };
  } catch {
    return { text: raw, attachments: [] as ResumeAttachment[] };
  }
}

/**
 * Melhora a leitura do texto colado no curriculo sem alterar seu conteudo.
 */
function formatCurriculoText(value: string) {
  return value
    .replace(/\s+/g, ' ')
    .replace(/\s+(DADOS PESSOAIS|FORMAÇÃO ACADÊMICA|FORMACAO ACADEMICA|EXPERIÊNCIA PROFISSIONAL|EXPERIENCIA PROFISSIONAL|CURSOS COMPLEMENTARES|COMPETÊNCIAS|COMPETENCIAS|PRETENSÃO SALARIAL|PRETENSAO SALARIAL|DISPONIBILIDADE)\b/g, '\n\n$1')
    .replace(/\s+(Nome|CPF|RG|Data de Nascimento|Estado Civil|Telefone|E-mail|Endereço|Endereco|Rua|Bairro|Cidade|Estado|CEP|Objetivo|Empresa|Cargo|Período|Periodo|Principais Atividades):/g, '\n$1:')
    .replace(/\s+-\s+/g, '\n- ')
    .trim();
}

/**
 * Converte tamanho em bytes para exibicao compacta.
 */
function formatFileSize(size: number) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * Identifica anexos que podem ser renderizados como imagem.
 */
function isImageAttachment(file: ResumeAttachment) {
  return file.type.startsWith('image/');
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
  const [error, setError] = useState('');
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

  if (!cpf) return <PageState title="Usuário sem vínculo de candidato" variant="error" />;
  if (query.isLoading) return <PageState title="Carregando perfil" />;
  if (query.isError || !query.data) return <PageState title="Não foi possível carregar o perfil" variant="error" />;

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    update.mutate({
      nome: formData.get('nome'),
      email: formData.get('email'),
      telefone: formData.get('telefone'),
    });
  }

  return (
    <section>
      <PageHeader title="Perfil do candidato" description="Dados pessoais do seu cadastro." />
      {error ? (
        <pre className="mb-4 whitespace-pre-wrap rounded-md border border-danger/30 bg-red-50 p-3 font-sans text-sm text-danger dark:bg-red-950/30">
          {error}
        </pre>
      ) : null}
      <form
        onSubmit={submit}
        className="grid gap-4 rounded-md border border-line bg-white p-4 md:grid-cols-3 dark:border-slate-700 dark:bg-slate-950"
      >
        {(['nome', 'email', 'telefone'] as const).map((field) => (
          <label key={field}>
            <span className="mb-1 block text-sm font-medium capitalize text-ink dark:text-slate-100">{field}</span>
            <input
              className="focus-ring w-full rounded-md border border-line bg-white p-2 text-sm text-ink dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              name={field}
              defaultValue={String(query.data?.[field] ?? '')}
            />
          </label>
        ))}
        <div className="md:col-span-3">
          <Button type="submit" disabled={update.isPending}>
            Salvar perfil
          </Button>
        </div>
      </form>
      <div className="mt-4 rounded-md border border-line bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
        <p className="text-xs font-semibold uppercase text-muted dark:text-slate-400">CPF</p>
        <p className="mt-1 text-sm">
          <SensitiveValue value={query.data.cpf_candidato} />
        </p>
      </div>
    </section>
  );
}

/**
 * Atualiza o curriculo do candidato respeitando validacoes do backend.
 */
export function CandidateResumePage() {
  const { user } = useAuth();
  const cpf = user?.candidato_cpf;
  const [curriculo, setCurriculo] = useState('');
  const [attachments, setAttachments] = useState<ResumeAttachment[]>([]);
  const [error, setError] = useState('');
  const queryClient = useQueryClient();
  const profile = useQuery({
    queryKey: ['candidate-resume', cpf],
    queryFn: async () => {
      const response = await api.get<ApiRecord>(`/candidato/candidatos/${cpf}/`);
      const parsed = parseCurriculoPayload(response.data.curriculo);
      setCurriculo(formatCurriculoText(parsed.text));
      setAttachments(parsed.attachments);
      return response.data;
    },
    enabled: Boolean(cpf),
  });
  const update = useMutation({
    mutationFn: () => api.patch(`/candidato/candidatos/${cpf}/curriculo/`, { curriculo: buildCurriculoPayload() }),
    onSuccess: () => {
      setError('');
      void queryClient.invalidateQueries({ queryKey: ['candidate-resume', cpf] });
    },
    onError: (mutationError) => setError(extractApiError(mutationError)),
  });

  /**
   * Remove anexo da lista que sera salva no curriculo.
   */
  function removeAttachment(name: string) {
    setAttachments((current) => current.filter((file) => file.name !== name));
  }

  /**
   * Le arquivos locais e os converte para data URL antes de salvar.
   */
  async function handleFiles(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files || []);
    setError('');

    const converted = await Promise.all(
      files.map(
        (file) =>
          new Promise<ResumeAttachment>((resolve, reject) => {
            if (file.size > MAX_FILE_SIZE) {
              reject(new Error(`O arquivo ${file.name} excede 2 MB.`));
              return;
            }

            const reader = new FileReader();
            reader.onload = () =>
              resolve({
                name: file.name,
                type: file.type || 'application/octet-stream',
                size: file.size,
                dataUrl: String(reader.result),
              });
            reader.onerror = () => reject(new Error(`Não foi possível ler ${file.name}.`));
            reader.readAsDataURL(file);
          }),
      ),
    ).catch((fileError: Error) => {
      setError(fileError.message);
      return [];
    });

    setAttachments((current) => {
      const names = new Set(current.map((file) => file.name));
      return [...current, ...converted.filter((file) => !names.has(file.name))];
    });
    event.target.value = '';
  }

  /**
   * Recria o payload persistido, preservando texto e anexos no mesmo campo.
   */
  function buildCurriculoPayload() {
    if (attachments.length === 0) return curriculo;

    return [
      curriculo,
      '',
      ATTACHMENTS_START,
      JSON.stringify(attachments),
      ATTACHMENTS_END,
    ]
      .filter(Boolean)
      .join('\n');
  }

  if (!cpf) return <PageState title="Usuário sem vínculo de candidato" variant="error" />;
  if (profile.isLoading) return <PageState title="Carregando currículo" />;

  return (
    <section>
      <PageHeader title="Currículo" description="Atualize seu currículo para os processos seletivos." />
      {error ? (
        <pre className="mb-4 whitespace-pre-wrap rounded-md border border-danger/30 bg-red-50 p-3 font-sans text-sm text-danger dark:bg-red-950/30">
          {error}
        </pre>
      ) : null}
      <div className="rounded-md border border-line bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
        <textarea
          className="focus-ring mb-3 min-h-72 w-full rounded-md border border-line bg-white p-3 text-sm text-ink dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
          value={curriculo}
          onChange={(event) => setCurriculo(event.target.value)}
        />
        <div className="mb-4 rounded-md border border-line bg-panel p-4 dark:border-slate-700 dark:bg-slate-900">
          <label className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <span className="flex items-center gap-2 text-sm font-medium text-ink dark:text-slate-100">
              <FileUp className="h-4 w-4 text-brand" />
              Anexar arquivos ou imagens
            </span>
            <input
              type="file"
              multiple
              accept="image/*,.pdf,.doc,.docx,.txt"
              onChange={handleFiles}
              className="max-w-full text-sm"
            />
          </label>
          {attachments.length ? (
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {attachments.map((file) => (
                <article
                  key={file.name}
                  className="overflow-hidden rounded-md border border-line bg-white dark:border-slate-700 dark:bg-slate-950"
                >
                  {isImageAttachment(file) ? (
                    <img
                      src={file.dataUrl}
                      alt={file.name}
                      className="h-44 w-full bg-slate-100 object-contain dark:bg-slate-900"
                    />
                  ) : (
                    <div className="flex h-28 items-center justify-center bg-panel px-4 text-center text-sm font-medium text-ink dark:bg-slate-900 dark:text-slate-100">
                      {file.name}
                    </div>
                  )}
                  <div className="flex items-center justify-between gap-3 p-3">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold text-ink dark:text-slate-100">{file.name}</p>
                      <p className="text-xs text-muted dark:text-slate-400">{formatFileSize(file.size)}</p>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      <a
                        href={file.dataUrl}
                        download={file.name}
                        className="rounded-md border border-line px-2 py-1 text-xs font-semibold text-brand hover:bg-panel dark:border-slate-700 dark:hover:bg-slate-900"
                      >
                        Baixar
                      </a>
                      <button
                        type="button"
                        onClick={() => removeAttachment(file.name)}
                        className="rounded-md border border-line p-1.5 text-muted hover:bg-red-50 hover:text-danger dark:border-slate-700 dark:text-slate-400 dark:hover:bg-red-950/30"
                        aria-label={`Remover ${file.name}`}
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          ) : null}
        </div>
        <Button onClick={() => update.mutate()} disabled={update.isPending}>
          Salvar currículo
        </Button>
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

  if (!cpf) return <PageState title="Usuário sem vínculo de candidato" variant="error" />;
  if (jobs.isLoading) return <PageState title="Carregando vagas" />;

  return (
    <section>
      <PageHeader title="Vagas disponíveis" description="Vagas em que você ainda não se candidatou." />
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
            <p className="mt-2 text-sm text-muted dark:text-slate-400">
              {String(job.descricao ?? 'Sem descrição')}
            </p>
            <div className="mt-4">
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

  if (!cpf) return <PageState title="Usuário sem vínculo de candidato" variant="error" />;
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
            const description = displayValue(job?.descricao || 'Sem descrição cadastrada.');
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
                    <dt className="text-xs font-semibold uppercase text-muted dark:text-slate-400">Publicação</dt>
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
